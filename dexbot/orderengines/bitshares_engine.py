import copy
import datetime
import logging
import time

import bitshares.exceptions
import bitsharesapi
import bitsharesapi.exceptions
from bitshares.account import Account
from bitshares.amount import Amount, Asset
from bitshares.dex import Dex
from bitshares.instance import shared_bitshares_instance
from bitshares.market import Market
from bitshares.price import FilledOrder, Order, UpdateCallOrder
from bitshares.utils import formatTime
from events import Events

from dexbot.config import Config
from dexbot.helper import truncate
from dexbot.storage import Storage

# Number of maximum retries used to retry action before failing
MAX_TRIES = 3


class BitsharesOrderEngine(Storage, Events):
    """
    All prices are passed and returned as BASE/QUOTE. (In the BREAD:USD market that would be USD/BREAD, 2.5 USD / 1
    BREAD).

     - Buy orders reserve BASE
     - Sell orders reserve QUOTE

    OrderEngine inherits:
        * :class:`dexbot.storage.Storage` : Stores data to sqlite database
        * ``Events`` :The websocket endpoint of BitShares has notifications that are subscribed to
                        and dispatched by dexbot. This uses python's native Events
    """

    def __init__(
        self,
        name,
        config=None,
        _account=None,
        _market=None,
        fee_asset_symbol=None,
        bitshares_instance=None,
        *args,
        **kwargs
    ):

        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()

        # Dex instance used to get different fees for the market
        self.dex = Dex(self.bitshares)

        # Storage
        Storage.__init__(self, name)

        # Events
        Events.__init__(self)

        # Redirect this event to also call order placed and order matched
        self.onMarketUpdate += self._callbackPlaceFillOrders

        if config:
            self.config = config
        else:
            self.config = Config.get_worker_config_file(name)

        # Get worker's parameters from the config
        self.worker = config["workers"][name]
        self._market = _market or Market(self.worker["market"], bitshares_instance=self.bitshares)
        self._account = _account or Account(self.worker["account"], full=True, bitshares_instance=self.bitshares)

        # Recheck flag - Tell the strategy to check for updated orders
        self.recheck_orders = False

        # Count of orders to be fetched from the API
        self.fetch_depth = 8

        # Set fee asset
        fee_asset_symbol = fee_asset_symbol or self.worker.get('fee_asset')

        if fee_asset_symbol:
            try:
                self.fee_asset = Asset(fee_asset_symbol, bitshares_instance=self.bitshares)
            except bitshares.exceptions.AssetDoesNotExistsException:
                self.fee_asset = Asset('1.3.0', bitshares_instance=self.bitshares)
        else:
            # If there is no fee asset, use BTS
            self.fee_asset = Asset('1.3.0', bitshares_instance=self.bitshares)

        # CER cache
        self.core_exchange_rate = None

        # Ticker
        self.ticker = self._market.ticker

        # Settings for bitshares instance
        self.bitshares.bundle = bool(self.worker.get("bundle", False))

        # Disabled flag - this flag can be flipped to True by a worker and will be reset to False after reset only
        self.disabled = False

        # Order expiration time in seconds
        self.expiration = 60 * 60 * 24 * 365 * 5

        # buy/sell actions will return order id by default
        self.returnOrderId = 'head'

        self.log = logging.LoggerAdapter(logging.getLogger('dexbot.orderengine'), {})

    def _callbackPlaceFillOrders(self, d):
        """This method distinguishes notifications caused by Matched orders from those caused by placed orders."""
        if isinstance(d, FilledOrder):
            self.onOrderMatched(d)
        elif isinstance(d, Order):
            self.onOrderPlaced(d)
        elif isinstance(d, UpdateCallOrder):
            self.onUpdateCallOrder(d)
        else:
            pass

    def _cancel_orders(self, orders):
        try:
            self.retry_action(self.bitshares.cancel, orders, account=self._account, fee_asset=self.fee_asset['id'])
        except bitsharesapi.exceptions.UnhandledRPCError as exception:
            str_exception = str(exception)
            if ('Order does not exist' in str_exception) or ('Unable to find Object' in str_exception):
                # The order(s) we tried to cancel doesn't exist
                self.bitshares.txbuffer.clear()
                return False
            else:
                self.log.exception("Unable to cancel order")
                return False
        except bitshares.exceptions.MissingKeyError:
            self.log.exception('Unable to cancel order(s), private key missing.')
            return False

        return True

    def account_total_value(self, return_asset):
        """
        Returns the total value of the account in given asset.

        :param string | return_asset: Balance is returned as this asset
        :return: float: Value of the account in one asset
        """
        total_value = 0

        # Total balance calculation
        for balance in self.balances:
            if balance['symbol'] != return_asset:
                # Convert to asset if different
                total_value += self.convert_asset(balance['amount'], balance['symbol'], return_asset)
            else:
                total_value += balance['amount']

        # Orders balance calculation
        for order in self.all_own_orders:
            updated_order = self.get_updated_order(order['id'])

            if not order:
                continue
            if updated_order['base']['symbol'] == return_asset:
                total_value += updated_order['base']['amount']
            else:
                total_value += self.convert_asset(
                    updated_order['base']['amount'], updated_order['base']['symbol'], return_asset
                )

        return total_value

    def balance(self, asset, fee_reservation=0):
        """
        Return the balance of your worker's account in a specific asset.

        :param string | asset: In what asset the balance is wanted to be returned
        :param float | fee_reservation: How much is saved in reserve for the fees
        :return: Balance of specific asset
        """
        balance = self._account.balance(asset)

        if fee_reservation > 0:
            balance['amount'] = balance['amount'] - fee_reservation

        return balance

    def calculate_order_data(self, order_type, order, amount, price):
        """Reconstructs order data using price and amount."""
        quote_asset = Amount(amount, self._market['quote']['symbol'], bitshares_instance=self.bitshares)
        base_asset = Amount(amount * price, self._market['base']['symbol'], bitshares_instance=self.bitshares)
        if order_type == 'buy':
            order['quote'] = quote_asset
            order['price'] = price
            order['base'] = base_asset
        elif order_type == 'sell':
            order['quote'] = base_asset
            order['price'] = price ** -1
            order['base'] = quote_asset
        else:
            raise ValueError('Invalid order_type')

        return order

    def calculate_worker_value(self, unit_of_measure):
        """
        Returns the combined value of allocated and available BASE and QUOTE. Total value is measured in
        "unit_of_measure", which is either BASE or QUOTE symbol.

        :param string | unit_of_measure: Asset symbol
        :return: Value of the worker as float
        """
        base_total = 0
        quote_total = 0

        # Calculate total balances
        balances = self.balances
        for balance in balances:
            if balance['symbol'] == self.base_asset:
                base_total += balance['amount']
            elif balance['symbol'] == self.quote_asset:
                quote_total += balance['amount']

        # Calculate value of the orders in unit of measure
        orders = self.own_orders
        for order in orders:
            if order['base']['symbol'] == self.quote_asset:
                # Pick sell orders order's BASE amount, which is same as worker's QUOTE, to worker's BASE
                quote_total += order['base']['amount']
            else:
                base_total += order['base']['amount']

        # Finally convert asset to another and return the sum
        if unit_of_measure == self.base_asset:
            quote_total = self.convert_asset(quote_total, self.quote_asset, unit_of_measure)
        elif unit_of_measure == self.quote_asset:
            base_total = self.convert_asset(base_total, self.base_asset, unit_of_measure)

        # Fixme: Make sure that decimal precision is correct.
        return base_total + quote_total

    def cancel_all_orders(self, all_markets=False):
        """
        Cancel all orders of the worker's market or all markets.

        :param bool all_markets: True = cancel orders on all markets, False = cancel only own market
        """
        orders_to_cancel = []

        if all_markets:
            self.log.info('Canceling all account orders')
            orders_to_cancel = self.all_own_orders
        else:
            self.log.info(
                'Canceling all orders on market {}/{}'.format(
                    self.market['quote']['symbol'], self.market['base']['symbol']
                )
            )
            orders_to_cancel = self.own_orders

        if orders_to_cancel:
            self.cancel_orders(orders_to_cancel)

        self.log.info("Orders canceled")

    def cancel_orders(self, orders, batch_only=False):
        """
        Cancel specific order(s)

        :param list | orders: List of orders to cancel
        :param bool | batch_only: Try cancel orders only in batch mode without one-by-one fallback
        :return:
        """
        if not isinstance(orders, (list, set, tuple)):
            orders = [orders]

        orders = [order['id'] for order in orders if 'id' in order]

        success = self._cancel_orders(orders)
        if not success and batch_only:
            return False
        if not success and len(orders) > 1 and not batch_only:
            # One of the order cancels failed, cancel the orders one by one
            for order in orders:
                success = self._cancel_orders(order)
                if not success:
                    return False
        return success

    def count_asset(self, order_ids=None, return_asset=False):
        """
        Returns the combined amount of the given order ids and the account balance The amounts are returned in quote and
        base assets of the market.

        :param list | order_ids: list of order ids to be added to the balance
        :param bool | return_asset: true if returned values should be Amount instances
        :return: dict with keys quote and base

        Todo: When would we want the sum of a subset of orders? Why order_ids? Maybe just specify asset?
        """
        quote = 0
        base = 0
        quote_asset = self._market['quote']['id']
        base_asset = self._market['base']['id']

        # Total balance calculation
        for balance in self.balances:
            if balance.asset['id'] == quote_asset:
                quote += balance['amount']
            elif balance.asset['id'] == base_asset:
                base += balance['amount']

        if order_ids is None:
            # Get all orders from Blockchain
            order_ids = [order['id'] for order in self.own_orders]
        if order_ids:
            orders_balance = self.get_allocated_assets(order_ids)
            quote += orders_balance['quote']
            base += orders_balance['base']

        if return_asset:
            quote = Amount(quote, quote_asset, bitshares_instance=self.bitshares)
            base = Amount(base, base_asset, bitshares_instance=self.bitshares)

        return {'quote': quote, 'base': base}

    def get_allocated_assets(self, order_ids=None, return_asset=False):
        """
        Returns the amount of QUOTE and BASE allocated in orders, and that do not show up in available balance.

        :param list | order_ids:
        :param bool | return_asset:
        :return: Dictionary of QUOTE and BASE amounts
        """
        if not order_ids:
            order_ids = []
        elif isinstance(order_ids, str):
            order_ids = [order_ids]

        quote = 0
        base = 0
        quote_asset = self._market['quote']['id']
        base_asset = self._market['base']['id']

        for order_id in order_ids:
            order = self.get_updated_order(order_id)
            if not order:
                continue
            asset_id = order['base']['asset']['id']
            if asset_id == quote_asset:
                quote += order['base']['amount']
            elif asset_id == base_asset:
                base += order['base']['amount']

        # Return as Amount objects instead of only float values
        if return_asset:
            quote = Amount(quote, quote_asset, bitshares_instance=self.bitshares)
            base = Amount(base, base_asset, bitshares_instance=self.bitshares)

        return {'quote': quote, 'base': base}

    def get_highest_own_buy_order(self, orders=None):
        """
        Returns highest own buy order.

        :param list | orders:
        :return: Highest own buy order by price at the market or None
        """
        if not orders:
            orders = self.get_own_buy_orders()

        try:
            return orders[0]
        except IndexError:
            return None

    def get_lowest_own_sell_order(self, orders=None):
        """
        Returns lowest own sell order.

        :param list | orders:
        :return: Lowest own sell order by price at the market
        """
        if not orders:
            orders = self.get_own_sell_orders()

        try:
            return orders[0]
        except IndexError:
            return None

    def get_market_orders(self, depth=1, updated=True):
        """
        Returns orders from the current market. Orders are sorted by price.

        get_limit_orders() call does not have any depth limit.

        :param int | depth: Amount of orders per side will be fetched, default=1
        :param bool | updated: Return updated orders. "Updated" means partially filled orders will represent
                               remainders and not just initial amounts
        :return: Returns a list of orders or None
        """
        orders = self.bitshares.rpc.get_limit_orders(self._market['base']['id'], self._market['quote']['id'], depth)
        if updated:
            orders = [self.get_updated_limit_order(o) for o in orders]
        orders = [Order(o, bitshares_instance=self.bitshares) for o in orders]
        return orders

    def get_order_cancellation_fee(self, fee_asset):
        """
        Returns the order cancellation fee in the specified asset.

        :param string | fee_asset: Asset in which the fee is wanted
        :return: Cancellation fee as fee asset
        """
        # Get fee
        fees = self.dex.returnFees()
        limit_order_cancel = fees['limit_order_cancel']
        return self.convert_fee(limit_order_cancel['fee'], fee_asset)

    def get_order_creation_fee(self, fee_asset):
        """
        Returns the cost of creating an order in the asset specified.

        :param fee_asset: QUOTE, BASE, BTS, or any other
        :return:
        """
        # Get fee
        fees = self.dex.returnFees()
        limit_order_create = fees['limit_order_create']
        return self.convert_fee(limit_order_create['fee'], fee_asset)

    def get_own_buy_orders(self, orders=None):
        """
        Get own buy orders from current market, or from a set of orders passed for this function.

        :return: List of buy orders
        """
        if not orders:
            # List of orders was not given so fetch everything from the market
            orders = self.own_orders

        return self.filter_buy_orders(orders)

    def get_own_sell_orders(self, orders=None):
        """
        Get own sell orders from current market.

        :return: List of sell orders
        """
        if not orders:
            # List of orders was not given so fetch everything from the market
            orders = self.own_orders

        return self.filter_sell_orders(orders)

    def get_own_spread(self):
        """
        Returns the difference between own closest opposite orders.

        :return: float or None: Own spread
        """
        try:
            # Try fetching own orders
            highest_own_buy_price = self.get_highest_own_buy_order().get('price')
            lowest_own_sell_price = self.get_lowest_own_sell_order().get('price')
        except AttributeError:
            return None

        # Calculate actual spread
        actual_spread = lowest_own_sell_price / highest_own_buy_price - 1
        return actual_spread

    def get_updated_order(self, order_id):
        """
        Tries to get the updated order from the API. Returns None if the order doesn't exist.

        :param str|dict order_id: blockchain Order object or id of the order
        """
        if isinstance(order_id, dict):
            order_id = order_id['id']

        # At first, try to look up own orders. This prevents RPC calls whether requested order is own order
        order = None
        for limit_order in self._account['limit_orders']:
            if order_id == limit_order['id']:
                order = limit_order
                break
        else:
            # We are using direct rpc call here because passing an Order object to self.get_updated_limit_order() give
            # us weird error "Object of type 'BitShares' is not JSON serializable"
            order = self.bitshares.rpc.get_objects([order_id])[0]

        # Do not try to continue whether there is no order in the blockchain
        if not order:
            return None

        updated_order = self.get_updated_limit_order(order)
        return Order(updated_order, bitshares_instance=self.bitshares)

    def execute(self):
        """
        Execute a bundle of operations.

        :return: dict: transaction
        """
        self.bitshares.blocking = "head"
        r = self.bitshares.txbuffer.broadcast()
        self.bitshares.blocking = False
        return r

    def is_buy_order(self, order):
        """
        Check whether an order is buy order.

        :param dict | order: dict or Order object
        :return bool
        """
        # Check if the order is buy order, by comparing asset symbol of the order and the market
        if order['base']['symbol'] == self._market['base']['symbol']:
            return True
        else:
            return False

    def is_current_market(self, base_asset_id, quote_asset_id):
        """
        Returns True if given asset id's are of the current market.

        :return: bool: True = Current market, False = Not current market
        """
        if quote_asset_id == self._market['quote']['id']:
            if base_asset_id == self._market['base']['id']:
                return True
            return False

        # Todo: Should we return true if market is opposite?
        if quote_asset_id == self._market['base']['id']:
            if base_asset_id == self._market['quote']['id']:
                return True
            return False

        return False

    def is_sell_order(self, order):
        """
        Check whether an order is sell order.

        :param dict | order: dict or Order object
        :return bool
        """
        # Check if the order is sell order, by comparing asset symbol of the order and the market
        if order['base']['symbol'] == self._market['quote']['symbol']:
            return True
        else:
            return False

    def place_market_buy_order(self, amount, price, return_none=False, *args, **kwargs):
        """
        Places a buy order in the market.

        :param float | amount: Order amount in QUOTE
        :param float | price: Order price in BASE
        :param bool | return_none:
        :param args:
        :param kwargs:
        :return:
        """
        symbol = self._market['base']['symbol']
        precision = self._market['base']['precision']
        base_amount = truncate(price * amount, precision)
        return_order_id = kwargs.pop('returnOrderId', self.returnOrderId)

        # Don't try to place an order of size 0
        if not base_amount:
            self.log.critical('Trying to buy 0')
            self.disabled = True
            return None

        # Make sure we have enough balance for the order
        if return_order_id and self.balance(self._market['base']) < base_amount:
            self.log.critical("Insufficient buy balance, needed {} {}".format(base_amount, symbol))
            self.disabled = True
            return None

        self.log.info(
            'Placing a buy order with {:.{prec}f} {} @ {:.8f}'.format(base_amount, symbol, price, prec=precision)
        )

        # Place the order
        buy_transaction = self.retry_action(
            self._market.buy,
            price,
            Amount(amount=amount, asset=self._market["quote"], bitshares_instance=self.bitshares),
            account=self._account.name,
            expiration=self.expiration,
            returnOrderId=return_order_id,
            fee_asset=self.fee_asset['id'],
            *args,
            **kwargs
        )

        self.log.debug('Placed buy order {}'.format(buy_transaction))
        if return_order_id:
            buy_order = self.get_order(buy_transaction['orderid'], return_none=return_none)
            if buy_order and buy_order['deleted']:
                # The API doesn't return data on orders that don't exist
                # We need to calculate the data on our own
                buy_order = self.calculate_order_data('buy', buy_order, amount, price)
                buy_order['id'] = buy_transaction['orderid']
                self.recheck_orders = True
            return buy_order
        else:
            return True

    def place_market_sell_order(self, amount, price, return_none=False, invert=False, *args, **kwargs):
        """
        Places a sell order in the market.

        :param float | amount: Order amount in QUOTE
        :param float | price: Order price in BASE
        :param bool | return_none:
        :param bool | invert: True = return inverted sell order
        :param args:
        :param kwargs:
        :return:
        """
        symbol = self._market['quote']['symbol']
        precision = self._market['quote']['precision']
        quote_amount = truncate(amount, precision)
        return_order_id = kwargs.pop('returnOrderId', self.returnOrderId)

        # Don't try to place an order of size 0
        if not quote_amount:
            self.log.critical('Trying to sell 0')
            self.disabled = True
            return None

        # Make sure we have enough balance for the order
        if return_order_id and self.balance(self._market['quote']) < quote_amount:
            self.log.critical("Insufficient sell balance, needed {} {}".format(amount, symbol))
            self.disabled = True
            return None

        self.log.info(
            'Placing a sell order with {:.{prec}f} {} @ {:.8f}'.format(quote_amount, symbol, price, prec=precision)
        )

        # Place the order
        sell_transaction = self.retry_action(
            self._market.sell,
            price,
            Amount(amount=amount, asset=self._market["quote"]),
            account=self._account.name,
            expiration=self.expiration,
            returnOrderId=return_order_id,
            fee_asset=self.fee_asset['id'],
            *args,
            **kwargs
        )

        self.log.debug('Placed sell order {}'.format(sell_transaction))
        if return_order_id:
            sell_order = self.get_order(sell_transaction['orderid'], return_none=return_none)
            if sell_order and sell_order['deleted']:
                # The API doesn't return data on orders that don't exist, we need to calculate the data on our own
                sell_order = self.calculate_order_data('sell', sell_order, amount, price)
                sell_order['id'] = sell_transaction['orderid']
                self.recheck_orders = True
            if sell_order and invert:
                sell_order.invert()
            return sell_order
        else:
            return True

    def retry_action(self, action, *args, **kwargs):
        """
        Perform an action, and if certain suspected-to-be-spurious grapheme bugs occur, instead of bubbling the
        exception, it is quietly logged (level WARN), and try again tries a fixed number of times (MAX_TRIES) before
        failing.

        :param action:
        :return:
        """
        tries = 0
        while True:
            try:
                ref_block = self.bitshares.txbuffer.get("ref_block_num")
                ref_block_prefix = self.bitshares.txbuffer.get("ref_block_prefix")
                self.log.debug('Ref block num: {}, prefix: {}'.format(ref_block, ref_block_prefix))
                return action(*args, **kwargs)
            except bitsharesapi.exceptions.UnhandledRPCError as exception:
                if "Assert Exception: amount_to_sell.amount > 0" in str(exception):
                    if tries > MAX_TRIES:
                        raise
                    else:
                        tries += 1
                        self.log.warning("Ignoring: '{}'".format(str(exception)))
                        self.bitshares.txbuffer.clear()
                        self._account.refresh()
                        time.sleep(2)
                elif "now <= trx.expiration" in str(exception):  # Usually loss of sync to blockchain
                    if tries > MAX_TRIES:
                        raise
                    else:
                        tries += 1
                        self.log.warning("retrying on '{}'".format(str(exception)))
                        self.bitshares.txbuffer.clear()
                        time.sleep(6)  # Wait at least a BitShares block
                elif "trx.expiration <= now + chain_parameters.maximum_time_until_expiration" in str(exception):
                    if tries > MAX_TRIES:
                        info = self.bitshares.info()
                        raise Exception(
                            'Too much difference between node block time and trx expiration, please change '
                            'the node. Block time: {}, local time: {}'.format(
                                info['time'], formatTime(datetime.datetime.utcnow())
                            )
                        )
                    else:
                        tries += 1
                        self.log.warning(
                            'Too much difference between node block time and trx expiration, switching node'
                        )
                        self.bitshares.txbuffer.clear()
                        self.bitshares.rpc.next()
                elif "Assert Exception: delta.amount > 0: Insufficient Balance" in str(exception):
                    self.log.critical('Insufficient balance of fee asset')
                    raise
                elif "trx.ref_block_prefix == tapos_block_summary.block_id._hash" in str(exception):
                    if tries > MAX_TRIES:
                        raise
                    else:
                        # TODO: move node switch to a function
                        old = self.bitshares.rpc.url
                        self.log.warning('Got tapos_block_summary exception, switching node')
                        self.bitshares.clear()  # reinstantiates txbuilder (it caches ref_block_num)
                        # TODO: Notify still uses old node, needs to be switched!
                        self.bitshares.rpc.next()
                        new = self.bitshares.rpc.url
                        self.log.info('Old: {}, new: {}'.format(old, new))
                        tries += 1
                else:
                    raise

    @property
    def balances(self):
        """
        Returns all the balances of the account assigned for the worker.

        :return: Balances in list where each asset is in their own Amount object
        """
        return self._account.balances

    def get_own_orders(self, refresh=True):
        """
        Return the account's open orders in the current market.

        :param bool refresh: Use most recent data
        :return: List of Order objects
        """
        orders = []

        # Refresh account data
        if refresh:
            self._account.refresh()

        worker_market = self._market.get_string('/')

        for order in self._account.openorders:
            if worker_market == order.market and self._account.openorders:
                orders.append(order)

        return orders

    def get_all_own_orders(self, refresh=True):
        """
        Return the worker's open orders in all markets.

        :param bool refresh: Use most recent data
        :return: List of Order objects
        """
        # Refresh account data
        if refresh:
            self._account.refresh()

        orders = []
        for order in self._account.openorders:
            orders.append(order)

        return orders

    @property
    def account(self):
        """
        Return the full account as :class:`bitshares.account.Account` object! Can be refreshed by using ``x.refresh()``

        :return: object | Account
        """
        return self._account

    @property
    def market(self):
        """Return the market object as :class:`bitshares.market.Market`"""
        return self._market

    @property
    def base_asset(self):
        return self._market.get_string('/').split('/')[1]

    @property
    def quote_asset(self):
        return self._market.get_string('/').split('/')[0]

    @property
    def all_own_orders(self):
        """Return the worker's open orders in all markets."""
        return self.get_all_own_orders()

    @property
    def own_orders(self):
        """Return the account's open orders in the current market."""
        return self.get_own_orders()

    @staticmethod
    def get_updated_limit_order(limit_order):
        """
        Returns a modified limit_order so that when passed to Order class, will return an Order object with updated
        amount values.

        :param limit_order: an item of Account['limit_orders'] or bitshares.rpc.get_limit_orders()
        :return: Order
        """
        order = copy.deepcopy(limit_order)
        price = float(order['sell_price']['base']['amount']) / float(order['sell_price']['quote']['amount'])
        base_amount = float(order['for_sale'])
        quote_amount = base_amount / price
        order['sell_price']['base']['amount'] = base_amount
        order['sell_price']['quote']['amount'] = quote_amount
        return order

    @staticmethod
    def convert_asset(from_value, from_asset, to_asset):
        """
        Converts asset to another based on the latest market value.

        :param float | from_value: Amount of the input asset
        :param string | from_asset: Symbol of the input asset
        :param string | to_asset: Symbol of the output asset
        :return: float Asset converted to another asset as float value
        """
        market = Market('{}/{}'.format(from_asset, to_asset))
        ticker = market.ticker()
        latest_price = ticker.get('latest', {}).get('price', None)
        precision = market['base']['precision']

        return truncate((from_value * latest_price), precision)

    def convert_fee(self, fee_amount, fee_asset):
        """
        Convert fee amount in BTS to fee in fee_asset.

        :param float | fee_amount: fee amount paid in BTS
        :param Asset | fee_asset: fee asset to pay fee in
        :return: float | amount of fee_asset to pay fee
        """
        if isinstance(fee_asset, str):
            fee_asset = Asset(fee_asset, bitshares_instance=self.bitshares)

        if fee_asset['id'] == '1.3.0':
            # Fee asset is BTS, so no further calculations are needed
            return fee_amount
        else:
            if not self.core_exchange_rate:
                # Determine how many fee_asset is needed for core-exchange
                temp_market = Market(base=fee_asset, quote=Asset('1.3.0', bitshares_instance=self.bitshares))
                self.core_exchange_rate = temp_market.ticker()['core_exchange_rate']
            return fee_amount * self.core_exchange_rate['base']['amount']

    def get_order(self, order_id, return_none=True):
        """
        Get Order object with order_id.

        :param str | dict order_id: blockchain object id of the order can be an order dict with the id key in it
        :param bool return_none: return None instead of an empty Order object when the order doesn't exist
        :return: Order object
        """
        if not order_id:
            return None
        if 'id' in order_id:
            order_id = order_id['id']
        try:
            order = Order(order_id, bitshares_instance=self.bitshares)
        except Exception:
            logging.getLogger(__name__).error('Got an exception getting order id {}'.format(order_id))
            raise
        if return_none and order['deleted']:
            return None
        return order

    def is_partially_filled(self, order, threshold=0.3):
        """
        Checks whether order was partially filled.

        :param dict order: Order instance
        :param float fill_threshold: Order fill threshold, relative
        :return: bool True = Order is filled more than threshold
                      False = Order is not partially filled
        """
        if self.is_buy_order(order):
            order_type = 'buy'
            price = order['price']
        else:
            order_type = 'sell'
            price = order['price'] ** -1

        if order['for_sale']['amount'] != order['base']['amount']:
            diff_abs = order['base']['amount'] - order['for_sale']['amount']
            diff_rel = diff_abs / order['base']['amount']
            if diff_rel > threshold:
                self.log.debug(
                    'Partially filled {} order: {} {} @ {:.8f}, filled: {:.2%}'.format(
                        order_type, order['base']['amount'], order['base']['symbol'], price, diff_rel
                    )
                )
                return True
        return False
