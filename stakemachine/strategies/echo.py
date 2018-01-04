from stakemachine.basestrategy import BaseStrategy
import logging
log = logging.getLogger(__name__)


class Echo(BaseStrategy):

    configure = [] # we don't need extra config
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        """ set call backs for events
        """
        self.onOrderMatched += self.print_orderMatched
        self.onOrderPlaced += self.print_orderPlaced
        self.onUpdateCallOrder += self.print_UpdateCallOrder
        self.onMarketUpdate += self.print_marketUpdate
        self.ontick += self.print_newBlock
        self.onAccount += self.print_accountUpdate
        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

    def error(self, *args, **kwargs):
        """ What to do on an error
        """
        # Cancel all future execution
        self.disabled = True

    def print_orderMatched(self, i):
        """ Is called when an order in the market is matched

            A developer may want to filter those to identify
            own orders.

            :param bitshares.price.FilledOrder i: Filled order details
        """
        print("order matched: %s" % i)

    def print_orderPlaced(self, i):
        """ Is called when a new order in the market is placed

            A developer may want to filter those to identify
            own orders.

            :param bitshares.price.Order i: Order details
        """
        print("order placed:  %s" % i)

    def print_UpdateCallOrder(self, i):
        """ Is called when a call order for a market pegged asset is updated

            A developer may want to filter those to identify
            own orders.

            :param bitshares.price.CallOrder i: Call order details
        """
        print("call update:   %s" % i)

    def print_marketUpdate(self, i):
        """ Is called when Something happens in your market.

            This method is actually called by the backend and is
            dispatched to ``onOrderMatched``, ``onOrderPlaced`` and
            ``onUpdateCallOrder``.

            :param object i: Can be instance of ``FilledOrder``, ``Order``, or ``CallOrder``
        """
        print("marketupdate:  %s" % i)

    def print_newBlock(self, i):
        """ Is called when a block is received

            :param str i: The hash of the block

            .. note:: Unfortunately, it is currently not possible to
                      identify the block number for ``i`` alone. If you
                      need to know the most recent block number, you
                      need to use ``bitshares.blockchain.Blockchain``
        """
        print("new block:     %s" % i)
        # raise ValueError("Testing disabling")

    def print_accountUpdate(self, i):
        """ This method is called when the bot's account name receives
            any update. This includes anything that changes
            ``2.6.xxxx``, e.g., any operation that affects your account.
        """
        print("account:       %s" % i)
