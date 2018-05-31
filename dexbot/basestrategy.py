import logging
import time
import math

from .storage import Storage
from .statemachine import StateMachine

from events import Events
import bitsharesapi
import bitsharesapi.exceptions
from bitshares.amount import Amount
from bitshares.market import Market
from bitshares.account import Account
from bitshares.price import FilledOrder, Order, UpdateCallOrder
from bitshares.instance import shared_bitshares_instance


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

        Also, Base Strategy inherits :class:`dexbot.storage.Storage`
        which allows to permanently store data in a sqlite database
        using:

        ``basestrategy["key"] = "value"``

        .. note:: This applies a ``json.loads(json.dumps(value))``!

    Workers must never attempt to interact with the user, they must assume they are running unattended
    They can log events. If a problem occurs they can't fix they should set self.disabled = True and throw an exception
    The framework catches all exceptions thrown from event handlers and logs appropriately.
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

    def __init__(
        self,
        config,
        name,
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

        self.config = config
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

    def calculate_center_price(self, suppress_errors=False):
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

    def calculate_offset_center_price(self, spread, center_price=None, order_ids=None):
        """ Calculate center price which shifts based on available funds
        """
        if center_price is None:
            # No center price was given so we simply calculate the center price
            calculated_center_price = self.calculate_center_price()
            center_price = calculated_center_price
        else:
            # Center price was given so we only use the calculated center price
            # for quote to base asset conversion
            calculated_center_price = self.calculate_center_price(True)
            if not calculated_center_price:
                calculated_center_price = center_price

        total_balance = self.total_balance(order_ids)
        total = (total_balance['quote'] * calculated_center_price) + total_balance['base']

        if not total:  # Prevent division by zero
            percentage = 0
        else:
            percentage = (total_balance['base'] / total)
        lowest_price = center_price / math.sqrt(1 + spread)
        highest_price = center_price * math.sqrt(1 + spread)
        offset_center_price = ((highest_price - lowest_price) * percentage) + lowest_price
        return offset_center_price

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

    def clean_exit(self):
        """ Worker stop/exit wrapper. It should perform cleanup actions when terminating the bot.
            By default, just call cancel_all().
        """
        self.cancel_all()

    def market_buy(self, amount, price, return_none=False):
        symbol = self.market['base']['symbol']
        precision = self.market['base']['precision']
        base_amount = self.truncate(price * amount, precision)

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
            returnOrderId="head"
        )
        self.log.debug('Placed buy order {}'.format(buy_transaction))
        buy_order = self.get_order(buy_transaction['orderid'], return_none=return_none)
        if buy_order and buy_order['deleted']:
            # The API doesn't return data on orders that don't exist
            # We need to calculate the data on our own
            buy_order = self.calculate_order_data(buy_order, amount, price)
            self.recheck_orders = True

        return buy_order

    def market_sell(self, amount, price, return_none=False):
        symbol = self.market['quote']['symbol']
        precision = self.market['quote']['precision']
        quote_amount = self.truncate(amount, precision)

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
            returnOrderId="head"
        )
        self.log.debug('Placed sell order {}'.format(sell_transaction))
        sell_order = self.get_order(sell_transaction['orderid'], return_none=return_none)
        if sell_order and sell_order['deleted']:
            # The API doesn't return data on orders that don't exist
            # We need to calculate the data on our own
            sell_order = self.calculate_order_data(sell_order, amount, price)
            sell_order.invert()
            self.recheck_orders = True

        return sell_order

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
        self.cancel_all()
        self.clear_orders()
        self.clear()

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

    @staticmethod
    def truncate(number, decimals):
        """ Change the decimal point of a number without rounding
        """
        return math.floor(number * 10 ** decimals) / 10 ** decimals
