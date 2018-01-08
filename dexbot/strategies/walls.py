from math import fabs
from pprint import pprint
from collections import Counter
from bitshares.amount import Amount
from dexbot.basestrategy import BaseStrategy, ConfigElement
from dexbot.errors import InsufficientFundsError

class Walls(BaseStrategy):

    @classmethod
    def configure(cls):
        return BaseStrategy.configure()+[
            ConfigElement("spread","int",5,"the spread between sell and buy as percentage",(0,100)),
            ConfigElement("threshold","int",5,"percentage the feed has to move before we change orders",(0,100)),
            ConfigElement("buy","float",0.0,"the default amount to buy",(0.0,None)),
            ConfigElement("sell","float",0.0,"the default amount to sell",(0.0,None)),
            ConfigElement("blocks","int",20,"number of blocks to wait before re-calculating",(0,10000)),
            ConfigElement("dry_run","bool",False,"Dry Run Mode\nIf Yes the bot won't buy or sell anything, just log what it would do.\nIf No, the bot will buy and sell for real.",None)
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define Callbacks
        self.onMarketUpdate += self.onmarket
        self.ontick += self.tick
        self.onAccount += self.test

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        # Counter for blocks
        self.counter = Counter()

        # Tests for actions
        self.test_blocks = self.bot.get("blocks", 0)

    def error(self, *args, **kwargs):
        self.disabled = True
        self.cancelall()
        self.log.info(repr(self.execute()))

    def updateorders(self):
        """ Update the orders
        """
        self.log.info("Replacing orders")

        # Canceling orders
        self.cancelall()

        price = self.getprice()

        # prices
        buy_price = price * (1 - self.bot['spread'] / 100)
        sell_price = price * (1 + self.bot['spread'] / 100)

        # Store price in storage for later use
        self["feed_price"] = float(price)

        # Buy Side
        if float(self.balance(self.market["base"])) < buy_price * self.bot["buy"]:
            raise InsufficientFundsError(Amount(self.bot["buy"] * float(buy_price), self.market["base"]))
            self["insufficient_buy"] = True
        else:
            self["insufficient_buy"] = False
            amt = Amount(self.bot["buy"], self.market["quote"])
            if self.bot.get("dry_run",False):
                p1=str(buy_price)
                buy_price.invert()
                p2=str(buy_price)
                self.log.info("BUY {amt} at {price} = {inv_price}".format(
                    amt=repr(amt),
                    price=p1,
                    inv_price = p2))
            else:
                ret = self.market.buy(
                    buy_price,
                    amt,
                    account=self.account
                )

        # Sell Side
        if float(self.balance(self.market["quote"])) < self.bot["sell"]:
            raise InsufficientFundsError(Amount(self.bot["sell"], self.market["quote"]))
            self["insufficient_sell"] = True
        else:
            self["insufficient_sell"] = False
            amt = Amount(self.bot["sell"], self.market["quote"])
            if self.bot.get("dry_run",False):
                p1=str(sell_price)
                sell_price.invert()
                p2=str(sell_price)
                self.log.info("SELL {amt} {price} = {inv_price}".format(
                    amt=repr(amt),
                    price = p1,
                    inv_price = p2))
            else:
                ret = self.market.sell(
                    sell_price,
                    amt,
                    account=self.account
                )

        self.log.info(repr(self.execute()))

    def getprice(self):
        """ Here we obtain the price for the quote and make sure it has
            a feed price
        """
        #if self.bot.get("reference") == "feed": # what does this mean? what other options did xeroc have in mind?
        assert self.market == self.market.core_quote_market(), "Wrong market for 'feed' reference!"
        ticker = self.market.ticker()
        price = ticker.get("quoteSettlement_price")
        assert abs(price["price"]) != float("inf"), "Check price feed of asset! (%s)" % str(price)
        return price

    def tick(self, d):
        """ ticks come in on every block
        """
        self.log.info("tick self.counter = %r self.test_blocks = %r" % (dict(self.counter),self.test_blocks))
        if self.test_blocks:
            if not (self.counter["blocks"] or 0) % self.test_blocks:
                self.test()
            self.counter["blocks"] += 1

    def test(self, *args, **kwargs):
        """ Tests if the orders need updating
        """
        orders = self.orders

        # Test if still 2 orders in the market (the walls)
        if len(orders) < 2 and len(orders) > 0:
            if (
                not self["insufficient_buy"] and
                not self["insufficient_sell"]
            ):
                self.log.info("No 2 orders available. Updating orders!")
                self.updateorders()
        elif len(orders) == 0:
            self.updateorders()

        # Test if price feed has moved more than the threshold
        if (
            self["feed_price"] and
            fabs(1 - float(self.getprice()) / self["feed_price"]) > self.bot.get("threshold",5) / 100.0
        ):
            self.log.info("Price feed moved by more than the threshold. Updating orders!")
            self.updateorders()

    def onmarket(self, data):
        self.log.info("Market event type = %s repr = %r dict = %s" % (type(data),repr(data),dict(data)))
