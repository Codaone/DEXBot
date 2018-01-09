******
Events
******

The websocket endpoint of BitShares has notifications that are
subscribed to and dispatched by ``dexbot``. This uses python's
native ``Events``. The following events are available in your
strategies and depend on the configuration of your bot/strategy:

* ``onOrderMatched``: Called when orders in your market are matched
* ``onOrderPlaced``: Called when a new order in your market is placed
* ``onUpdateCallOrder``: Called if one of the assets in your market is a market-pegged asset and someone updates his call position
* ``onMarketUpdate``: Called whenever something happens in your market (includes matched orders, placed orders and call order updates!)
* ``ontick``: Called when a new block is received
* ``onAccount``: Called when your account's statistics is updated (changes to ``2.6.xxxx`` with ``xxxx`` being your account id number)
* ``error_ontick``: Is called when an error happend when processing ``ontick``
* ``error_onMarketUpdate``: Is called when an error happend when processing ``onMarketUpdate``
* ``error_onAccount``: Is called when an error happend when processing ``onAccount``

Simple Example
--------------

.. code-block:: python

    class Simple(BaseStrategy):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            """ set call backs for events
            """
            self.onOrderMatched += print
            self.onOrderPlaced += print
            self.onUpdateCallOrder += print
            self.onMarketUpdate += print
            self.ontick += print
            self.onAccount += print
