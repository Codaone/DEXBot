import datetime
import logging
import collections
import time
import math
import copy

from .storage import Storage
from .statemachine import StateMachine
from .config import Config
from .helper import truncate

from events import Events
import bitsharesapi
import bitsharesapi.exceptions
import bitshares.exceptions
from bitshares.amount import Amount
from bitshares.amount import Asset
from bitshares.market import Market
from bitshares.account import Account
from bitshares.price import FilledOrder, Order, UpdateCallOrder
from bitshares.instance import shared_bitshares_instance

MAX_TRIES = 3

ConfigElement = collections.namedtuple('ConfigElement', 'key type default title description extra')
# Strategies need to specify their own configuration values, so each strategy can have
# a class method 'configure' which returns a list of ConfigElement named tuples.
# Tuple fields as follows:
# - Key: the key in the bot config dictionary that gets saved back to config.yml
# - Type: one of "int", "float", "bool", "string", "choice"
# - Default: the default value. must be right type.
# - Title: name shown to the user, preferably not too long
# - Description: comments to user, full sentences encouraged
# - Extra:
#       For int: a (min, max, suffix) tuple
#       For float: a (min, max, precision, suffix) tuple
#       For string: a regular expression, entries must match it, can be None which equivalent to .*
#       For bool, ignored
#       For choice: a list of choices, choices are in turn (tag, label) tuples.
#       labels get presented to user, and tag is used as the value saved back to the config dict


class BaseStrategy(Storage, StateMachine, Events):
    """ Base Strategy and methods available in all Sub Classes that
        inherit this BaseStrategy.

        BaseStrategy inherits:

        * :class:`dexbot.storage.Storage`
        * :class:`dexbot.statemachine.StateMachine`
        * ``Events``

        Available attributes:

         * ``basestrategy.bitshares``: instance of ´`bitshares.BitShares()``
         * ``basestrategy.add_state``: Add a specific state
         * ``basestrategy.set_state``: Set finite state machine
         * ``basestrategy.get_state``: Change state of state machine
         * ``basestrategy.account``: The Account object of this worker
         * ``basestrategy.market``: The market used by this worker
         * ``basestrategy.orders``: List of open orders of the worker's account in the worker's market
         * ``basestrategy.balance``: List of assets and amounts available in the worker's account
         * ``basestrategy.log``: a per-worker logger (actually LoggerAdapter) adds worker-specific context:
            worker name & account (Because some UIs might want to display per-worker logs)

        Also, BaseStrategy inherits :class:`dexbot.storage.Storage`
        which allows to permanently store data in a sqlite database
        using:

        ``basestrategy["key"] = "value"``

        .. note:: This applies a ``json.loads(json.dumps(value))``!

        Workers must never attempt to interact with the user, they must assume they are running unattended.
        They can log events. If a problem occurs they can't fix they should set self.disabled = True and
        throw an exception. The framework catches all exceptions thrown from event handlers and logs appropriately.
    """

    __events__ = [
        'ontick',
        'onMarketUpdate',
        'onAccount',
        'error_ontick',
        'error_onMarketUpdate',
        'error_onAccount',
        'onOrderMatched',
        'onOrderPlaced',
        'onUpdateCallOrder',
    ]

    @classmethod
    def configure(cls, return_base_config=True):
        """
        Return a list of ConfigElement objects defining the configuration values for 
        this class
        User interfaces should then generate widgets based on this values, gather
        data and save back to the config dictionary for the worker.

        NOTE: when overriding you almost certainly will want to call the ancestor
        and then add your config values to the list.
        """
        # These configs are common to all bots
        base_config = [
            ConfigElement("account", "string", "", "Account", "BitShares account name for the bot to operate with", ""),
            ConfigElement("market", "string", "USD:BTS", "Market",
                          "BitShares market to operate on, in the format ASSET:OTHERASSET, for example \"USD:BTS\"",
                          r"[A-Z\.]+[:\/][A-Z\.]+"),
            ConfigElement('fee_asset', 'string', 'BTS', 'Fee asset', 'Asset to be used to pay transaction fees',
                          r'[A-Z\.]+')
        ]
        if return_base_config:
            return base_config
        return []

    def __init__(
        self,
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
        **kwargs
    ):
        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()

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

        self.worker = config["workers"][name]
        self._account = Account(
            self.worker["account"],
            full=True,
            bitshares_instance=self.bitshares
        )
        self._market = Market(
            config["workers"][name]["market"],
            bitshares_instance=self.bitshares
        )

        # Recheck flag - Tell the strategy to check for updated orders
        self.recheck_orders = False

        # Set fee asset
        fee_asset_symbol = self.worker.get('fee_asset')
        if fee_asset_symbol:
            try:
                self.fee_asset = Asset(fee_asset_symbol)
            except bitshares.exceptions.AssetDoesNotExistsException:
                self.fee_asset = Asset('1.3.0')
        else:
            self.fee_asset = Asset('1.3.0')

        # Settings for bitshares instance
        self.bitshares.bundle = bool(self.worker.get("bundle", False))

        # Disabled flag - this flag can be flipped to True by a worker and
        # will be reset to False after reset only
        self.disabled = False

        # Order expiration time in seconds
        self.expiration = 60 * 60 
# * 24 * 365 * 5

        # buy/sell actions will return order id by default
        self.returnOrderId = 'head'

        # CER cache
        self.core_exchange_rate = None

        # A private logger that adds worker identify data to the LogRecord
        self.log = logging.LoggerAdapter(
            logging.getLogger('dexbot.per_worker'),
            {'worker_name': name,
             'account': self.worker['account'],
             'market': self.worker['market'],
             'is_disabled': lambda: self.disabled}
        )

        self.orders_log = logging.LoggerAdapter(
            logging.getLogger('dexbot.orders_log'), {}
        )

    def _calculate_center_price(self, suppress_errors=False):
        ticker = self.market.ticker()
        highest_bid = ticker.get("highestBid")
        lowest_ask = ticker.get("lowestAsk")
        if highest_bid is None or highest_bid == 0.0:
            if not suppress_errors:
                self.log.critical(
                    "Cannot estimate center price, there is no highest bid."
                )
                self.disabled = True
            return None
        elif lowest_ask is None or lowest_ask == 0.0:
            if not suppress_errors:
                self.log.critical(
                    "Cannot estimate center price, there is no lowest ask."
                )
                self.disabled = True
            return None

        center_price = highest_bid['price'] * math.sqrt(lowest_ask['price'] / highest_bid['price'])
        return center_price

    def calculate_center_price(self, center_price=None, asset_offset=False, spread=None,
                               order_ids=None, manual_offset=0, suppress_errors=False):
        """ Calculate center price which shifts based on available funds
        """
        if center_price is None:
            # No center price was given so we simply calculate the center price
            calculated_center_price = self._calculate_center_price(suppress_errors)
        else:
            # Center price was given so we only use the calculated center price
            # for quote to base asset conversion
            calculated_center_price = self._calculate_center_price(True)
            if not calculated_center_price:
                calculated_center_price = center_price

        if center_price:
            calculated_center_price = center_price

        if asset_offset:
            total_balance = self.total_balance(order_ids)
            ticker = self.market.ticker()
            highest_bid = ticker.get("highestBid")
            lowest_ask = ticker.get("lowestAsk")
            total = total_balance['quote'] * float(lowest_ask) + total_balance['base']
            if not total:
                balance = 0.5 
            else:
                balance = (total_balance['base'] / total)
                lowest_price = calculated_center_price / (1 + spread)
                highest_price = calculated_center_price * (1 + spread)
# Returns a value between -1 and 1 # balance = (total_balance['base'] / total) * 2 - 1
                if lowest_price < highest_bid: lowest_price = highest_bid
                if highest_price > lowest_ask: highest_price = lowest_ask
                calculated_center_price = math.pow(highest_price, balance) * math.pow(lowest_price, 1 - balance)
#            if balance < 0:
# With less of base asset center price should be offset downward
#                calculated_center_price = calculated_center_price / math.sqrt(1 + spread * (balance * -1))
#            elif balance > 0:
# With more of base asset center price will be offset upwards
#                calculated_center_price = calculated_center_price * math.sqrt(1 + spread * balance)
#            else:
#                calculated_center_price = calculated_center_price
# Calculate final_offset_price if manual center price offset is given
        if manual_offset:
            if manual_offset < 0: calculated_center_price = calculated_center_price / (1 - manual_offset)
            elif manual_offset > 0: calculated_center_price = calculated_center_price * (1 + manual_offset)
#    bad symmetry  #  calculated_center_price = calculated_center_price + (calculated_center_price * manual_offset)
        return calculated_center_price

    @property
    def orders(self):
        """ Return the account's open orders in the current market
        """
        self.account.refresh()
        return [o for o in self.account.openorders if self.worker["market"] == o.market and self.account.openorders]

    @property
    def all_orders(self):
        """ Return the accounts's open orders in all markets
        """
        self.account.refresh()
        return [o for o in self.account.openorders]

    def get_buy_orders(self, sort=None, orders=None):
        """ Return buy orders
            :param str sort: DESC or ASC will sort the orders accordingly, default None.
            :param list orders: List of orders. If None given get all orders from Blockchain.
            :return list buy_orders: List of buy orders only.
        """
        buy_orders = []

        if not orders:
            orders = self.orders

        # Find buy orders
        for order in orders:
            if self.is_buy_order(order):
                buy_orders.append(order)
        if sort:
            buy_orders = self.sort_orders(buy_orders, sort)

        return buy_orders

    def get_sell_orders(self, sort=None, orders=None):
        """ Return sell orders
            :param str sort: DESC or ASC will sort the orders accordingly, default None.
            :param list orders: List of orders. If None given get all orders from Blockchain.
            :return list sell_orders: List of sell orders only.
        """
        sell_orders = []

        if not orders:
            orders = self.orders

        # Find sell orders
        for order in orders:
            if self.is_sell_order(order):
                sell_orders.append(order)

        if sort:
            sell_orders = self.sort_orders(sell_orders, sort)

        return sell_orders

    def is_buy_order(self, order):
        """ Checks if the order is Buy order
            :param order: Buy / Sell order
            :return: bool: True = Buy order
        """
        if order['base']['symbol'] == self.market['base']['symbol']:
            return True
        return False

    def is_sell_order(self, order):
        """ Checks if the order is Sell order
            :param order: Buy / Sell order
            :return: bool: True = Sell order
        """
        if order['base']['symbol'] != self.market['base']['symbol']:
            return True
        return False

    @staticmethod
    def sort_orders(orders, sort='DESC'):
        """ Return list of orders sorted ascending or descending
            :param list orders: list of orders to be sorted
            :param str sort: ASC or DESC. Default DESC
            :return list: Sorted list of orders.
        """
        if sort == 'ASC':
            reverse = False
        elif sort == 'DESC':
            reverse = True
        else:
            return None

        # Sort orders by price
        return sorted(orders, key=lambda order: order['price'], reverse=reverse)

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

    @staticmethod
    def get_order(order_id, return_none=True):
        """ Returns the Order object for the order_id

            :param str|dict order_id: blockchain object id of the order
                can be an order dict with the id key in it
            :param bool return_none: return None instead of an empty
                Order object when the order doesn't exist
        """
        if not order_id:
            return None
        if 'id' in order_id:
            order_id = order_id['id']
        order = Order(order_id)
        if return_none and order['deleted']:
            return None
        return order

    def get_updated_order(self, order_id):
        """ Tries to get the updated order from the API
            returns None if the order doesn't exist

            :param str|dict order_id: blockchain object id of the order
                can be an order dict with the id key in it
        """
        if isinstance(order_id, dict):
            order_id = order_id['id']

        # Get the limited order by id
        order = None
        for limit_order in self.account['limit_orders']:
            if order_id == limit_order['id']:
                order = limit_order
                break
        else:
            return order

        # Do not try to continue whether there is no order in the blockchain
        if not order:
            return None

        order = self.get_updated_limit_order(order)
        return Order(order, bitshares_instance=self.bitshares)

    @property
    def updated_orders(self):
        """ Returns all open orders as updated orders
        """
        self.account.refresh()

        limited_orders = []
        for order in self.account['limit_orders']:
            base_asset_id = order['sell_price']['base']['asset_id']
            quote_asset_id = order['sell_price']['quote']['asset_id']
            # Check if the order is in the current market
            if not self.is_current_market(base_asset_id, quote_asset_id):
                continue

            limited_orders.append(self.get_updated_limit_order(order))

        return [
            Order(o, bitshares_instance=self.bitshares)
            for o in limited_orders
        ]

    @staticmethod
    def get_updated_limit_order(limit_order):
        """ Returns a modified limit_order so that when passed to Order class,
            will return an Order object with updated amount values
            :param limit_order: an item of Account['limit_orders']
            :return: dict
        """
        o = copy.deepcopy(limit_order)
        price = float(o['sell_price']['base']['amount']) / float(o['sell_price']['quote']['amount'])
        base_amount = float(o['for_sale'])
        quote_amount = base_amount / price
        o['sell_price']['base']['amount'] = base_amount
        o['sell_price']['quote']['amount'] = quote_amount
        return o

    @property
    def market(self):
        """ Return the market object as :class:`bitshares.market.Market`
        """
        return self._market

    @property
    def account(self):
        """ Return the full account as :class:`bitshares.account.Account` object!

            Can be refreshed by using ``x.refresh()``
        """
        return self._account

    def balance(self, asset):
        """ Return the balance of your worker's account for a specific asset
        """
        return self._account.balance(asset)

    @property
    def balances(self):
        """ Return the balances of your worker's account
        """
        return self._account.balances

    def _callbackPlaceFillOrders(self, d):
        """ This method distinguishes notifications caused by Matched orders
            from those caused by placed orders
        """
        if isinstance(d, FilledOrder):
            self.onOrderMatched(d)
        elif isinstance(d, Order):
            self.onOrderPlaced(d)
        elif isinstance(d, UpdateCallOrder):
            self.onUpdateCallOrder(d)
        else:
            pass

    def execute(self):
        """ Execute a bundle of operations
        """
        self.bitshares.blocking = "head"
        r = self.bitshares.txbuffer.broadcast()
        self.bitshares.blocking = False
        return r

    def _cancel(self, orders):
        try:
            self.retry_action(
                self.bitshares.cancel,
                orders, account=self.account, fee_asset=self.fee_asset['id']
            )
        except bitsharesapi.exceptions.UnhandledRPCError as e:
            if str(e).startswith('Assert Exception: maybe_found != nullptr: Unable to find Object'):
                # The order(s) we tried to cancel doesn't exist
                self.bitshares.txbuffer.clear()
                return False
            else:
                self.log.exception("Unable to cancel order")
        except bitshares.exceptions.MissingKeyError:
            self.log.exception('Unable to cancel order(s), private key missing.')

        return True

    def cancel(self, orders, batch_only=False):
        """ Cancel specific order(s)
            :param list orders: list of orders to cancel
            :param bool batch_only: try cancel orders only in batch mode without one-by-one fallback
        """
        if not isinstance(orders, (list, set, tuple)):
            orders = [orders]

        orders = [order['id'] for order in orders if 'id' in order]

        success = self._cancel(orders)
        if not success and batch_only:
            return False
        if not success and len(orders) > 1 and not batch_only:
            # One of the order cancels failed, cancel the orders one by one
            for order in orders:
                self._cancel(order)
        return True

    def cancel_all(self):
        """ Cancel all orders of the worker's account
        """
        self.log.info('Canceling all orders')
        if self.orders:
            self.cancel(self.orders)
        self.log.info("Orders canceled")

    def pause(self):
        """ Pause the worker
        """
        # By default, just call cancel_all(); strategies may override this method
        self.cancel_all()
        self.clear_orders()

    def market_buy(self, quote_amount, price, return_none=False, *args, **kwargs):
        symbol = self.market['base']['symbol']
        precision = self.market['base']['precision']
        base_amount = truncate(price * quote_amount, precision)

        # Don't try to place an order of size 0
        if not base_amount:
            self.log.critical('Trying to buy 0')
            self.disabled = True
            return None

        # Make sure we have enough balance for the order
        if self.returnOrderId and self.balance(self.market['base']) < base_amount:
            self.log.critical(
                "Insufficient buy balance, needed {} {}".format(
                    base_amount, symbol)
            )
            self.disabled = True
            return None

        self.log.info(
            'Placing a buy order for {:.{prec}} {} @ {:.8f}'.format(
                base_amount, symbol, price, prec=precision)
        )

        # Place the order
        buy_transaction = self.retry_action(
            self.market.buy,
            price,
            Amount(amount=quote_amount, asset=self.market["quote"]),
            account=self.account.name,
            expiration=self.expiration,
            returnOrderId=self.returnOrderId,
            fee_asset=self.fee_asset['id'],
            *args,
            **kwargs
        )

        self.log.debug('Placed buy order {}'.format(buy_transaction))

        if self.returnOrderId:
            buy_order = self.get_order(buy_transaction['orderid'], return_none=return_none)
            if buy_order and buy_order['deleted']:
                # The API doesn't return data on orders that don't exist
                # We need to calculate the data on our own
                buy_order = self.calculate_order_data(buy_order, quote_amount, price)
                self.recheck_orders = True
            return buy_order
        else:
            return True

    def market_sell(self, quote_amount, price, return_none=False, *args, **kwargs):
        symbol = self.market['quote']['symbol']
        precision = self.market['quote']['precision']
        quote_amount = truncate(quote_amount, precision)

        # Don't try to place an order of size 0
        if not quote_amount:
            self.log.critical('Trying to sell 0')
            self.disabled = True
            return None

        # Make sure we have enough balance for the order
        if self.returnOrderId and self.balance(self.market['quote']) < quote_amount:
            self.log.critical(
                "Insufficient sell balance, needed {} {}".format(
                    quote_amount, symbol)
            )
            self.disabled = True
            return None

        self.log.info(
            'Placing a sell order for {:.{prec}f} {} @ {:.8f}'.format(
                quote_amount, symbol, price, prec=precision)
        )

        # Place the order
        sell_transaction = self.retry_action(
            self.market.sell,
            price,
            Amount(amount=quote_amount, asset=self.market["quote"]),
            account=self.account.name,
            expiration=self.expiration,
            returnOrderId=self.returnOrderId,
            fee_asset=self.fee_asset['id'],
            *args,
            **kwargs
        )

        self.log.debug('Placed sell order {}'.format(sell_transaction))
        if self.returnOrderId:
            sell_order = self.get_order(sell_transaction['orderid'], return_none=return_none)
            if sell_order and sell_order['deleted']:
                # The API doesn't return data on orders that don't exist
                # We need to calculate the data on our own
                sell_order = self.calculate_order_data(sell_order, quote_amount, price)
                sell_order.invert()
                self.recheck_orders = True
            return sell_order
        else:
            return True

    def calculate_order_data(self, order, amount, price):
        quote_asset = Amount(amount, self.market['quote']['symbol'])
        order['quote'] = quote_asset
        order['price'] = price
        base_asset = Amount(amount * price, self.market['base']['symbol'])
        order['base'] = base_asset
        return order

    def is_current_market(self, base_asset_id, quote_asset_id):
        """ Returns True if given asset id's are of the current market
        """
        if quote_asset_id == self.market['quote']['id']:
            if base_asset_id == self.market['base']['id']:
                return True
            return False
        if quote_asset_id == self.market['base']['id']:
            if base_asset_id == self.market['quote']['id']:
                return True
            return False
        return False

    def purge(self):
        """ Clear all the worker data from the database and cancel all orders
        """
        self.clear_orders()
        self.cancel_all()
        self.clear()

    @staticmethod
    def purge_worker_data(worker_name):
        """ Remove worker data from database only """
        Storage.clear_worker_data(worker_name)

    def total_balance(self, order_ids=None, return_asset=False):
        """ Returns the combined balance of the given order ids and the account balance
            The amounts are returned in quote and base assets of the market

            :param order_ids: list of order ids to be added to the balance
            :param return_asset: true if returned values should be Amount instances
            :return: dict with keys quote and base
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
            order_ids = [order['id'] for order in self.orders]
        if order_ids:
            orders_balance = self.orders_balance(order_ids)
            quote += orders_balance['quote']
            base += orders_balance['base']

        if return_asset:
            quote = Amount(quote, quote_asset)
            base = Amount(base, base_asset)

        return {'quote': quote, 'base': base}

    def account_total_value(self, return_asset):
        """ Returns the total value of the account in given asset
            :param str return_asset: Asset which is wanted as return
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
        for order in self.all_orders:
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

    @staticmethod
    def convert_asset(from_value, from_asset, to_asset):
        """Converts asset to another based on the latest market value
            :param from_value: Amount of the input asset
            :param from_asset: Symbol of the input asset
            :param to_asset: Symbol of the output asset
            :return: Asset converted to another asset as float value
        """
        market = Market('{}/{}'.format(from_asset, to_asset))
        ticker = market.ticker()
        latest_price = ticker.get('latest', {}).get('price', None)
        return from_value * latest_price

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

    def orders_balance(self, order_ids, return_asset=False):
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

        if return_asset:
            quote = Amount(quote, quote_asset)
            base = Amount(base, base_asset)

        return {'quote': quote, 'base': base}

    def retry_action(self, action, *args, **kwargs):
        """
        Perform an action, and if certain suspected-to-be-spurious graphene bugs occur,
        instead of bubbling the exception, it is quietly logged (level WARN), and try again
        tries a fixed number of times (MAX_TRIES) before failing
        """
        tries = 0
        while True:
            try:
                return action(*args, **kwargs)
            except bitsharesapi.exceptions.UnhandledRPCError as e:
                if "Assert Exception: amount_to_sell.amount > 0" in str(e):
                    if tries > MAX_TRIES:
                        raise
                    else:
                        tries += 1
                        self.log.warning("Ignoring: '{}'".format(str(e)))
                        self.bitshares.txbuffer.clear()
                        self.account.refresh()
                        time.sleep(2)
                elif "now <= trx.expiration" in str(e):  # Usually loss of sync to blockchain
                    if tries > MAX_TRIES:
                        raise
                    else:
                        tries += 1
                        self.log.warning("retrying on '{}'".format(str(e)))
                        self.bitshares.txbuffer.clear()
                        time.sleep(6)  # Wait at least a BitShares block
                else:
                    raise

    def write_order_log(self, worker_name, order):
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
