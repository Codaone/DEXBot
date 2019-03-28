import datetime
import copy
import logging
import math
import time

from dexbot.config import Config
from dexbot.storage import Storage
from dexbot.statemachine import StateMachine
from dexbot.helper import truncate
from dexbot.strategies.external_feeds.price_feed import PriceFeed
from dexbot.qt_queue.idle_queue import idle_add
from .config_parts.base_config import BaseConfig

from events import Events
import bitshares.exceptions
import bitsharesapi
import bitsharesapi.exceptions
from bitshares.account import Account
from bitshares.amount import Amount, Asset
from bitshares.dex import Dex
from bitshares.instance import shared_bitshares_instance
from bitshares.market import Market
from bitshares.price import FilledOrder, Order, UpdateCallOrder

# Number of maximum retries used to retry action before failing
MAX_TRIES = 3


class StrategyBase(Storage, StateMachine, Events):
    """ A strategy based on this class is intended to work in one market. This class contains
        most common methods needed by the strategy.

        All prices are passed and returned as BASE/QUOTE.
        (In the BREAD:USD market that would be USD/BREAD, 2.5 USD / 1 BREAD).
         - Buy orders reserve BASE
         - Sell orders reserve QUOTE

        Strategy inherits:
            * :class:`dexbot.storage.Storage` : Stores data to sqlite database
            * :class:`dexbot.statemachine.StateMachine`
            * ``Events``

        Available attributes:
            * ``worker.bitshares``: instance of ´`bitshares.BitShares()``
            * ``worker.add_state``: Add a specific state
            * ``worker.set_state``: Set finite state machine
            * ``worker.get_state``: Change state of state machine
            * ``worker.account``: The Account object of this worker
            * ``worker.market``: The market used by this worker
            * ``worker.orders``: List of open orders of the worker's account in the worker's market
            * ``worker.balance``: List of assets and amounts available in the worker's account
            * ``worker.log``: a per-worker logger (actually LoggerAdapter) adds worker-specific context:
                worker name & account (Because some UIs might want to display per-worker logs)

        Also, Worker inherits :class:`dexbot.storage.Storage`
        which allows to permanently store data in a sqlite database
        using:

        ``worker["key"] = "value"``

        .. note:: This applies a ``json.loads(json.dumps(value))``!

        Workers must never attempt to interact with the user, they must assume they are running unattended.
        They can log events. If a problem occurs they can't fix they should set self.disabled = True and
        throw an exception. The framework catches all exceptions thrown from event handlers and logs appropriately.
    """

    @classmethod
    def configure(cls, return_base_config=True):
        return BaseConfig.configure(return_base_config)

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        return BaseConfig.configure_details(include_default_tabs)

    __events__ = [
        'onAccount',
        'onMarketUpdate',
        'onOrderMatched',
        'onOrderPlaced',
        'ontick',
        'onUpdateCallOrder',
        'error_onAccount',
        'error_onMarketUpdate',
        'error_ontick',
    ]

    def __init__(self,
                 name,
                 config=None,
                 onAccount=None,
                 onOrderMatched=None,
                 onOrderPlaced=None,
                 onMarketUpdate=None,
                 onUpdateCallOrder=None,
                 ontick=None,
                 bitshares_instance=None,
                 *args,
                 **kwargs):

        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()

        # Dex instance used to get different fees for the market
        self.dex = Dex(self.bitshares)

        # Storage
        Storage.__init__(self, name)

        # Statemachine
        StateMachine.__init__(self, name)

        # Events
        Events.__init__(self)

        if ontick:
            self.ontick += ontick
        if onMarketUpdate:
            self.onMarketUpdate += onMarketUpdate
        if onAccount:
            self.onAccount += onAccount
        if onOrderMatched:
            self.onOrderMatched += onOrderMatched
        if onOrderPlaced:
            self.onOrderPlaced += onOrderPlaced
        if onUpdateCallOrder:
            self.onUpdateCallOrder += onUpdateCallOrder

        # Redirect this event to also call order placed and order matched
        self.onMarketUpdate += self._callbackPlaceFillOrders

        if config:
            self.config = config
        else:
            self.config = config = Config.get_worker_config_file(name)

        # Get worker's parameters from the config
        self.worker = config["workers"][name]

        # Get Bitshares account and market for this worker
        self._account = Account(self.worker["account"], full=True, bitshares_instance=self.bitshares)

        self._market = Market(config["workers"][name]["market"], bitshares_instance=self.bitshares)

        # Recheck flag - Tell the strategy to check for updated orders
        self.recheck_orders = False

        # Count of orders to be fetched from the API
        self.fetch_depth = 8

        # Set fee asset
        fee_asset_symbol = self.worker.get('fee_asset')

        if fee_asset_symbol:
            try:
                self.fee_asset = Asset(fee_asset_symbol)
            except bitshares.exceptions.AssetDoesNotExistsException:
                self.fee_asset = Asset('1.3.0')
        else:
            # If there is no fee asset, use BTS
            self.fee_asset = Asset('1.3.0')

        # CER cache
        self.core_exchange_rate = None

        # Ticker
        self.ticker = self.market.ticker

        # Settings for bitshares instance
        self.bitshares.bundle = bool(self.worker.get("bundle", False))

        # Disabled flag - this flag can be flipped to True by a worker and will be reset to False after reset only
        self.disabled = False

        # Order expiration time in seconds
        self.expiration = 60 * 60 * 24 * 365 * 5

        # buy/sell actions will return order id by default
        self.returnOrderId = 'head'

        # A private logger that adds worker identify data to the LogRecord
        self.log = logging.LoggerAdapter(
            logging.getLogger('dexbot.per_worker'),
            {
                'worker_name': name,
                'account': self.worker['account'],
                'market': self.worker['market'],
                'is_disabled': lambda: self.disabled
            }
        )

        self.orders_log = logging.LoggerAdapter(
            logging.getLogger('dexbot.orders_log'), {}
        )

    def _callbackPlaceFillOrders(self, d):
        """ This method distinguishes notifications caused by Matched orders from those caused by placed orders
        """
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
            self.retry_action(
                self.bitshares.cancel,
                orders, account=self.account, fee_asset=self.fee_asset['id']
            )
        except bitsharesapi.exceptions.UnhandledRPCError as exception:
            if str(exception).startswith('Assert Exception: maybe_found != nullptr: Unable to find Object'):
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
        """ Returns the total value of the account in given asset

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
                    updated_order['base']['amount'],
                    updated_order['base']['symbol'],
                    return_asset
                )

        return total_value

    def balance(self, asset, fee_reservation=0):
        """ Return the balance of your worker's account in a specific asset.

            :param string | asset: In what asset the balance is wanted to be returned
            :param float | fee_reservation: How much is saved in reserve for the fees
            :return: Balance of specific asset
        """
        balance = self._account.balance(asset)

        if fee_reservation > 0:
            balance['amount'] = balance['amount'] - fee_reservation

        return balance

    def calculate_order_data(self, order, amount, price):
        quote_asset = Amount(amount, self.market['quote']['symbol'])
        order['quote'] = quote_asset
        order['price'] = price
        base_asset = Amount(amount * price, self.market['base']['symbol'])
        order['base'] = base_asset
        return order

    def calculate_worker_value(self, unit_of_measure):
        """ Returns the combined value of allocated and available BASE and QUOTE. Total value is
            measured in "unit_of_measure", which is either BASE or QUOTE symbol.

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
        orders = self.get_own_orders
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

    def cancel_all_orders(self):
        """ Cancel all orders of the worker's account
        """
        self.log.info('Canceling all orders')

        if self.all_own_orders:
            self.cancel_orders(self.all_own_orders)

        self.log.info("Orders canceled")

    def cancel_orders(self, orders, batch_only=False):
        """ Cancel specific order(s)

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
        """ Returns the combined amount of the given order ids and the account balance
            The amounts are returned in quote and base assets of the market

            :param list | order_ids: list of order ids to be added to the balance
            :param bool | return_asset: true if returned values should be Amount instances
            :return: dict with keys quote and base
            Todo: When would we want the sum of a subset of orders? Why order_ids? Maybe just specify asset?
        """
        quote = 0
        base = 0
        quote_asset = self.market['quote']['id']
        base_asset = self.market['base']['id']

        # Total balance calculation
        for balance in self.balances:
            if balance.asset['id'] == quote_asset:
                quote += balance['amount']
            elif balance.asset['id'] == base_asset:
                base += balance['amount']

        if order_ids is None:
            # Get all orders from Blockchain
            order_ids = [order['id'] for order in self.get_own_orders]
        if order_ids:
            orders_balance = self.get_allocated_assets(order_ids)
            quote += orders_balance['quote']
            base += orders_balance['base']

        if return_asset:
            quote = Amount(quote, quote_asset)
            base = Amount(base, base_asset)

        return {'quote': quote, 'base': base}

    def get_allocated_assets(self, order_ids=None, return_asset=False):
        """ Returns the amount of QUOTE and BASE allocated in orders, and that do not show up in available balance

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
        quote_asset = self.market['quote']['id']
        base_asset = self.market['base']['id']

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
            quote = Amount(quote, quote_asset)
            base = Amount(base, base_asset)

        return {'quote': quote, 'base': base}

    def get_market_buy_orders(self, depth=10):
        """ Fetches most recent data and returns list of buy orders.

            :param int | depth: Amount of buy orders returned, Default=10
            :return: List of market sell orders
        """
        orders = self.get_market_orders(depth=depth)
        buy_orders = self.filter_buy_orders(orders)
        return buy_orders

    def get_market_sell_orders(self, depth=10):
        """ Fetches most recent data and returns list of sell orders.

            :param int | depth: Amount of sell orders returned, Default=10
            :return: List of market sell orders
        """
        orders = self.get_market_orders(depth=depth)
        sell_orders = self.filter_sell_orders(orders)
        return sell_orders

    def get_highest_market_buy_order(self, orders=None):
        """ Returns the highest buy order that is not own, regardless of order size.

            :param list | orders: Optional list of orders, if none given fetch newest from market
            :return: Highest market buy order or None
        """
        if not orders:
            orders = self.get_market_buy_orders(1)

        try:
            order = orders[0]
        except IndexError:
            self.log.info('Market has no buy orders.')
            return None

        return order

    def get_highest_own_buy_order(self, orders=None):
        """ Returns highest own buy order.

            :param list | orders:
            :return: Highest own buy order by price at the market or None
        """
        if not orders:
            orders = self.get_own_buy_orders()

        try:
            return orders[0]
        except IndexError:
            return None

    def get_lowest_market_sell_order(self, orders=None):
        """ Returns the lowest sell order that is not own, regardless of order size.

            :param list | orders: Optional list of orders, if none given fetch newest from market
            :return: Lowest market sell order or None
        """
        if not orders:
            orders = self.get_market_sell_orders(1)

        try:
            order = orders[0]
        except IndexError:
            self.log.info('Market has no sell orders.')
            return None

        return order

    def get_lowest_own_sell_order(self, orders=None):
        """ Returns lowest own sell order.

            :param list | orders:
            :return: Lowest own sell order by price at the market
        """
        if not orders:
            orders = self.get_own_sell_orders()

        try:
            return orders[0]
        except IndexError:
            return None

    def get_external_market_center_price(self, external_price_source):
        """ Get center price from an external market for current market pair

            :param external_price_source: External market name
            :return: Center price as float
        """
        self.log.debug('inside get_external_mcp, exchange: {} '.format(external_price_source))
        market = self.market.get_string('/')
        self.log.debug('market: {}  '.format(market))
        price_feed = PriceFeed(external_price_source, market)
        price_feed.filter_symbols()
        center_price = price_feed.get_center_price(None)
        self.log.debug('PriceFeed: {}'.format(center_price))

        if center_price is None:  # Try USDT
            center_price = price_feed.get_center_price("USDT")
            self.log.debug('Substitute USD/USDT center price: {}'.format(center_price))
            if center_price is None:  # Try consolidated
                center_price = price_feed.get_consolidated_price()
                self.log.debug('Consolidated center price: {}'.format(center_price))
        return center_price

    def get_market_center_price(self, base_amount=0, quote_amount=0, suppress_errors=False):
        """ Returns the center price of market including own orders.

            :param float | base_amount:
            :param float | quote_amount:
            :param bool | suppress_errors:
            :return: Market center price as float
        """
        center_price = None
        buy_price = self.get_market_buy_price(quote_amount=quote_amount,
                                              base_amount=base_amount, exclude_own_orders=False)
        sell_price = self.get_market_sell_price(quote_amount=quote_amount,
                                                base_amount=base_amount, exclude_own_orders=False)
        if buy_price is None or buy_price == 0.0:
            if not suppress_errors:
                self.log.critical("Cannot estimate center price, there is no highest bid.")
                self.disabled = True
                return None

        if sell_price is None or sell_price == 0.0:
            if not suppress_errors:
                self.log.critical("Cannot estimate center price, there is no lowest ask.")
                self.disabled = True
                return None
            # Calculate and return market center price. make sure buy_price has value
        if buy_price:
            center_price = buy_price * math.sqrt(sell_price / buy_price)
            self.log.debug('Center price in get_market_center_price: {:.8f} '.format(center_price))
        return center_price

    def get_market_buy_price(self, quote_amount=0, base_amount=0, exclude_own_orders=True):
        """ Returns the BASE/QUOTE price for which [depth] worth of QUOTE could be bought, enhanced with
            moving average or weighted moving average

            :param float | quote_amount:
            :param float | base_amount:
            :param bool | exclude_own_orders: Exclude own orders when calculating a price
            :return: price as float
        """
        market_buy_orders = []

        # Exclude own orders from orderbook if needed
        if exclude_own_orders:
            market_buy_orders = self.get_market_buy_orders(depth=self.fetch_depth)
            own_buy_orders_ids = [o['id'] for o in self.get_own_buy_orders()]
            market_buy_orders = [o for o in market_buy_orders if o['id'] not in own_buy_orders_ids]

        # In case amount is not given, return price of the highest buy order on the market
        if quote_amount == 0 and base_amount == 0:
            if exclude_own_orders:
                if market_buy_orders:
                    return float(market_buy_orders[0]['price'])
                else:
                    return '0.0'
            else:
                return float(self.ticker().get('highestBid'))

        # Like get_market_sell_price(), but defaulting to base_amount if both base and quote are specified.
        asset_amount = base_amount

        """ Since the purpose is never get both quote and base amounts, favor base amount if both given because
            this function is looking for buy price.
        """
        if base_amount > quote_amount:
            base = True
        else:
            asset_amount = quote_amount
            base = False

        if not market_buy_orders:
            market_buy_orders = self.get_market_buy_orders(depth=self.fetch_depth)
        market_fee = self.market['base'].market_fee_percent

        target_amount = asset_amount * (1 + market_fee)

        quote_amount = 0
        base_amount = 0
        missing_amount = target_amount

        for order in market_buy_orders:
            if base:
                # BASE amount was given
                if order['base']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['base']['amount']
                else:
                    base_amount += missing_amount
                    quote_amount += missing_amount / order['price']
                    break
            elif not base:
                # QUOTE amount was given
                if order['quote']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['quote']['amount']
                else:
                    base_amount += missing_amount * order['price']
                    quote_amount += missing_amount
                    break

        # Prevent division by zero
        if not quote_amount:
            return 0.0

        return base_amount / quote_amount

    def get_market_orders(self, depth=1, updated=True):
        """ Returns orders from the current market. Orders are sorted by price.

            get_market_orders() call does not have any depth limit.

            :param int | depth: Amount of orders per side will be fetched, default=1
            :param bool | updated: Return updated orders. "Updated" means partially filled orders will represent
                                   remainders and not just initial amounts
            :return: Returns a list of orders or None
        """
        orders = self.bitshares.rpc.get_limit_orders(self.market['base']['id'], self.market['quote']['id'], depth)
        if updated:
            orders = [self.get_updated_limit_order(o) for o in orders]
        orders = [Order(o, bitshares_instance=self.bitshares) for o in orders]
        return orders

    def get_orderbook_orders(self, depth=1):
        """ Returns orders from the current market split in bids and asks. Orders are sorted by price.

            Market.orderbook() call has hard-limit of depth=50 enforced by bitshares node.

            bids = buy orders
            asks = sell orders

            :param int | depth: Amount of orders per side will be fetched, default=1
            :return: Returns a dictionary of orders or None
        """
        return self.market.orderbook(depth)

    def get_market_sell_price(self, quote_amount=0, base_amount=0, exclude_own_orders=True):
        """ Returns the BASE/QUOTE price for which [quote_amount] worth of QUOTE could be bought,
            enhanced with moving average or weighted moving average.

            [quote/base]_amount = 0 means lowest regardless of size

            :param float | quote_amount:
            :param float | base_amount:
            :param bool | exclude_own_orders: Exclude own orders when calculating a price
            :return:
        """
        market_sell_orders = []

        # Exclude own orders from orderbook if needed
        if exclude_own_orders:
            market_sell_orders = self.get_market_sell_orders(depth=self.fetch_depth)
            own_sell_orders_ids = [o['id'] for o in self.get_own_sell_orders()]
            market_sell_orders = [o for o in market_sell_orders if o['id'] not in own_sell_orders_ids]

        # In case amount is not given, return price of the lowest sell order on the market
        if quote_amount == 0 and base_amount == 0:
            if exclude_own_orders:
                if market_sell_orders:
                    return float(market_sell_orders[0]['price'])
                else:
                    return '0.0'
            else:
                return float(self.ticker().get('lowestAsk'))

        asset_amount = quote_amount

        """ Since the purpose is never get both quote and base amounts, favor quote amount if both given because
            this function is looking for sell price.
        """
        if quote_amount > base_amount:
            quote = True
        else:
            asset_amount = base_amount
            quote = False

        if not market_sell_orders:
            market_sell_orders = self.get_market_sell_orders(depth=self.fetch_depth)
        market_fee = self.market['quote'].market_fee_percent

        target_amount = asset_amount * (1 + market_fee)

        quote_amount = 0
        base_amount = 0
        missing_amount = target_amount

        for order in market_sell_orders:
            if quote:
                # QUOTE amount was given
                if order['quote']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['quote']['amount']
                else:
                    base_amount += missing_amount * order['price']
                    quote_amount += missing_amount
                    break
            elif not quote:
                # BASE amount was given
                if order['base']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['base']['amount']
                else:
                    base_amount += missing_amount
                    quote_amount += missing_amount / order['price']
                    break

        # Prevent division by zero
        if not quote_amount:
            return 0.0

        return base_amount / quote_amount

    def get_market_spread(self, quote_amount=0, base_amount=0):
        """ Returns the market spread %, including own orders, from specified depth.

            :param float | quote_amount:
            :param float | base_amount:
            :return: Market spread as float or None
        """
        ask = self.get_market_sell_price(quote_amount=quote_amount, base_amount=base_amount, exclude_own_orders=False)
        bid = self.get_market_buy_price(quote_amount=quote_amount, base_amount=base_amount, exclude_own_orders=False)

        # Calculate market spread
        if ask == 0 or bid == 0:
            return None

        return ask / bid - 1

    def get_order_cancellation_fee(self, fee_asset):
        """ Returns the order cancellation fee in the specified asset.

            :param string | fee_asset: Asset in which the fee is wanted
            :return: Cancellation fee as fee asset
        """
        # Get fee
        fees = self.dex.returnFees()
        limit_order_cancel = fees['limit_order_cancel']
        return self.convert_fee(limit_order_cancel['fee'], fee_asset)

    def get_order_creation_fee(self, fee_asset):
        """ Returns the cost of creating an order in the asset specified

            :param fee_asset: QUOTE, BASE, BTS, or any other
            :return:
        """
        # Get fee
        fees = self.dex.returnFees()
        limit_order_create = fees['limit_order_create']
        return self.convert_fee(limit_order_create['fee'], fee_asset)

    def filter_buy_orders(self, orders, sort=None):
        """ Return own buy orders from list of orders. Can be used to pick buy orders from a list
            that is not up to date with the blockchain data.

            :param list | orders: List of orders
            :param string | sort: DESC or ASC will sort the orders accordingly, default None
            :return list | buy_orders: List of buy orders only
        """
        buy_orders = []

        # Filter buy orders
        for order in orders:
            # Check if the order is buy order, by comparing asset symbol of the order and the market
            if order['base']['symbol'] == self.market['base']['symbol']:
                buy_orders.append(order)

        if sort:
            buy_orders = self.sort_orders_by_price(buy_orders, sort)

        return buy_orders

    def filter_sell_orders(self, orders, sort=None, invert=True):
        """ Return sell orders from list of orders. Can be used to pick sell orders from a list
            that is not up to date with the blockchain data.

            :param list | orders: List of orders
            :param string | sort: DESC or ASC will sort the orders accordingly, default None
            :param bool | invert: return inverted orders or not
            :return list | sell_orders: List of sell orders only
        """
        sell_orders = []

        # Filter sell orders
        for order in orders:
            # Check if the order is buy order, by comparing asset symbol of the order and the market
            if order['base']['symbol'] != self.market['base']['symbol']:
                # Invert order before appending to the list, this gives easier comparison in strategy logic
                if invert:
                    order = order.invert()
                sell_orders.append(order)

        if sort:
            sell_orders = self.sort_orders_by_price(sell_orders, sort)

        return sell_orders

    def get_own_buy_orders(self, orders=None):
        """ Get own buy orders from current market, or from a set of orders passed for this function.

            :return: List of buy orders
        """
        if not orders:
            # List of orders was not given so fetch everything from the market
            orders = self.get_own_orders

        return self.filter_buy_orders(orders)

    def get_own_sell_orders(self, orders=None):
        """ Get own sell orders from current market

            :return: List of sell orders
        """
        if not orders:
            # List of orders was not given so fetch everything from the market
            orders = self.get_own_orders

        return self.filter_sell_orders(orders)

    def get_own_spread(self):
        """ Returns the difference between own closest opposite orders.

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
        """ Tries to get the updated order from the API. Returns None if the order doesn't exist

            :param str|dict order_id: blockchain Order object or id of the order
        """
        if isinstance(order_id, dict):
            order_id = order_id['id']

        # At first, try to look up own orders. This prevents RPC calls whether requested order is own order
        order = None
        for limit_order in self.account['limit_orders']:
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
        """ Execute a bundle of operations

            :return: dict: transaction
        """
        self.bitshares.blocking = "head"
        r = self.bitshares.txbuffer.broadcast()
        self.bitshares.blocking = False
        return r

    def is_buy_order(self, order):
        """ Check whether an order is buy order

            :param dict | order: dict or Order object
            :return bool
        """
        # Check if the order is buy order, by comparing asset symbol of the order and the market
        if order['base']['symbol'] == self.market['base']['symbol']:
            return True
        else:
            return False

    def is_current_market(self, base_asset_id, quote_asset_id):
        """ Returns True if given asset id's are of the current market

            :return: bool: True = Current market, False = Not current market
        """
        if quote_asset_id == self.market['quote']['id']:
            if base_asset_id == self.market['base']['id']:
                return True
            return False

        # Todo: Should we return true if market is opposite?
        if quote_asset_id == self.market['base']['id']:
            if base_asset_id == self.market['quote']['id']:
                return True
            return False

        return False

    def is_sell_order(self, order):
        """ Check whether an order is sell order

            :param dict | order: dict or Order object
            :return bool
        """
        # Check if the order is sell order, by comparing asset symbol of the order and the market
        if order['base']['symbol'] == self.market['quote']['symbol']:
            return True
        else:
            return False

    def pause(self):
        """ Pause the worker

            Note: By default pause cancels orders, but this can be overridden by strategy
        """
        # Cancel all orders from the market
        self.cancel_all_orders()

        # Removes worker's orders from local database
        self.clear_orders()

    def clear_all_worker_data(self):
        """ Clear all the worker data from the database and cancel all orders
        """
        # Removes worker's orders from local database
        self.clear_orders()

        # Cancel all orders from the market
        self.cancel_all_orders()

        # Finally clear all worker data from the database
        self.clear()

    def place_market_buy_order(self, amount, price, return_none=False, *args, **kwargs):
        """ Places a buy order in the market

            :param float | amount: Order amount in QUOTE
            :param float | price: Order price in BASE
            :param bool | return_none:
            :param args:
            :param kwargs:
            :return:
        """
        symbol = self.market['base']['symbol']
        precision = self.market['base']['precision']
        base_amount = truncate(price * amount, precision)
        return_order_id = kwargs.pop('returnOrderId', self.returnOrderId)

        # Don't try to place an order of size 0
        if not base_amount:
            self.log.critical('Trying to buy 0')
            self.disabled = True
            return None

        # Make sure we have enough balance for the order
        if return_order_id and self.balance(self.market['base']) < base_amount:
            self.log.critical("Insufficient buy balance, needed {} {}".format(base_amount, symbol))
            self.disabled = True
            return None

        self.log.info('Placing a buy order with {:.{prec}f} {} @ {:.8f}'
                      .format(base_amount, symbol, price, prec=precision))

        # Place the order
        buy_transaction = self.retry_action(
            self.market.buy,
            price,
            Amount(amount=amount, asset=self.market["quote"]),
            account=self.account.name,
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
                buy_order = self.calculate_order_data(buy_order, amount, price)
                self.recheck_orders = True
            return buy_order
        else:
            return True

    def place_market_sell_order(self, amount, price, return_none=False, invert=False, *args, **kwargs):
        """ Places a sell order in the market

            :param float | amount: Order amount in QUOTE
            :param float | price: Order price in BASE
            :param bool | return_none:
            :param bool | invert: True = return inverted sell order
            :param args:
            :param kwargs:
            :return:
        """
        symbol = self.market['quote']['symbol']
        precision = self.market['quote']['precision']
        quote_amount = truncate(amount, precision)
        return_order_id = kwargs.pop('returnOrderId', self.returnOrderId)

        # Don't try to place an order of size 0
        if not quote_amount:
            self.log.critical('Trying to sell 0')
            self.disabled = True
            return None

        # Make sure we have enough balance for the order
        if return_order_id and self.balance(self.market['quote']) < quote_amount:
            self.log.critical("Insufficient sell balance, needed {} {}".format(amount, symbol))
            self.disabled = True
            return None

        self.log.info('Placing a sell order with {:.{prec}f} {} @ {:.8f}'
                      .format(quote_amount, symbol, price, prec=precision))

        # Place the order
        sell_transaction = self.retry_action(
            self.market.sell,
            price,
            Amount(amount=amount, asset=self.market["quote"]),
            account=self.account.name,
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
                sell_order = self.calculate_order_data(sell_order, amount, price)
                self.recheck_orders = True
            if sell_order and invert:
                sell_order.invert()
            return sell_order
        else:
            return True

    def retry_action(self, action, *args, **kwargs):
        """ Perform an action, and if certain suspected-to-be-spurious grapheme bugs occur,
            instead of bubbling the exception, it is quietly logged (level WARN), and try again
            tries a fixed number of times (MAX_TRIES) before failing

            :param action:
            :return:
        """
        tries = 0
        while True:
            try:
                return action(*args, **kwargs)
            except bitsharesapi.exceptions.UnhandledRPCError as exception:
                if "Assert Exception: amount_to_sell.amount > 0" in str(exception):
                    if tries > MAX_TRIES:
                        raise
                    else:
                        tries += 1
                        self.log.warning("Ignoring: '{}'".format(str(exception)))
                        self.bitshares.txbuffer.clear()
                        self.account.refresh()
                        time.sleep(2)
                elif "now <= trx.expiration" in str(exception):  # Usually loss of sync to blockchain
                    if tries > MAX_TRIES:
                        raise
                    else:
                        tries += 1
                        self.log.warning("retrying on '{}'".format(str(exception)))
                        self.bitshares.txbuffer.clear()
                        time.sleep(6)  # Wait at least a BitShares block
                elif "Assert Exception: delta.amount > 0: Insufficient Balance" in str(exception):
                    self.log.critical('Insufficient balance of fee asset')
                    raise
                else:
                    raise

    def store_profit_estimation_data(self):
        """ Save total quote, total base, center_price, and datetime in to the database
        """
        assets = self.count_asset()
        account = self.config['workers'][self.worker_name].get('account')
        base_amount = assets['base']
        base_symbol = self.market['base'].get('symbol')
        quote_amount = assets['quote']
        quote_symbol = self.market['quote'].get('symbol')
        center_price = self.get_market_center_price()
        timestamp = time.time()

        self.store_balance_entry(account, self.worker_name, base_amount, base_symbol,
                                 quote_amount, quote_symbol, center_price, timestamp)

    def get_profit_estimation_data(self, seconds):
        """ Get balance history closest to the given time

            :returns The data as dict from the first timestamp going backwards from seconds argument
        """
        return self.get_balance_history(self.config['workers'][self.worker_name].get('account'),
                                        self.worker_name, seconds)

    def calc_profit(self):
        """ Calculate relative profit for the current worker
        """
        profit = 0
        time_range = 60 * 60 * 24 * 7  # 7 days
        current_time = time.time()
        timestamp = current_time - time_range

        # Fetch the balance from history
        old_data = self.get_balance_history(self.config['workers'][self.worker_name].get('account'), self.worker_name,
                                            timestamp, self.base_asset, self.quote_asset)
        if old_data:
            earlier_base = old_data.base_total
            earlier_quote = old_data.quote_total
            old_center_price = old_data.center_price
            center_price = self.get_market_center_price()

            if not (old_center_price or center_price):
                return profit

            # Calculate max theoretical balances based on starting price
            old_max_quantity_base = earlier_base + earlier_quote * old_center_price
            old_max_quantity_quote = earlier_quote + earlier_base / old_center_price

            if not (old_max_quantity_base or old_max_quantity_quote):
                return profit

            # Current balances
            balance = self.count_asset()
            base_balance = balance['base']
            quote_balance = balance['quote']

            # Calculate max theoretical current balances
            max_quantity_base = base_balance + quote_balance * center_price
            max_quantity_quote = quote_balance + base_balance / center_price

            base_roi = max_quantity_base / old_max_quantity_base
            quote_roi = max_quantity_quote / old_max_quantity_quote
            profit = round(math.sqrt(base_roi * quote_roi) - 1, 4)

        return profit

    def write_order_log(self, worker_name, order):
        """ Write order log to csv file

            :param string | worker_name: Name of the worker
            :param object | order: Order that was fulfilled
        """
        operation_type = 'TRADE'

        if order['base']['symbol'] == self.market['base']['symbol']:
            base_symbol = order['base']['symbol']
            base_amount = -order['base']['amount']
            quote_symbol = order['quote']['symbol']
            quote_amount = order['quote']['amount']
        else:
            base_symbol = order['quote']['symbol']
            base_amount = order['quote']['amount']
            quote_symbol = order['base']['symbol']
            quote_amount = -order['base']['amount']

        message = '{};{};{};{};{};{};{};{}'.format(
            worker_name,
            order['id'],
            operation_type,
            base_symbol,
            base_amount,
            quote_symbol,
            quote_amount,
            datetime.datetime.now().isoformat()
        )

        self.orders_log.info(message)

    @property
    def account(self):
        """ Return the full account as :class:`bitshares.account.Account` object!
            Can be refreshed by using ``x.refresh()``

            :return: object | Account
        """
        return self._account

    @property
    def balances(self):
        """ Returns all the balances of the account assigned for the worker.

            :return: Balances in list where each asset is in their own Amount object
        """
        return self._account.balances

    @property
    def base_asset(self):
        return self.worker['market'].split('/')[1]

    @property
    def quote_asset(self):
        return self.worker['market'].split('/')[0]

    @property
    def all_own_orders(self, refresh=True):
        """ Return the worker's open orders in all markets

            :param bool | refresh: Use most recent data
            :return: List of Order objects
        """
        # Refresh account data
        if refresh:
            self.account.refresh()

        orders = []
        for order in self.account.openorders:
            orders.append(order)

        return orders

    @property
    def get_own_orders(self):
        """ Return the account's open orders in the current market

            :return: List of Order objects
        """
        orders = []

        # Refresh account data
        self.account.refresh()

        for order in self.account.openorders:
            if self.worker["market"] == order.market and self.account.openorders:
                orders.append(order)

        return orders

    @property
    def market(self):
        """ Return the market object as :class:`bitshares.market.Market`
        """
        return self._market

    @staticmethod
    def convert_asset(from_value, from_asset, to_asset):
        """ Converts asset to another based on the latest market value

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
        """ Convert fee amount in BTS to fee in fee_asset

            :param float | fee_amount: fee amount paid in BTS
            :param Asset | fee_asset: fee asset to pay fee in
            :return: float | amount of fee_asset to pay fee
        """
        if isinstance(fee_asset, str):
            fee_asset = Asset(fee_asset)

        if fee_asset['id'] == '1.3.0':
            # Fee asset is BTS, so no further calculations are needed
            return fee_amount
        else:
            if not self.core_exchange_rate:
                # Determine how many fee_asset is needed for core-exchange
                temp_market = Market(base=fee_asset, quote=Asset('1.3.0'))
                self.core_exchange_rate = temp_market.ticker()['core_exchange_rate']
            return fee_amount * self.core_exchange_rate['base']['amount']

    @staticmethod
    def get_order(order_id, return_none=True):
        """ Get Order object with order_id

            :param str | dict order_id: blockchain object id of the order can be an order dict with the id key in it
            :param bool return_none: return None instead of an empty Order object when the order doesn't exist
            :return: Order object
        """
        if not order_id:
            return None
        if 'id' in order_id:
            order_id = order_id['id']
        try:
            order = Order(order_id)
        except Exception:
            logging.getLogger(__name__).error('Got an exception getting order id {}'.format(order_id))
            raise
        if return_none and order['deleted']:
            return None
        return order

    @staticmethod
    def get_updated_limit_order(limit_order):
        """ Returns a modified limit_order so that when passed to Order class,
            will return an Order object with updated amount values

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
    def purge_all_local_worker_data(worker_name):
        """ Removes worker's data and orders from local sqlite database

            :param worker_name: Name of the worker to be removed
        """
        Storage.clear_worker_data(worker_name)

    @staticmethod
    def sort_orders_by_price(orders, sort='DESC'):
        """ Return list of orders sorted ascending or descending by price

            :param list | orders: list of orders to be sorted
            :param string | sort: ASC or DESC. Default DESC
            :return list: Sorted list of orders
        """
        if sort.upper() == 'ASC':
            reverse = False
        elif sort.upper() == 'DESC':
            reverse = True
        else:
            return None

        # Sort orders by price
        return sorted(orders, key=lambda order: order['price'], reverse=reverse)

    # GUI updaters
    def update_gui_slider(self):
        ticker = self.market.ticker()
        latest_price = ticker.get('latest', {}).get('price', None)
        if not latest_price:
            return

        total_balance = self.count_asset()
        total = (total_balance['quote'] * latest_price) + total_balance['base']

        if not total:  # Prevent division by zero
            percentage = 50
        else:
            percentage = (total_balance['base'] / total) * 100
        idle_add(self.view.set_worker_slider, self.worker_name, percentage)
        self['slider'] = percentage

    def update_gui_profit(self):
        profit = self.calc_profit()

        # Add to idle queue
        idle_add(self.view.set_worker_profit, self.worker_name, float(profit))
        self['profit'] = profit
