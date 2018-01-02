*************
Configuration
*************

The configuration of ``stakemachine`` happens through a YAML formated
file and takes the following form:

.. code-block:: yaml

    # The BitShares endpoint to talk to
    node: "wss://node.testnet.bitshares.eu"

    # List of bots
    bots:

        # Name of the bot. This is mostly for logging and internal
        # use to distinguish different bots
        NAME_OF_BOT:

            # Python module to look for the strategy (can be custom)
	    # stakemachine will search in ~/bots as well as standard dirs 
	    module: "stakemachine.strategies.echo"

            # The bot class in that module to use
            bot: Echo

            # The market to subscribe to
            market: GOLD:TEST

            # The account to use for this bot
            account: xeroc

            # Custom bot configuration
            foo: bar

Usig the configuration in custom strategies
-------------------------------------------

The bot's configuration is available to in each strategy as dictionary
in ``self.bot``. The whole configuration is avaialable in
``self.config``. The name of your bot can be found in ``self.name``.
