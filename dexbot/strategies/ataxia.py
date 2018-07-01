import math
from datetime import datetime
from datetime import timedelta

from bitshares.amount import Amount

from dexbot.basestrategy import BaseStrategy, ConfigElement
from dexbot.qt_queue.idle_queue import idle_add


class Strategy(BaseStrategy):
    """ Ataxia strategy, based on Staggered Orders
    """

    @classmethod
    def configure(cls):
        return BaseStrategy.configure() + [
            ConfigElement(
                'size', 'float', 1.0,
                'The amount of the top order', (0.0, None)),
            ConfigElement(
                'spread', 'float', 5.0,
                'The percentage difference between buy and sell (Spread)', (0.0, None)),
            ConfigElement(
                'increment', 'float', 1.0,
                'The percentage difference between staggered orders (Increment)', (0.1, None)),
            ConfigElement(
                'upper_bound', 'float', 10.0,
                'The top price in the range', (0.0, None)),
            ConfigElement(
                'lower_bound', 'float', 0.0,
                'The bottom price in the range', (0.0, None))
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log.info("Initializing Ataxia")

        # Define Callbacks
        self.onMarketUpdate += self.on_market_update_wrapper
        self.onAccount += self.reassess
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        self.worker_name = kwargs.get('name')
        self.view = kwargs.get('view')
        self.size = self.worker['size']
        self.spread = self.worker['spread'] / 100
        self.increment = self.worker['increment'] / 100
        self.upper_bound = self.worker['upper_bound']
        self.lower_bound = self.worker['lower_bound']
        # Order expiration time, should be high enough
        self.expiration = 60*60*24*365*5
        self.last_check = datetime.now()

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
            if abs(o['price']-price)/price < 0.001:  # "within 0.1% means equal" as slight errors creep in due to rounding
                return False
        return True

    def ladder(self):
        """Create the static ladder
        two list of (price, size) tuples, second reverse of first
        """
        return Strategy.create_ladder(self.size, self.spread, self.increment, self.upper_bound, self.lower_bound)

    @staticmethod
    def create_ladder(sizep, spread, increment, upper_bound, lower_bound):
        l = []
        size = sizep
        price = upper_bound
        while price > lower_bound:
            l.append((price, size))
            size = size / math.sqrt(1 + spread + increment)
            price = price * (1 - increment)
        rl = l.copy()
        rl.reverse()
        return (l, rl)

    @staticmethod
    def spread_zone(spread, market):
        ticker = market.ticker()
        spread = max(spread, 0.001)
        if 'latest' in ticker and ticker['latest'] and float(ticker['latest']) > 0.0:
            centre = float(ticker['latest'])
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
        else:
            # there's no latest price: ? we are bootstrapping
            if 'highestBid' in ticker and ticker['highestBid'] and float(ticker['highestBid']) > 0.0:
                if 'lowestAsk' in ticker and ticker['lowestAsk'] and float(ticker['lowestAsk']) > 0.0:
                    # there's an orderbook, so take the average
                    centre = (float(ticker['highestBid']) + float(ticker['lowestAsk']))/2
                    lowest_sell = centre * (1 + (spread/2))
                    highest_buy = centre * (1 - (spread/2))
                else:
                    lowest_sell = float(ticker['highestBid'])
                    highest_buy = lowest_sell * (1 + spread)
            elif 'lowestAsk' in ticker and ticker['lowestAsk'] and float(ticker['lowestAsk']) > 0.0:
                highest_buy = float(ticker['lowestAsk'])
                lowest_buy = highest_buy * (1 - spread)
            else:
                # market has no latest, no bids and no asks
                self.log.critical("Completely empty market: I don't know what to do")
                raise Exception()
        return (highest_buy, lowest_sell)

    def reassess(self, *args, **kwargs):
        if self.check_param_change():
            self.log.info('Purging orderbook')
            # Make sure no orders remain
            self.cancel_all()

        self.last_check = datetime.now()
        downladder, upladder = self.ladder()
        new_order = True
        total_orders = 0
        while new_order:
            new_order = False
            self.account.refresh()
            highest_buy, lowest_sell = Strategy.spread_zone(self.spread, self.market)
            self.log.debug("highest_buy = {} lowest_sell = {}".format(highest_buy, lowest_sell))
            # do max one order on each side, then cycle outer loop (i.e. check back
            # with market whether things have shifted)
            for price, size in downladder:
                if price > lowest_sell:
                    if self.check_at_price(1/price):  # sell orders are inverted
                        if float(self.balance(self.market['quote'])) > size:
                            new_order = True
                            total_orders += 1
                            self.market_sell(size, price, expiration=self.expiration)
                        else:
                            self.log.critical("I've run out of quote")
                        break
                else:
                    break
            for price, size in upladder:
                if price < highest_buy:
                    if self.check_at_price(price):
                        if float(self.balance(self.market['base'])) > size*price:
                            new_order = True
                            total_orders += 1
                            self.market_buy(size, price, expiration=self.expiration)
                        else:
                            self.log.critical("I've run out of base")
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
        delta = datetime.now() - self.last_check

        # Only allow to check orders whether minimal time passed
        if delta > timedelta(seconds=300):
            self.reassess()

    @staticmethod
    def get_required_assets(market, amount, spread, increment, lower_bound, upper_bound):
        return None  # TODO

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
