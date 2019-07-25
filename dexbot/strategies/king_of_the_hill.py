# Python imports
import copy

from datetime import datetime, timedelta
from decimal import Decimal

# Project imports
from dexbot.strategies.base import StrategyBase
from dexbot.strategies.config_parts.koth_config import KothConfig


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
        return KothConfig.configure(return_base_config)

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        return KothConfig.configure_details(include_default_tabs)

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
        self.top_buy_price = 0
        self.top_sell_price = 0
        self.buy_order_amount = float(self.worker.get('buy_order_amount', 0))
        self.sell_order_amount = float(self.worker.get('sell_order_amount', 0))
        self.is_relative_order_size = self.worker.get('relative_order_size', False)
        self.buy_order_size_threshold = self.worker.get('buy_order_size_threshold', 0)
        self.sell_order_size_threshold = self.worker.get('sell_order_size_threshold', 0)
        self.upper_bound = self.worker.get('upper_bound', 0)
        self.lower_bound = self.worker.get('lower_bound', 0)
        self.min_order_lifetime = self.worker.get('min_order_lifetime', 1)

        self.orders = {}
        # Current order we must be higher
        self.buy_order_to_beat = None
        self.sell_order_to_beat = None
        # We put an order to be higher than that order
        self.beaten_buy_order = None
        self.beaten_sell_order = None
        # Set last check in the past to get immediate check at startup
        self.last_check = datetime(2000, 1, 1)
        self.min_check_interval = self.min_order_lifetime
        self.partial_fill_threshold = 0.8

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

        if self.orders:
            self.check_orders()
        else:
            self.place_orders()

        self.last_check = datetime.now()

    def check_orders(self):
        """ Check whether own orders needs intervention
        """
        self.get_top_prices()

        orders = copy.deepcopy(self.orders)
        for order_type, order_id in orders.items():
            order = self.get_order(order_id)
            need_cancel = False

            if order:
                is_partially_filled = self.is_partially_filled(order, threshold=self.partial_fill_threshold)
                if is_partially_filled:
                    # If own order filled too much, replace it with new order
                    self.log.info('Own {} order filled too much, resetting'.format(order_type))
                    need_cancel = True
                # Check if someone put order above ours or beaten order was canceled
                elif order_type == 'buy' and not self.get_order(self.beaten_buy_order):
                    self.log.debug('No beaten buy order on market')
                    need_cancel = True
                elif order_type == 'buy' and order['price'] < self.top_buy_price:
                    self.log.debug('Detected an order above ours')
                    need_cancel = True
                elif order_type == 'sell' and not self.get_order(self.beaten_sell_order):
                    self.log.debug('No beaten sell order on market')
                    need_cancel = True
                elif order_type == 'sell' and order['price'] ** -1 > self.top_sell_price:
                    self.log.debug('Detected an order above ours')
                    need_cancel = True

            # Own order is not there
            else:
                self.log.info('Own {} order filled, placing a new one'.format(order_type))
                self.place_order(order_type)

            if need_cancel and self.cancel_orders(order):
                self.place_order(order_type)

    def get_top_prices(self):
        """ Get current top prices (foreign orders)
        """
        # Obtain orderbook orders excluding our orders
        market_orders = self.get_market_orders(depth=100)
        own_orders_ids = [order['id'] for order in self.own_orders]
        market_orders = [order for order in market_orders if order['id'] not in own_orders_ids]
        buy_orders = self.filter_buy_orders(market_orders)
        sell_orders = self.filter_sell_orders(market_orders, invert=True)

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
                self.top_sell_price = order['price']
                self.sell_order_to_beat = order['id']
                if self.top_sell_price < self.lower_bound:
                    self.log.debug(
                        'Top sell price to be higher {:.8f} < lower bound {:.8f}'.format(
                            self.top_sell_price, self.lower_bound
                        )
                    )
                    self.top_sell_price = self.lower_bound
                else:
                    self.log.debug('Top sell price to be higher: {:.8f}'.format(self.top_sell_price))
                break

        for order in buy_orders:
            if order['base']['amount'] > buy_order_size_threshold:
                self.top_buy_price = order['price']
                self.buy_order_to_beat = order['id']
                if self.top_buy_price > self.upper_bound:
                    self.log.debug(
                        'Top buy price to be higher {:.8f} > upper bound {:.8f}'.format(
                            self.top_buy_price, self.upper_bound
                        )
                    )
                    self.top_buy_price = self.upper_bound
                else:
                    self.log.debug('Top buy price to be higher: {:.8f}'.format(self.top_buy_price))
                break

    def is_too_small_amounts(self, amount_quote, amount_base):
        """ Check whether amounts are within asset precision limits
            :param Decimal amount_quote: QUOTE asset amount
            :param Decimal amount_base: BASE asset amount
            :return: bool True = amounts are too small
                          False = amounts are within limits
        """
        if (
            amount_quote < Decimal(10) ** -self.market['quote']['precision']
            or amount_base < Decimal(10) ** -self.market['base']['precision']
        ):
            return True

        return False

    def place_order(self, order_type):
        """ Place single order
        """
        new_order = None

        if order_type == 'buy':
            if not self.top_buy_price:
                self.log.error('Cannot determine top buy price, correct your bounds and/or ignore thresholds')
                self.disabled = True
                return

            amount_base = Decimal(self.amount_base).quantize(Decimal(0).scaleb(-self.market['base']['precision']))
            if not amount_base:
                self.log.error('Cannot place {} order with 0 amount. Adjust your settings!'.format(order_type))
                self.disabled = True
                return

            price = Decimal(self.top_buy_price)
            amount_quote = (amount_base / price).quantize(Decimal(0).scaleb(-self.market['quote']['precision']))
            price = amount_base / amount_quote
            while price <= self.top_buy_price:
                # Decrease quote amount until price will become higher
                amount_quote -= Decimal(10) ** -self.market['quote']['precision']
                price = amount_base / amount_quote

            # Limit price by upper bound
            if price > self.upper_bound:
                price = Decimal(self.upper_bound)
                amount_quote = amount_base / price

            # Prevent too small amounts
            if self.is_too_small_amounts(amount_quote, amount_base):
                self.log.error('Amount for {} order is too small'.format(order_type))
                return

            new_order = self.place_market_buy_order(float(amount_quote), float(price))
            self.beaten_buy_order = self.buy_order_to_beat
        elif order_type == 'sell':
            if not self.top_sell_price:
                self.log.error('Cannot determine top sell price, correct your bounds and/or ignore thresholds')
                self.disabled = True
                return

            amount_quote = Decimal(self.amount_quote).quantize(Decimal(0).scaleb(-self.market['quote']['precision']))
            if not amount_quote:
                self.log.error('Cannot place {} order with 0 amount. Adjust your settings!'.format(order_type))
                self.disabled = True
                return

            price = Decimal(self.top_sell_price)
            amount_base = (amount_quote * price).quantize(Decimal(0).scaleb(-self.market['base']['precision']))
            price = amount_base / amount_quote
            while price >= self.top_sell_price:
                # Decrease base amount until price will become lower
                amount_base -= Decimal(10) ** -self.market['base']['precision']
                price = amount_base / amount_quote

            # Limit price by lower bound
            if price < self.lower_bound:
                price = Decimal(self.lower_bound)

            # Prevent too small amounts
            if self.is_too_small_amounts(amount_quote, amount_base):
                self.log.error('Amount for {} order is too small'.format(order_type))
                return

            new_order = self.place_market_sell_order(float(amount_quote), float(price))
            self.beaten_sell_order = self.sell_order_to_beat

        if new_order:
            # Store own order into dict {order_type: id} to perform checks later
            self.orders[order_type] = new_order['id']
        else:
            self.log.error('Failed to place {} order'.format(order_type))

    def place_orders(self):
        """ Place new orders
        """
        place_buy = False
        place_sell = False

        self.get_top_prices()

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
