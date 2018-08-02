import math

from dexbot.basestrategy import BaseStrategy, ConfigElement
from dexbot.qt_queue.idle_queue import idle_add


class Strategy(BaseStrategy):
    """ Relative Orders strategy
    """

    @classmethod
    def configure(cls, return_base_config=True):
        return BaseStrategy.configure(return_base_config) + [
            ConfigElement('relative_order_size', 'bool', False, 'Relative order size',
                          'Amount is expressed as a percentage of the account balance of quote/base asset', None),
            ConfigElement('amount', 'float', 1, 'Amount',
                          'Fixed order size, expressed in quote asset, unless "relative order size" selected', (0, None, 8, '')),
            ConfigElement('center_price_dynamic', 'bool', True, 'Dynamic center price',
                          'Always calculate the middle from the closest market orders', None),
            ConfigElement('center_price', 'float', 0, 'Center price',
                          'Fixed center price expressed in base asset: base/quote', (0, None, 8, '%')),
            ConfigElement('center_price_offset', 'bool', False, 'Center price offset based on asset balances',
                          'Automatically adjust orders up or down based on the imbalance of your assets', None),
            ConfigElement('spread', 'float', 5, 'Spread',
                          'The percentage difference between buy and sell', (0, 100, 2, '%')),
            ConfigElement('manual_offset', 'float', 0, 'Manual center price offset',
                          "Manually adjust orders up or down. "
                          "Works independently of other offsets and doesn't override them", (-50, 100, 2, '%'))
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log.info("Initializing Relative Orders")

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

        self.is_relative_order_size = self.worker.get('relative_order_size', False)
        self.is_asset_offset = self.worker.get('center_price_offset', False)
        self.manual_offset = self.worker.get('manual_offset', 0) / 100
        self.order_size = float(self.worker.get('amount', 1))
        self.spread = self.worker.get('spread') / 100

        self.buy_price = None
        self.sell_price = None

        self.initial_balance = self['initial_balance'] or 0
        self.worker_name = kwargs.get('name')
        self.view = kwargs.get('view')
        self.check_orders()

    def error(self, *args, **kwargs):
        self.cancel_all()
        self.disabled = True

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
            self.center_price = self.calculate_center_price(
                None,
                self.is_asset_offset,
                self.spread,
                self['order_ids'],
                self.manual_offset
            )
        else:
            self.center_price = self.calculate_center_price(
                self.center_price,
                self.is_asset_offset,
                self.spread,
                self['order_ids'],
                self.manual_offset
            )

        self.buy_price = self.center_price / math.sqrt(1 + self.spread)
        self.sell_price = self.center_price * math.sqrt(1 + self.spread)

    def update_orders(self):
        self.log.info('Change detected, updating orders')

        # Recalculate buy and sell order prices
        self.calculate_order_prices()

        # Cancel the orders before redoing them
        self.cancel_all()
        self.clear_orders()

        order_ids = []

        amount_base = self.amount_base
        amount_quote = self.amount_quote

        # Buy Side
        buy_order = self.market_buy(amount_base, self.buy_price, True)
        if buy_order:
            self.save_order(buy_order)
            order_ids.append(buy_order['id'])

        # Sell Side
        sell_order = self.market_sell(amount_quote, self.sell_price, True)
        if sell_order:
            self.save_order(sell_order)
            order_ids.append(sell_order['id'])

        self['order_ids'] = order_ids

        self.log.info("Done placing orders")

        # Some orders weren't successfully created, redo them
        if len(order_ids) < 2 and not self.disabled:
            self.update_orders()

    def check_orders(self, *args, **kwargs):
        """ Tests if the orders need updating
        """
        orders = self.fetch_orders()

        if not orders:
            self.update_orders()
        else:
            orders_changed = False

            # Loop trough the orders and look for changes
            for order_id, order in orders.items():
                current_order = self.get_order(order_id)

                if not current_order:
                    orders_changed = True
                    self.write_order_log(self.worker_name, order)

            if orders_changed:
                self.update_orders()
            else:
                self.log.info("Orders correct on market")

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
        latest_price = ticker.get('latest', {}).get('price', None)
        if not latest_price:
            return

        order_ids = None
        orders = self.fetch_orders()

        if orders:
            order_ids = orders.keys()

        total_balance = self.total_balance(order_ids)
        total = (total_balance['quote'] * latest_price) + total_balance['base']

        if not total:  # Prevent division by zero
            percentage = 50
        else:
            percentage = (total_balance['base'] / total) * 100
        idle_add(self.view.set_worker_slider, self.worker_name, percentage)
        self['slider'] = percentage
