from math import fabs
from collections import Counter
from bitshares.amount import Amount
from dexbot.basestrategy import BaseStrategy, ConfigElement
from dexbot.errors import InsufficientFundsError


class Strategy(BaseStrategy):
    """ Walls strategy
    """

    @classmethod
    def configure(cls, return_base_config=True):
        return BaseStrategy.configure(return_base_config) + [
            ConfigElement("spread", "float", 5, "Spread",
                          "The spread between sell and buy as percentage", (0, 100, 2, '%')),
            ConfigElement("threshold", "float", 5, "Threshold",
                          "Percentage the feed has to move before we change orders", (0, 100, 2, '%')),
            ConfigElement("buy", "float", 0, "Buy",
                          "The default amount to buy", (0, None, 8, '')),
            ConfigElement("sell", "float", 0, "Sell",
                          "The default amount to sell", (0, None, 8, '')),
            ConfigElement("blocks", "int", 20, "Block num",
                          "Number of blocks to wait before re-calculating", (0, 10000, ''))
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define Callbacks
        self.onMarketUpdate += self.test
        self.ontick += self.tick
        self.onAccount += self.test

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        # Counter for blocks
        self.counter = Counter()

        # Tests for actions
        self.test_blocks = self.worker.get("test", {}).get("blocks", 0)

    def error(self, *args, **kwargs):
        self.disabled = True
        self.cancelall()
        self.log.info(self.execute())

    def updateorders(self):
        """ Update the orders
        """
        self.log.info("Replacing orders")

        # Canceling orders
        self.cancel_all()

        # Target
        target = self.worker.get("target", {})
        price = self.getprice()

        # prices
        buy_price = price * (1 - target["offsets"]["buy"] / 100)
        sell_price = price * (1 + target["offsets"]["sell"] / 100)

        # Store price in storage for later use
        self["feed_price"] = float(price)

        # Buy Side
        if float(self.balance(self.market["base"])
                 ) < buy_price * target["amount"]["buy"]:
            InsufficientFundsError(
                Amount(
                    target["amount"]["buy"] *
                    float(buy_price),
                    self.market["base"]))
            self["insufficient_buy"] = True
        else:
            self["insufficient_buy"] = False
            self.market.buy(
                buy_price,
                Amount(target["amount"]["buy"], self.market["quote"]),
                account=self.account
            )

        # Sell Side
        if float(self.balance(self.market["quote"])
                 ) < target["amount"]["sell"]:
            InsufficientFundsError(
                Amount(
                    target["amount"]["sell"],
                    self.market["quote"]))
            self["insufficient_sell"] = True
        else:
            self["insufficient_sell"] = False
            self.market.sell(
                sell_price,
                Amount(target["amount"]["sell"], self.market["quote"]),
                account=self.account
            )

        self.log.info(self.execute())

    def getprice(self):
        """ Here we obtain the price for the quote and make sure it has
            a feed price
        """
        target = self.worker.get("target", {})
        if target.get("reference") == "feed":
            assert self.market == self.market.core_quote_market(
            ), "Wrong market for 'feed' reference!"
            ticker = self.market.ticker()
            price = ticker.get("quoteSettlement_price")
            assert abs(price["price"]) != float(
                "inf"), "Check price feed of asset! (%s)" % str(price)
        return price

    def tick(self, d):
        """ ticks come in on every block
        """
        if self.test_blocks:
            if not (self.counter["blocks"] or 0) % self.test_blocks:
                self.test()
            self.counter["blocks"] += 1

    def test(self, *args, **kwargs):
        """ Tests if the orders need updating
        """
        orders = self.orders

        # Test if still 2 orders in the market (the walls)
        if 0 < len(orders) < 2:
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
            fabs(1 - float(self.getprice()) / self["feed_price"]) > self.worker["threshold"] / 100.0
        ):
            self.log.info(
                "Price feed moved by more than the threshold. Updating orders!")
            self.updateorders()
