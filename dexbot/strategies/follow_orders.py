from math import fabs
from pprint import pprint
from collections import Counter
from bitshares.amount import Amount
from bitshares.price import Price, Order, FilledOrder
from dexbot.basestrategy import BaseStrategy, ConfigElement
import time


class Strategy(BaseStrategy):

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
                "max",
                "float",
                100.0,
                "bot will not trade if price above this",
                (0.0,
                 None)),
            ConfigElement(
                "min",
                "float",
                100.0,
                "bot will not trade if price below this",
                (0.0,
                 None)),
            ConfigElement(
                "start",
                "float",
                100.0,
                "Starting price, as percentage of bid/ask spread",
                (0.0,
                 100.0)),
            ConfigElement(
                "reset",
                "bool",
                False,
                "bot will always reset orders on start",
                (0.0,
                 None)),
            ConfigElement(
                "staggers",
                "int",
                1,
                "Number of additional staggered orders to place",
                (1,
                 100)),
            ConfigElement(
                "staggerspread",
                "float",
                5,
                "Percentage difference between staggered orders",
                (0,
                 100)),
            ConfigElement(
                'bias',
                'float',
                0,
                "Percentage of bias higher or lower (negative is lower) from the baseprice",
                (-100,100))
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define Callbacks
        self.onMarketUpdate += self.onmarket
        if self.bot.get("reset", False):
            self.cancel_all()
        self.reassess()

    def updateorders(self, newprice):
        """ Update the orders
        """
        self.log.info("Replacing orders. Baseprice is %f" % newprice)
        step1 = self.bot['spread'] / 200.0 * newprice
        step2 = self.bot['staggerspread'] / 100.0 * newprice
        # apply bias
        newprice = (100.0 + self.bot['bias']) / 100.0 * newprice
        self['price'] = newprice
        # Canceling orders
        self.cancel_all()
        # record balances (on forks with have this feature)
        if hasattr(self, "record_balances"):
            self.record_balances(newprice)

        myorders = {}

        if newprice < self.bot["min"]:
            self.disabled = True
            self.log.critical(
                "Price {} is below minimum {}".format(
                    newprice, self.bot["min"]))
            return False
        if newprice > self.bot["max"]:
            self.disabled = True
            self.log.critical(
                "Price {} is above maximum {}".format(
                    newprice, self.bot["max"]))
            return False

        sell_wall = self.balance(self.market['quote']) * self.bot['wall_percent'] / 100.0
        sell_price = newprice + step1
        for i in range(0, self.bot['staggers']):
            self.log.info("SELL {amt} at {price:.4g} {base}/{quote} (= {inv_price:.4g} {quote}/{base})".format(
                amt=repr(sell_wall),
                price=sell_price,
                inv_price=1 / sell_price,
                quote=self.market['quote']['symbol'],
                base=self.market['base']['symbol']))
            ret = self.market.sell(
                sell_price,
                sell_wall,
                account=self.account,
                returnOrderId="head"
            )
            self.log.debug("SELL order done")
            myorders[ret['orderid']] = sell_price
            sell_price += step2

        buy_wall = Amount(float(self.balance(self.market['base']) * self.bot['wall_percent'] / 100.00 / newprice),self.market['quote'])
        buy_price = newprice - step1
        for i in range(0, self.bot['staggers']):
            self.log.info("BUY {amt} at {price:.4g} {base}/{quote} (= {inv_price:.4g} {quote}/{base})".format(
                amt=repr(buy_wall),
                price=buy_price,
                inv_price=1 / buy_price,
                quote=self.market['quote']['symbol'],
                base=self.market['base']['symbol']))
            ret = self.market.buy(
                buy_price,
                buy_wall,
                account=self.account,
                returnOrderId="head",
            )
            self.log.debug("BUY order done")
            myorders[ret['orderid']] = buy_price
            buy_price -= step2
        self['myorders'] = myorders
        # ret = self.execute() this doesn't seem to work reliably
        # self.safe_dissect(ret,"execute")

        return True
    
    def onmarket(self, data):
        if isinstance(
                data, FilledOrder) and data['account_id'] == self.account['id']:
            self.log.debug(
                "data['quote']['asset'] = {} self.market['quote'] = {}".format(
                    data['quote']['asset'],
                    self.market['quote']))
            if data['quote']['asset'] == self.market['quote']:
                self.log.debug("Quote = quote")
            if repr(data['quote']['asset']['id']) == repr(
                    self.market['quote']['id']):
                self.log.debug("quote['id'] = quote['id']")
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
                self.reassess(None)  # check if order has been filled while we were busy entering orders
        else:
            self.log.debug("no action")


    def recalculate_price(self, market_data=None):
        """Recalculate the base price according to the bot's rules
        (descendants encouraged to override)
        Returning None indicates no new orders
        """
        still_open = set(i['id'] for i in self.account.openorders)
        self.log.debug("still_open: {}".format(still_open))
        if len(still_open) == 0:
            self.log.info("no open orders, recalculating the startprice")
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
            return bid + ((ask - bid) * self.bot['start'] / 100.0)
        missing = set(self['myorders'].keys()) - still_open
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
