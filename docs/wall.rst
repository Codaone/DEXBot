*************
Wall Strategy
*************

This strategy simply places a buy and a sell wall into a specific market
using a specified account.

Example Configuration
---------------------
.. code-block:: yaml

    # BitShares end point
    node: "wss://node.bitshares.eu"

    # List of Bots
    bots:

            # Only a single Walls Bot
            Walls:

                 # The Walls strategy module and class
                 module: dexbot.strategies.walls
                 bot: Walls

                 # The market to serve
                 market: HERO:BTS

                 # The account to sue
                 account: hero-market-maker

                 # We shall bundle operations into a single transaction
                 bundle: True

                 # Test your conditions every x blocks
                 test:
                         blocks: 10

                 # Where the walls should be
                 target:

                         # They relate to the price feed
                         reference: feed

                         # There should be an offset
                         offsets:
                             buy: 2.5
                             sell: 2.5

                         # We'd like to use x amount of quote (here: HERO)
                         # in the walls
                         amount:
                             buy: 5.0
                             sell: 5.0

                 # When the price moves by more than 2%, update the walls
                 threshold: 2


Source Code
-----------
.. literalinclude:: ../dexbot/strategies/walls.py
   :language: python
   :linenos:
