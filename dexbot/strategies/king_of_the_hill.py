# Python imports
from datetime import datetime, timedelta

# Project imports
from dexbot.strategies.base import StrategyBase  # , ConfigElement

STRATEGY_NAME = 'King of the Hill'


class Strategy(StrategyBase):
    """ King of the Hill strategy

        This worker will place a buy or sell order for an asset and update so that the users order stays closest to the
        opposing order book.

        Moving forward: If any other orders are placed closer to the opposing order book the worker will cancel the
        users order and replace it with one that is the smallest possible increment closer to the opposing order book
        than any other orders.

        Moving backward: If the users order is the closest to the opposing order book but a gap opens up on the order
        book behind the users order the worker will cancel the order and place it at the smallest possible increment
        closer to the opposing order book than any other order.
    """

    @classmethod
    def configure(cls, return_base_config=True):
        return StrategyBase.configure(return_base_config) + [
            ConfigElement('mode', 'choice', 'both', 'Mode',
                          'Operational mode', ([
                    ('both', 'Buy + sell'),
                    ('buy', 'Buy only'),
                    ('sell', 'Sell only')])),
            ConfigElement('lower_bound', 'float', 0, 'Lower bound',
                          'Do not place sell orders lower than this bound',
                          (0, 10000000, 8, '')),
            ConfigElement('upper_bound', 'float', 0, 'Upper bound',
                          'Do not place buy orders higher than this bound',
                          (0, 10000000, 8, '')),
            ConfigElement('buy_order_amount', 'float', 0, 'Amount (BASE)',
                          'Fixed order size for buy orders, expressed in BASE asset, unless "relative order size"'
                          ' selected', (0, None, 8, '')),
            ConfigElement('sell_order_amount', 'float', 0, 'Amount (QUOTE)',
                          'Fixed order size for sell orders, expressed in QUOTE asset, unless "relative order size"'
                          ' selected', (0, None, 8, '')),
            ConfigElement('relative_order_size', 'bool', False, 'Relative order size',
                          'Amount is expressed as a percentage of the account balance of quote/base asset', None),
            ConfigElement('buy_order_size_threshold', 'float', 0, 'Ignore smaller buy orders',
                          'Ignore buy orders which are smaller than this threshold (BASE). '
                          'If unset, use own order size as a threshold', (0, None, 8, '')),
            ConfigElement('sell_order_size_threshold', 'float', 0, 'Ignore smaller sell orders',
                          'Ignore sell orders which are smaller than this threshold (QUOTE). '
                          'If unset, use own order size as a threshold', (0, None, 8, '')),
            ConfigElement('min_order_lifetime', 'int', 6, 'Min order lifetime',
                          'Minimum order lifetime before order reset, seconds', (1, None, ''))
        ]

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        return StrategyBase.configure_details(include_default_tabs) + []

    def __init__(self, *args, **kwargs):
        # Initializes StrategyBase class
        super().__init__(*args, **kwargs)

        self.log.info("Initializing {}...".format(STRATEGY_NAME))

        # Tick counter
        self.counter = 0

        # Define Callbacks
        self.onMarketUpdate += self.maintain_strategy
        self.ontick += self.tick

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        # Get view
        self.view = kwargs.get('view')

        self.worker_name = kwargs.get('name')

        self.mode = self.worker.get('mode', 'both')
        self.buy_order_amount = float(self.worker.get('buy_order_amount', 0))
        self.sell_order_amount = float(self.worker.get('sell_order_amount', 0))
        self.is_relative_order_size = self.worker.get(
            'relative_order_size', False)
        self.buy_order_size_threshold = self.worker.get(
            'buy_order_size_threshold', 0)
        self.sell_order_size_threshold = self.worker.get(
            'sell_order_size_threshold', 0)
        self.upper_bound = self.worker.get('upper_bound', 0)
        self.lower_bound = self.worker.get('lower_bound', 0)
        self.min_order_lifetime = self.worker.get('min_order_lifetime', 1)
        # self.buy_price = None
        # self.sell_price = None
        self.orders = []
        # Current order we must be higher
        self.buy_order_to_beat = None
        self.sell_order_to_beat = None
        # We put an order to be higher than that order
        self.beaten_buy_order = None
        self.beaten_sell_order = None
        # Set last check in the past to get immediate check at startup
        self.last_check = datetime(2000, 1, 1)
        self.min_check_interval = self.min_order_lifetime

        if self.view:
            self.update_gui_slider()

        # Make sure we're starting from scratch as we don't keeping orders in the db
        self.cancel_all_orders()

        self.log.info("{} initialized.".format(STRATEGY_NAME))

    def maintain_strategy(self, *args):
        """ Strategy main logic
        """
        delta = datetime.now() - self.last_check
        # Only allow to check orders whether minimal time passed
        if delta < timedelta(seconds=self.min_check_interval):
            return

        self.calc_order_prices()

        if self.orders:
            self.check_orders()
        else:
            self.place_orders()

        self.last_check = datetime.now()

    def check_orders(self):
        """ Check whether own orders needs intervention
        """
        orders_to_delete = []
        for stored_order in self.orders:
            order = self.get_order(stored_order['id'])
            order_type = self.get_order_type(stored_order)

            if order:
                is_partially_filled = self.is_partially_filled(
                    order, threshold=0.8)
                if is_partially_filled:
                    # If own order filled too much, replace it with new order
                    # TODO: check cancel_orders() return value after #467 fix
                    self.log.info(
                        'Own {} order filled too much, resetting'.format(order_type))
                    self.cancel_orders(order)
                    orders_to_delete.append(stored_order['id'])
                    self.place_order(order_type)
                # Check if someone put order above ours or beaten order was canceled
                elif ((order_type == 'buy' and (not self.get_order(self.beaten_buy_order) or
                                                stored_order['price'] < self.buy_price)) or
                      (order_type == 'sell' and (not self.get_order(self.beaten_sell_order) or
                                                 stored_order['price'] ** -1 > self.sell_price))):
                    self.log.debug('Moving {} order'.format(order_type))
                    self.cancel_orders(order)
                    orders_to_delete.append(stored_order['id'])
                    self.place_order(order_type)
            # Own order is not there
            else:
                self.log.info(
                    'Own {} order filled, placing a new one'.format(order_type))
                orders_to_delete.append(stored_order['id'])
                self.place_order(order_type)

        self.orders = [
            order for order in self.orders if order['id'] not in orders_to_delete]

    def get_order_type(self, order):
        """ Determine order type and return it as a string
        """
        if self.is_buy_order(order):
            return 'buy'
        else:
            return 'sell'

    def calc_order_prices(self):
        """ Calculate prices of our orders
        """
        # Obtain orderbook orders excluding our orders
        market_orders = self.get_market_orders(depth=100)
        own_orders_ids = [order['id'] for order in self.get_own_orders]
        print(own_orders_ids)
        market_orders = [
            order for order in market_orders if order['id'] not in own_orders_ids]
        print('market_orders:', market_orders)
        buy_orders = self.filter_buy_orders(market_orders)
        sell_orders = self.filter_sell_orders(market_orders, invert=True)
        print('buy_orders:', buy_orders)
        print('sell_orders:', sell_orders)
        # xxx_order_size_threshold indicates order price we need to beat
        sell_order_size_threshold = self.sell_order_size_threshold
        if not sell_order_size_threshold:
            sell_order_size_threshold = self.amount_quote

        buy_order_size_threshold = self.buy_order_size_threshold
        if not buy_order_size_threshold:
            buy_order_size_threshold = self.amount_base

        # Note that we're operating on inverted orders here
        for order in sell_orders:
            if order['quote']['amount'] > sell_order_size_threshold:
                # Calculate price to beat order by slightly decreasing BASE amount
                new_base = order['base']['amount'] - 2 * \
                           10 ** -self.market['base']['precision']
                # Don't let to place sell orders lower than lower bound
                self.sell_price = max(
                    new_base / order['quote']['amount'], self.lower_bound)
                print(self.sell_price)
                self.sell_order_to_beat = order['id']
                self.log.debug(
                    'Sell price to be higher: {:.8f}'.format(self.sell_price))
                break

        for order in buy_orders:
            if order['base']['amount'] > buy_order_size_threshold:
                new_quote = order['quote']['amount'] - 2 * \
                            10 ** -self.market['quote']['precision']
                # Don't let to place buy orders above upper bound
                self.buy_price = min(
                    order['base']['amount'] / new_quote, self.upper_bound)
                print(self.buy_price)
                self.buy_order_to_beat = order['id']
                self.log.debug(
                    'Buy price to be higher: {:.8f}'.format(self.buy_price))
                break

    def place_order(self, order_type):
        """ Place single order
        """
        new_order = None

        if order_type == 'buy':
            if not self.buy_price:
                self.log.error(
                    'Cannot determine buy price, correct your bounds and/or ignore thresholds')
                self.disabled = True
                return
            amount_base = self.amount_base
            if not amount_base:
                self.log.error(
                    'Cannot place {} order with 0 amount. Adjust your settings!'.format(order_type))
                self.disabled = True
                return
            amount_quote = amount_base / self.buy_price
            # Prevent too small amounts
            if self.is_too_small_amounts(amount_quote, amount_base):
                self.log.error(
                    'Amount for {} order is too small'.format(order_type))
                return
            print('before:')
            new_order = self.place_market_buy_order(
                amount_quote, self.buy_price)
            print(new_order)
            self.beaten_buy_order = self.buy_order_to_beat
            print(self.beaten_buy_order)
        elif order_type == 'sell':
            if not self.sell_price:
                self.log.error(
                    'Cannot determine sell price, correct your bounds and/or ignore thresholds')
                self.disabled = True
                return
            amount_quote = self.amount_quote
            if not amount_quote:
                self.log.error(
                    'Cannot place {} order with 0 amount. Adjust your settings!'.format(order_type))
                self.disabled = True
                return
            amount_base = amount_quote * self.sell_price
            # Prevent too small amounts
            if self.is_too_small_amounts(amount_quote, amount_base):
                self.log.error(
                    'Amount for {} order is too small'.format(order_type))
                return
            new_order = self.place_market_sell_order(
                amount_quote, self.sell_price)
            self.beaten_sell_order = self.sell_order_to_beat

        if new_order:
            # Store own orders into list to perform checks later
            self.orders.append(new_order)
        else:
            self.log.error('Failed to place {} order'.format(order_type))

    def place_orders(self):
        """ Place new orders
        """
        place_buy = False
        place_sell = False

        if self.mode == 'both':
            place_buy = True
            place_sell = True
        elif self.mode == 'buy':
            place_buy = True
        elif self.mode == 'sell':
            place_sell = True

        if place_buy:
            self.place_order('buy')
        if place_sell:
            self.place_order('sell')

    @property
    def amount_quote(self):
        """ Get quote amount, calculate if order size is relative
        """
        amount = self.sell_order_amount
        if self.is_relative_order_size:
            quote_balance = float(self.balance(self.market['quote']))
            amount = quote_balance * (amount / 100)

        return amount

    @property
    def amount_base(self):
        """ Get base amount, calculate if order size is relative
        """
        amount = self.buy_order_amount
        if self.is_relative_order_size:
            base_balance = float(self.balance(self.market['base']))
            amount = base_balance * (amount / 100)

        return amount

    def error(self, *args, **kwargs):
        """ Defines what happens when error occurs """
        self.disabled = True

    def tick(self, d):
        """ Ticks come in on every block """
        if not (self.counter or 0) % 4:
            self.maintain_strategy()
        self.counter += 1
