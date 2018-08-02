import math
import time

from dexbot.basestrategy import BaseStrategy, ConfigElement
from dexbot.qt_queue.idle_queue import idle_add

CHECK_MIN_TIME = 300  # five minutes between market checks
BOUNDS_CHECK_TIME = 24*3600  # check bounds/size no more than once a day
WIGGLE = 7  # don't bother redoing orders if bounds/size have less than 7% change


class Strategy(BaseStrategy):
    """ Ataxia strategy, based on Staggered Orders
    """

    @classmethod
    def configure(cls):
        return BaseStrategy.configure() + [
            ConfigElement(
                'size', 'float', 1.0, 'Top Order Size',
                'The amount of the top order', (0.0, None, 4, '')),
            ConfigElement(
                'spread', 'float', 5.0, 'Spread',
                'The percentage difference between buy and sell (Spread)', (0.0, 100.0, 2, '%')),
            ConfigElement(
                'increment', 'float', 1.0, 'Increment',
                'The percentage difference between staggered orders (Increment)', (0.5, 100.0, 2, '%')),
            ConfigElement(
                'upper_bound', 'float', 1.0, 'Upper Bound',
                'The top price in the range', (0.0, None, 4, '')),
            ConfigElement(
                'lower_bound', 'float', 1000.0, 'Lower Bound',
                'The bottom price in the range', (0.0, None, 4, ''))
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.worker_name = kwargs.get('name')
        self.view = kwargs.get('view')
        self.size = self.worker['size']
        self.spread = self.worker['spread'] / 100
        self.increment = self.worker['increment'] / 100
        self.upper_bound = self.worker['upper_bound']
        self.lower_bound = self.worker['lower_bound']
        # Order expiration time, should be high enough
        self.expiration = 60*60*24*365*5
        self.last_check = 0

        if kwargs.get('active', True):
            self.log.info("Initializing {}".format(str(self.__class__.__module__)))

            # Define Callbacks
            self.onMarketUpdate += self.on_market_update_wrapper
            self.onAccount += self.reassess
            self.error_onMarketUpdate = self.error
            self.error_onAccount = self.error

            self.reassess()

    def error(self, *args, **kwargs):
        self.disabled = True

    def save_params(self):
        for param in ['size', 'increment', 'upper_bound', 'lower_bound', 'spread']:
            self['old_'+param] = self.worker[param]

    def check_param_change(self):
        """True if any core param has changed"""
        for param in ['size', 'increment', 'upper_bound', 'lower_bound', 'spread']:
            old_param = 'old_'+param
            if not old_param in self:
                self.save_params()
                return True
            if self[old_param] != self.worker[param]:
                self.save_params()
                return True
        return False

    def check_at_price(self, price):
        """True if no order in self.orderlist at this price"""
        for o in self.orders:
            # "within 0.1% means equal" as slight errors creep in due to rounding
            if abs(o['price']-price)/price < 0.001:
                return False
        return True

    def create_ladder(self, upper_bound, lower_bound):
        """Create the static ladder
        two list of (price, size) tuples, second reverse of first
        size always starts at 1, we multiply later for actual order size
        """
        l = []
        size = 1
        price = upper_bound
        while price > lower_bound:
            l.append((price, size))
            size = size / math.sqrt(1 + self.spread + self.increment)
            price = price * (1 - self.increment)
        return l

    def spread_zone(self, upper_bound, lower_bound):
        ticker = self.market.ticker()
        spread = max(self.spread, 0.001)
        if 'latest' in ticker and ticker['latest'] and float(ticker['latest']) > 0.0:
            centre = float(ticker['latest'])
        else:
            # there's no latest price: we are bootstrapping so use the midpoint of the range
            centre = (upper_bound + lower_bound)/2
        lowest_sell = centre * (1 + (spread/2))
        highest_buy = centre * (1 - (spread/2))
        # don't ever trade against the market
        if 'highestBid' in ticker and ticker['highestBid']:
            bid = float(ticker['highestBid'])
            if bid > 0.0:
                lowest_sell = max(lowest_sell, bid)
        if 'lowestAsk' in ticker and ticker['lowestAsk']:
            ask = float(ticker['lowestAsk'])
            if ask > 0.0:
                highest_buy = min(highest_buy, ask)
        return (highest_buy, lowest_sell)

    def compute_bounds(self):
        """
        In descendants, allow the bounds to be dynamic by some method
        (maybe external price feed, maybe some other market analysis)
        In this implementation, just return the values unmodified
        """
        return (self.upper_bound, self.lower_bound)

    def compute_size(self, ladder):
        """
        In descendants, compute the size (presumably based on the balances)
        allows reinvesting profits
        here, just return unchanged
        """
        return self.size

    def reassess(self, *args, **kwargs):
        if self.check_param_change():
            self.log.info('Purging orderbook')
            # Make sure no orders remain
            self.cancel_all()
            # do the bounds initially
            upper_bound, lower_bound = self.compute_bounds()
            ladder = self.create_ladder(upper_bound, lower_bound)
            size = self.compute_size(ladder)
            self['dynamic_lower_bound'] = lower_bound
            self['dynamic_upper_bound'] = upper_bound
            self['dynamic_size'] = size
            self['last_bounds_check'] = time.time()
        else:
            if time.time() - (self['last_bounds_check'] or 0) > BOUNDS_CHECK_TIME:
                self['last_bounds_check'] = time.time()
                # recompute bounds and size
                new_upper_bound, new_lower_bound = self.compute_bounds()
                new_ladder = self.create_ladder(new_upper_bound, new_lower_bound)
                new_size = self.compute_size(new_ladder)
                # but don't bother redoing the orders unless bounds/size have actually moved significantly
                if (abs(new_upper_bound-(self['dynamic_upper_bound'] or 0))/new_upper_bound > WIGGLE/100.0
                    or abs(new_lower_bound-(self['dynamic_lower_bound'] or 0))/new_lower_bound > WIGGLE/100.0
                        or abs(new_size-(self['dynamic_size'] or 0))/new_size > WIGGLE/100.0):
                    self.log.info('dynamic parameters changed, purging orderbook')
                    self.cancel_all()
                    lower_bound = new_lower_bound
                    self['dynamic_lower_bound'] = lower_bound
                    upper_bound = new_upper_bound
                    self['dynamic_upper_bound'] = upper_bound
                    size = new_size
                    self['dynamic_size'] = size
                    ladder = new_ladder
                else:
                    # change too small: stick to old values
                    lower_bound = self['dynamic_lower_bound']
                    upper_bound = self['dynamic_upper_bound']
                    size = self['dynamic_size']
                    ladder = self.create_ladder(upper_bound, lower_bound)
            else:
                # its not time to recheck, stick to old values
                lower_bound = self['dynamic_lower_bound']
                upper_bound = self['dynamic_upper_bound']
                size = self['dynamic_size']
                ladder = self.create_ladder(upper_bound, lower_bound)
        self.last_check = time.time()
        # prepare up and down ladders
        downladder = ladder
        upladder = ladder.copy()
        upladder.reverse()
        new_order = True
        total_orders = 0
        # now do the orders
        while new_order:
            new_order = False
            self.account.refresh()
            highest_buy, lowest_sell = self.spread_zone(upper_bound, lower_bound)
            self.log.debug("highest_buy = {} lowest_sell = {}".format(highest_buy, lowest_sell))
            # do max one order on each side, then cycle outer loop (i.e. check back
            # with market whether things have shifted)
            for price, ladder_size in downladder:
                if price > lowest_sell:
                    if self.check_at_price(1/price):  # sell orders are inverted
                        # ladder sizes from base of 1, multiple by size toget "real" order size
                        total_amount = size*ladder_size
                        if float(self.balance(self.market['quote'])) > total_amount:
                            new_order = True
                            total_orders += 1
                            self.market_sell(total_amount, price, expiration=self.expiration)
                        else:
                            self.log.warning("I've run out of quote")
                        break
                else:
                    break
            for price, ladder_size in upladder:
                if price < highest_buy:
                    if self.check_at_price(price):
                        total_amount = size*ladder_size
                        if float(self.balance(self.market['base'])) > total_amount*price:
                            new_order = True
                            total_orders += 1
                            self.market_buy(total_amount, price, expiration=self.expiration)
                        else:
                            self.log.warning("I've run out of base")
                        break
                else:
                    break

        if total_orders:
            self.log.info("Done placing orders")
            if self.view:
                self.update_gui_profit()
                self.update_gui_slider()

    def pause(self, *args, **kwargs):
        """ Override pause() method because we don't want to remove orders
        """
        self.log.info("Stopping and leaving orders on the market")

    def on_market_update_wrapper(self, *args, **kwargs):
        """ Handle market update callbacks
        """
        delta = time.time() - self.last_check

        # Only allow to check orders whether minimal time passed
        if delta > CHECK_MIN_TIME:
            self.reassess()

    @classmethod
    def get_required_assets(cls, *args, **kwargs):
        kwargs['active'] = False
        # create a strategy instance that doesn't trade, so
        # we can interrogate it for required assets
        inactive_strategy = cls(*args, **kwargs)
        return None  # for now don't bother

    # GUI updaters
    def update_gui_profit(self):
        pass

    def update_gui_slider(self):
        ticker = self.market.ticker()
        latest_price = ticker.get('latest', {}).get('price', None)
        if not latest_price:
            return

        if self.orders:
            order_ids = [i['id'] for i in self.orders]
        else:
            order_ids = None
        total_balance = self.total_balance(order_ids)
        total = (total_balance['quote'] * latest_price) + total_balance['base']

        if not total:  # Prevent division by zero
            percentage = 50
        else:
            percentage = (total_balance['base'] / total) * 100
        idle_add(self.view.set_worker_slider, self.worker_name, percentage)
        self['slider'] = percentage
