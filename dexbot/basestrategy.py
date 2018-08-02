import datetime
import logging
import collections
import time
import math

from .storage import Storage
from .statemachine import StateMachine
from .config import Config
from .helper import truncate

from events import Events
import bitsharesapi
import bitsharesapi.exceptions
import bitshares.exceptions
from bitshares.amount import Amount
from bitshares.market import Market
from bitshares.account import Account
from bitshares.price import FilledOrder, Order, UpdateCallOrder
from bitshares.instance import shared_bitshares_instance
from .storage import Storage
from .statemachine import StateMachine
from . import graph

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


MAX_TRIES = 3


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
                          r"[A-Z\.]+[:\/][A-Z\.]+")
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

        # Settings for bitshares instance
        self.bitshares.bundle = bool(self.worker.get("bundle", False))

        # Disabled flag - this flag can be flipped to True by a worker and
        # will be reset to False after reset only
        self.disabled = False

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
        if not float(highest_bid):
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

    def calculate_center_price(self, center_price=None,
                               asset_offset=False, spread=None, order_ids=None, manual_offset=0):
        """ Calculate center price which shifts based on available funds
        """
        if center_price is None:
            # No center price was given so we simply calculate the center price
            calculated_center_price = self._calculate_center_price()
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
            total = (total_balance['quote'] * calculated_center_price) + total_balance['base']

            if not total:  # Prevent division by zero
                balance = 0
            else:
                # Returns a value between -1 and 1
                balance = (total_balance['base'] / total) * 2 - 1

            if balance < 0:
                # With less of base asset center price should be offset downward
                calculated_center_price = calculated_center_price / math.sqrt(1 + spread * (balance * -1))
            elif balance > 0:
                # With more of base asset center price will be offset upwards
                calculated_center_price = calculated_center_price * math.sqrt(1 + spread * balance)
            else:
                calculated_center_price = calculated_center_price

        # Calculate final_offset_price if manual center price offset is given
        if manual_offset:
            calculated_center_price = calculated_center_price + (calculated_center_price * manual_offset)

        return calculated_center_price

    @property
    def orders(self):
        """ Return the worker's open accounts in the current market
        """
        self.account.refresh()
        return [o for o in self.account.openorders if self.worker["market"] == o.market and self.account.openorders]

    @staticmethod
    def get_order(order_id, return_none=True):
        """ Returns the Order object for the order_id

            :param str|dict order_id: blockchain object id of the order
                can be a dict with the id key in it
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

    def get_updated_order(self, order):
        """ Tries to get the updated order from the API
            returns None if the order doesn't exist
        """
        if not order:
            return None
        if isinstance(order, str):
            order = {'id': order}
        for updated_order in self.updated_open_orders:
            if updated_order['id'] == order['id']:
                return updated_order
        return None

    @property
    def updated_open_orders(self):
        """
        Returns updated open Orders.
        account.openorders doesn't return updated values for the order so we calculate the values manually
        """
        self.account.refresh()
        self.account.ensure_full()

        limit_orders = self.account['limit_orders'][:]
        for o in limit_orders:
            base_amount = float(o['for_sale'])
            price = float(o['sell_price']['base']['amount']) / float(o['sell_price']['quote']['amount'])
            quote_amount = base_amount / price
            o['sell_price']['base']['amount'] = base_amount
            o['sell_price']['quote']['amount'] = quote_amount

        orders = [
            Order(o, bitshares_instance=self.bitshares)
            for o in limit_orders
        ]

        return [o for o in orders if self.worker["market"] == o.market]

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

    def get_converted_asset_amount(self, asset):
        """
        Returns asset amount converted to base asset amount
        """
        base_asset = self.market['base']
        quote_asset = Asset(asset['symbol'], bitshares_instance=self.bitshares)
        if base_asset['symbol'] == quote_asset['symbol']:
            return asset['amount']
        else:
            market = Market(
                base=base_asset,
                quote=quote_asset,
                bitshares_instance=self.bitshares)
            return market.ticker()['latest']['price'] * asset['amount']

    @property
    def test_mode(self):
        return self.config['node'] == "wss://node.testnet.bitshares.eu"

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
            self.retry_action(self.bitshares.cancel, orders, account=self.account)
        except bitsharesapi.exceptions.UnhandledRPCError as e:
            if str(e) == 'Assert Exception: maybe_found != nullptr: Unable to find Object':
                # The order(s) we tried to cancel doesn't exist
                self.bitshares.txbuffer.clear()
                return False
            else:
                self.log.exception("Unable to cancel order")
        except bitshares.exceptions.MissingKeyError:
            self.log.exception('Unable to cancel order(s), private key missing.')

        return True

    def cancel(self, orders):
        """ Cancel specific order(s)
        """
        if not isinstance(orders, (list, set, tuple)):
            orders = [orders]

        orders = [order['id'] for order in orders if 'id' in order]

        success = self._cancel(orders)
        if not success and len(orders) > 1:
            # One of the order cancels failed, cancel the orders one by one
            for order in orders:
                self._cancel(order)

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

    def market_buy(self, amount, price, return_none=False, *args, **kwargs):
        symbol = self.market['base']['symbol']
        precision = self.market['base']['precision']
        base_amount = truncate(price * amount, precision)

        # Make sure we have enough balance for the order
        if self.balance(self.market['base']) < base_amount:
            self.log.critical(
                "Insufficient buy balance, needed {} {}".format(
                    base_amount, symbol)
            )
            self.disabled = True
            return None

        self.log.info(
            'Placing a buy order for {} {} @ {}'.format(
                base_amount, symbol, round(price, 8))
        )

        # Place the order
        buy_transaction = self.retry_action(
            self.market.buy,
            price,
            Amount(amount=amount, asset=self.market["quote"]),
            account=self.account.name,
            returnOrderId="head",
            *args,
            **kwargs
        )
        buy_order = self.get_order(buy_transaction['orderid'], return_none=return_none)
        if buy_order and buy_order['deleted']:
            # The API doesn't return data on orders that don't exist
            # We need to calculate the data on our own
            buy_order = self.calculate_order_data(buy_order, amount, price)
            self.recheck_orders = True

        return buy_order

    def market_sell(self, amount, price, return_none=False, *args, **kwargs):
        symbol = self.market['quote']['symbol']
        precision = self.market['quote']['precision']
        quote_amount = truncate(amount, precision)

        # Make sure we have enough balance for the order
        if self.balance(self.market['quote']) < quote_amount:
            self.log.critical(
                "Insufficient sell balance, needed {} {}".format(
                    amount, symbol)
            )
            self.disabled = True
            return None

        self.log.info(
            'Placing a sell order for {} {} @ {}'.format(
                quote_amount, symbol, round(price, 8))
        )

        # Place the order
        sell_transaction = self.retry_action(
            self.market.sell,
            price,
            Amount(amount=amount, asset=self.market["quote"]),
            account=self.account.name,
            returnOrderId="head",
            *args,
            **kwargs
        )
        sell_order = self.get_order(sell_transaction['orderid'], return_none=return_none)
        if sell_order and sell_order['deleted']:
            # The API doesn't return data on orders that don't exist
            # We need to calculate the data on our own
            sell_order = self.calculate_order_data(sell_order, amount, price)
            sell_order.invert()
            self.recheck_orders = True

        return sell_order

    def record_balances(self, baseprice):
        self.save_journal([('price', baseprice),
                           (self.market['quote']['symbol'],
                            self.balance(self.market['quote'])),
                           (self.market['base']['symbol'], self.balance(self.market['base']))])

    def calculate_order_data(self, order, amount, price):
        quote_asset = Amount(amount, self.market['quote']['symbol'])
        order['quote'] = quote_asset
        order['price'] = price
        base_asset = Amount(amount * price, self.market['base']['symbol'])
        order['base'] = base_asset
        return order

    def purge(self):
        """ Clear all the worker data from the database and cancel all orders
        """
        self.clear_orders()
        self.cancel_all()
        self.clear()

    def graph(self, start, end_=None):
        """Draw a graph over the specified time period (both datetime)
        Uses routine suitable for one-market trading workers
        More complex workers (arbitrage, etc) may need to override to provide
        meaningful graphs
        """
        data = graph.query_to_dicts(self.query_journal(start, end_))
        if len(data) < 2:
            # not enough data to graph
            return None
        data = graph.rebase_data(data,
                                 self.market['quote']['symbol'],
                                 self.market['base']['symbol'])
        return graph.do_graph(data)

    @staticmethod
    def purge_worker_data(worker_name):
        Storage.clear_worker_data(worker_name)

    @staticmethod
    def get_order_amount(order, asset_type):
        try:
            order_amount = order[asset_type]['amount']
        except (KeyError, TypeError):
            order_amount = 0
        return order_amount

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

        for balance in self.balances:
            if balance.asset['id'] == quote_asset:
                quote += balance['amount']
            elif balance.asset['id'] == base_asset:
                base += balance['amount']

        orders_balance = self.orders_balance(order_ids)
        quote += orders_balance['quote']
        base += orders_balance['base']

        if return_asset:
            quote = Amount(quote, quote_asset)
            base = Amount(base, base_asset)

        return {'quote': quote, 'base': base}

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
