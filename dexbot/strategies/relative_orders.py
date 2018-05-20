from dexbot.basestrategy import BaseStrategy
from dexbot.queue.idle_queue import idle_add

from bitshares.amount import Amount


class Strategy(BaseStrategy):
    """ Relative Orders strategy
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define Callbacks
        self.onMarketUpdate += self.check_orders
        self.onAccount += self.check_orders

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        self.is_center_price_dynamic = self.worker["center_price_dynamic"]
        if self.is_center_price_dynamic:
            self.center_price = None
        else:
            self.center_price = self.worker["center_price"]

        self.is_relative_order_size = self.worker['amount_relative']
        self.order_size = float(self.worker['amount'])

        self.buy_price = None
        self.sell_price = None

        self.initial_balance = self['initial_balance'] or 0
        self.worker_name = kwargs.get('name')
        self.view = kwargs.get('view')

        self.check_orders()

    @property
    def amount_quote(self):
        """ Get quote amount, calculate if order size is relative
        """
        if self.is_relative_order_size:
            quote_balance = float(self.balance(self.market["quote"]))
            return quote_balance * (self.order_size / 100)
        else:
            return self.order_size

    @property
    def amount_base(self):
        """ Get base amount, calculate if order size is relative
        """
        if self.is_relative_order_size:
            base_balance = float(self.balance(self.market["base"]))
            # amount = % of balance / buy_price = amount combined with calculated price to give % of balance
            return base_balance * (self.order_size / 100) / self.buy_price
        else:
            return self.order_size

    def calculate_order_prices(self):
        if self.is_center_price_dynamic:
            self.center_price = self.calculate_relative_center_price(self.worker['spread'], self['order_ids'])

        self.buy_price = self.center_price / (1 + (self.worker["spread"] / 2) / 100)
        self.sell_price = self.center_price * (1 + (self.worker["spread"] / 2) / 100)

    def error(self, *args, **kwargs):
        self.cancel_all()
        self.disabled = True
        self.log.info(self.execute())

    def update_orders(self):
        self.log.info('Change detected, updating orders')

        # Recalculate buy and sell order prices
        self.calculate_order_prices()

        # Cancel the orders before redoing them
        self.cancel_all()

        # Mark the orders empty
        self['buy_order'] = {}
        self['sell_order'] = {}

        order_ids = []

        amount_base = self.amount_base
        amount_quote = self.amount_quote

        # Buy Side
        if float(self.balance(self.market["base"])) < self.buy_price * amount_base:
            self.log.critical(
                'Insufficient buy balance, needed {} {}'.format(self.buy_price * amount_base,
                                                                self.market['base']['symbol'])
            )
            self.disabled = True
        else:
            buy_order = self.market_buy(amount_base, self.buy_price)
            if buy_order:
                self['buy_order'] = buy_order
                order_ids.append(buy_order['id'])

        # Sell Side
        if float(self.balance(self.market["quote"])) < amount_quote:
            self.log.critical(
                "Insufficient sell balance, needed {} {}".format(amount_quote, self.market['quote']['symbol'])
            )
            self.disabled = True
        else:
            sell_order = self.market_sell(amount_quote, self.sell_price)
            if sell_order:
                self['sell_order'] = sell_order
                order_ids.append(sell_order['id'])

        self['order_ids'] = order_ids

        # Some orders weren't successfully created, redo them
        if len(order_ids) < 2 and not self.disabled:
            self.update_orders()

    def check_orders(self, *args, **kwargs):
        """ Tests if the orders need updating
        """
        stored_sell_order = self['sell_order']
        stored_buy_order = self['buy_order']
        current_sell_order = self.get_updated_order(stored_sell_order)
        current_buy_order = self.get_updated_order(stored_buy_order)

        if not current_sell_order or not current_buy_order:
            # Either buy or sell order is missing, update both orders
            self.update_orders()

        if self.view:
            self.update_gui_profit()
            self.update_gui_slider()

    # GUI updaters
    def update_gui_profit(self):
        # Fixme: profit calculation doesn't work this way, figure out a better way to do this.
        if self.initial_balance:
            profit = round((self.orders_balance(None) - self.initial_balance) / self.initial_balance, 3)
        else:
            profit = 0
        idle_add(self.view.set_worker_profit, self.worker_name, float(profit))
        self['profit'] = profit

    def update_gui_slider(self):
        ticker = self.market.ticker()
        latest_price = ticker.get('latest').get('price')
        total_balance = self.total_balance(self['order_ids'])
        total = (total_balance['quote'] * latest_price) + total_balance['base']

        if not total:  # Prevent division by zero
            percentage = 50
        else:
            percentage = (total_balance['base'] / total) * 100
        idle_add(self.view.set_worker_slider, self.worker_name, percentage)
        self['slider'] = percentage
