from math import fabs
from pprint import pprint
from collections import Counter, namedtuple
import time

from bitshares.amount import Amount
from bitshares.price import Price, Order, FilledOrder

from dexbot.basestrategy import BaseStrategy, ConfigElement

MyOrder = namedtuple("MyOrder", "quote quote_sym base base_sym")


class Strategy(BaseStrategy):
    """The Mirror Strategy
    """

    @classmethod
    def configure(cls):
        return BaseStrategy.configure() + [
            ConfigElement(
                "spread",
                "float",
                5,
                "Percentage difference between buy and sell",
                (0,
                 100)),
            ConfigElement(
                "wall_percent",
                "float",
                0,
                "the default amount to buy/sell, as a percentage of the balance",
                (0,
                 100)),
            ConfigElement(
                "diff",
                "float",
                100.0,
                "minimum difference from a pre-existing bid/ask price",
                (0.0,
                 None))
        ]

    def safe_dissect(self, thing, name):
        try:
            self.log.debug(
                "%s() returned type: %r repr: %r dict: %r" %
                (name, type(thing), repr(thing), dict(thing)))
        except BaseException:
            self.log.debug(
                "%s() returned type: %r repr: %r" %
                (name, type(thing), repr(thing)))

    def convert_orders(self, orders):
        """Convert a list of orders to a namedtuple
        (so can be compared)"""
        return [MyOrder(o['quote']['amount'], o['quote']['asset']['symbol'], o['base']['amount'], o['base']['asset']['symbol']) for o in orders]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define Callbacks
        self.onMarketUpdate += self.onmarket
        self.ontick += self.onblock
        self.reassess()

    def updateorders(self, newprice):
        """ Update the orders
        """
        self.log.info("Replacing orders. Baseprice is %f" % newprice)
        step1 = self.worker['spread'] / 200.0 * newprice
        self['price'] = newprice
        # Canceling orders
        self.cancel_all()
        # record balances
        if hasattr(self, "record_balances"):
            self.record_balances(newprice)

        market_orders = self.market.orderbook()
        bids = market_orders['bids']
        asks = market_orders['asks']

        my_orders = self.convert_orders(self.market.accountopenorders(account=self.account))

        sell_wall = self.balance(
            self.market['quote']) * self.worker['wall_percent'] / 100.0
        sell_price = newprice + step1

        bids = self.convert_orders(bids)
        for o in my_orders:
            try:
                bids.remove(o)
            except ValueError:
                pass

        bid_price = (bids[0].quote / bids[0].base) * ((100 + self.worker['diff'])/100.0)

        sell_price = max(bid_price, sell_price)

        buy_wall = Amount(
            float(
                self.balance(
                    self.market['base']) *
                self.worker['wall_percent'] /
                100.00 /
                newprice),
            self.market['quote'])
        buy_price = newprice - step1

        asks = self.convert_orders(asks)
        for o in my_orders:
            try:
                asks.remove(o)
            except ValueError:
                pass

        ask_price = (asks[0].base / asks[0].quote) * ((100 - self.worker['diff'])/100.0)

        buy_price = min(ask_price, buy_price)

        return True

    def onmarket(self, data):
        if isinstance(
                data, FilledOrder) and data['account_id'] == self.account['id']:
            self.log.info("I sold {} for {}".format(data['quote'], data['base']))
            self.reassess(data)

    def reassess(self, market_data=None):
        # sadly no smart way to match a FilledOrder to an existing order
        # even price-matching won't work as we can buy at a better price than we asked for
        # so look at what's missing
        self.log.debug("reassessing...")
        self.account.refresh()
        newprice = self.recalculate_price(market_data)
        if newprice is not None:
            if self.updateorders(newprice):
                time.sleep(1)
                # check if order has been filled while we were busy entering
                # orders
                self.reassess(None)
        else:
            self.log.info("Orders unchanged")

    def recalculate_price(self, market_data=None):
        """Recalculate the base price according to the worker's rules
        (descendants encouraged to override)
        Returning None indicates no new orders
        """
        still_open = set(i['id'] for i in self.account.openorders)
        self.log.debug("still_open: {}".format(still_open))
        recalc = False
        if len(still_open) == 0:
            self.log.debug("no open orders, recalculating the startprice")
            recalc = True
        elif 'myorders' not in self:
            self.log.error("we have open orders but no record, weird: recalculating startprice")
            recalc = True
        if recalc:
            t = self.market.ticker()
            if t['highestBid'] is None:
                self.log.critical("no bid price available")
                self.disabled = True
                return None
            if t['lowestAsk'] is None or t['lowestAsk'] == 0.0:
                self.log.critical("no ask price available")
                self.disabled = True
                return None
            bid = float(t['highestBid'])
            ask = float(t['lowestAsk'])
            return bid + ((ask - bid) * self.worker['start'] / 100.0)
        self.log.debug("myorders: {}".format(self['myorders']))
        missing = set(self['myorders'].keys()) - still_open
        self.log.debug("missing: {}".format(missing))
        if missing:
            found_price = 0.0
            highest_diff = 0.0
            for i in missing:
                diff = fabs(self['price'] - self['myorders'][i])
                if diff > highest_diff:
                    found_price = self['myorders'][i]
                    highest_diff = diff
            return found_price
        else:
            return None
