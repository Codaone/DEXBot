# Python imports
# import math

# Project imports
from .base import StrategyBase
from .config_parts.strategy_config import StrategyConfig
from dexbot.qt_queue.idle_queue import idle_add

# Third party imports
# from bitshares.market import Market

STRATEGY_NAME = 'Strategy Template'


class Strategy(StrategyBase):
    """ <strategy_name>

        Replace <strategy_name> with the name of the strategy.

        This is a template strategy which can be used to create custom strategies easier. The base for the strategy is
        ready. It is recommended comment the strategy and functions to help other developers to make changes.

        Adding strategy to GUI
        In dexbot.controller.worker_controller add new strategy inside strategies() as show below:

            strategies['dexbot.strategies.strategy_template'] = {
                'name': '<strategy_name>',
                'form_module': ''
            }

            key: Strategy location in the project
            name: The name that is shown in the GUI for user
            form_module: If there is custom form module created with QTDesigner

        Adding strategy to CLI
        In dexbot.cli_conf add strategy in to the STRATEGIES list

            {'tag': 'strategy_temp',
             'class': 'dexbot.strategies.strategy_template',
             'name': 'Template Strategy'},

        NOTE: Change this comment section to describe the strategy.
    """
    @classmethod
    def configure(cls, return_base_config=True):
        return StrategyConfig.configure(return_base_config)

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        return StrategyConfig.configure_details(include_default_tabs)

    def __init__(self, *args, **kwargs):
        # Initializes StrategyBase class
        super().__init__(*args, **kwargs)

        """ Using self.log.info() you can print text on the GUI to inform user on what is the bot currently doing. This
            is also written in the dexbot.log file.
        """
        self.log.info("Initializing {}...".format(STRATEGY_NAME))

        # Tick counter
        self.counter = 0

        # Define Callbacks
        self.onMarketUpdate += self.maintain_strategy
        self.onAccount += self.maintain_strategy
        self.ontick += self.tick

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error
        """ Define what strategy does on the following events
           - Bitshares account has been modified = self.onAccount
           - Market has been updated = self.onMarketUpdate

           These events are tied to methods which decide how the loop goes, unless the strategy is static, which
           means that it will only do one thing and never do
       """

        # Get view
        self.view = kwargs.get('view')

        """ Worker parameters

            There values are taken from the worker's config file.
            Name of the worker is passed in the **kwargs.
        """
        self.worker_name = kwargs.get('name')

        self.upper_bound = self.worker.get('upper_bound')
        self.lower_bound = self.worker.get('lower_bound')

        """ Strategy variables

            These variables are for the strategy only and should be initialized here if wanted into self's scope.
        """
        self.market_center_price = 0

        if self.view:
            self.update_gui_slider()

        self.log.info("{} initialized.".format(STRATEGY_NAME))

    def maintain_strategy(self):
        """ Strategy main loop

            This method contains the strategy's logic. Keeping this function as simple as possible is recommended.

            Note: All orders are "buy" orders, since they are flipped to be easier to handle. Keep them separated to
            avoid confusion on problems.

            Placing an order to the market has been made simple. Placing a buy order for example requires two values:
            Amount (as QUOTE asset) and price (which is BASE amount divided by QUOTE amount)

            "Placing to buy 100 ASSET_A with price of 10 ASSET_A / ASSET_B" would be place_market_buy_order(100, 10).
            This would then cost 1000 USD to fulfil.

            Further documentation can be found from the function's documentation.

        """
        # Start writing strategy logic from here.
        self.log.info("Starting {}".format(STRATEGY_NAME))

    def check_orders(self, *args, **kwargs):
        """  """
        pass

    def error(self, *args, **kwargs):
        """ Defines what happens when error occurs """
        self.disabled = False

    def pause(self):
        """ Override pause() in StrategyBase """
        pass

    def tick(self, d):
        """ Ticks come in on every block """
        if not (self.counter or 0) % 3:
            self.maintain_strategy()
        self.counter += 1

    def update_gui_slider(self):
        """ Updates GUI slider on the workers list """
        latest_price = self.ticker().get('latest', {}).get('price', None)
        if not latest_price:
            return

        order_ids = None
        orders = self.get_own_orders

        if orders:
            order_ids = [order['id'] for order in orders if 'id' in order]

        total_balance = self.count_asset(order_ids)
        total = (total_balance['quote'] * latest_price) + total_balance['base']

        if not total:  # Prevent division by zero
            percentage = 50
        else:
            percentage = (total_balance['base'] / total) * 100
        idle_add(self.view.set_worker_slider, self.worker_name, percentage)
        self['slider'] = percentage
