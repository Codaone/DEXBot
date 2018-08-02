from dexbot.basestrategy import BaseStrategy


class Strategy(BaseStrategy):
    """ Echo strategy
        Strategy that logs all events within the blockchain
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set call backs for events
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
        self.log.info("Order matched: {}".format(i))

    def print_orderPlaced(self, i):
        """ Is called when a new order in the market is placed

            A developer may want to filter those to identify
            own orders.

            :param bitshares.price.Order i: Order details
        """
        self.log.info("Order placed: {}".format(i))

    def print_UpdateCallOrder(self, i):
        """ Is called when a call order for a market pegged asset is updated

            A developer may want to filter those to identify
            own orders.

            :param bitshares.price.CallOrder i: Call order details
        """
        self.log.info("Call update: {}".format(i))

    def print_marketUpdate(self, i):
        """ Is called when Something happens in your market.

            This method is actually called by the backend and is
            dispatched to ``onOrderMatched``, ``onOrderPlaced`` and
            ``onUpdateCallOrder``.

            :param object i: Can be instance of ``FilledOrder``, ``Order``, or ``CallOrder``
        """
        self.log.info("Market update: {}".format(i))

    def print_newBlock(self, i):
        """ Is called when a block is received

            :param str i: The hash of the block

            .. note:: Unfortunately, it is currently not possible to
                      identify the block number for ``i`` alone. If you
                      need to know the most recent block number, you
                      need to use ``bitshares.blockchain.Blockchain``
        """
        self.log.info("New block: {}".format(i))

    def print_accountUpdate(self, i):
        """ This method is called when the worker's account name receives
            any update. This includes anything that changes
            ``2.6.xxxx``, e.g., any operation that affects your account.
        """
        self.log.info("Account: {}".format(i))
