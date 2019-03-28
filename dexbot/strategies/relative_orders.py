import math
from datetime import datetime, timedelta

from .base import StrategyBase
from .config_parts.relative_config import RelativeConfig


class Strategy(StrategyBase):
    """ Relative Orders strategy
    """

    @classmethod
    def configure(cls, return_base_config=True):
        return RelativeConfig.configure(return_base_config)

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        return RelativeConfig.configure_details(include_default_tabs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log.info("Initializing Relative Orders")

        # Tick counter
        self.counter = 0

        # Define Callbacks
        self.ontick += self.tick
        self.onMarketUpdate += self.check_orders
        self.onAccount += self.check_orders

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        # Market status
        self.empty_market = False

        # Get market center price from Bitshares
        self.market_center_price = self.get_market_center_price(suppress_errors=True)

        # Set external price source, defaults to False if not found
        self.external_feed = self.worker.get('external_feed', False)
        self.external_price_source = self.worker.get('external_price_source', 'gecko')

        if self.external_feed:
            # Get external center price from given source
            self.external_market_center_price = self.get_external_market_center_price(self.external_price_source)

        if not self.market_center_price:
            # Bitshares has no center price making it an empty market or one that has only one sided orders
            self.empty_market = True

        # Worker parameters
        self.is_center_price_dynamic = self.worker['center_price_dynamic']

        if self.is_center_price_dynamic:
            self.center_price = None
            self.center_price_depth = self.worker.get('center_price_depth', 0)
        else:
            # Use manually set center price
            self.center_price = self.worker["center_price"]

        self.is_relative_order_size = self.worker.get('relative_order_size', False)
        self.is_asset_offset = self.worker.get('center_price_offset', False)
        self.manual_offset = self.worker.get('manual_offset', 0) / 100
        self.order_size = float(self.worker.get('amount', 1))

        # Spread options
        self.spread = self.worker.get('spread') / 100
        self.dynamic_spread = self.worker.get('dynamic_spread', False)
        self.market_depth_amount = self.worker.get('market_depth_amount', 0)
        self.dynamic_spread_factor = self.worker.get('dynamic_spread_factor', 1) / 100

        self.is_reset_on_partial_fill = self.worker.get('reset_on_partial_fill', True)
        self.partial_fill_threshold = self.worker.get('partial_fill_threshold', 30) / 100
        self.is_reset_on_price_change = self.worker.get('reset_on_price_change', False)
        self.price_change_threshold = self.worker.get('price_change_threshold', 2) / 100
        self.is_custom_expiration = self.worker.get('custom_expiration', False)

        if self.is_custom_expiration:
            self.expiration = self.worker.get('expiration_time', self.expiration)

        self.last_check = datetime.now()
        self.min_check_interval = 8

        self.buy_price = None
        self.sell_price = None
        self.initializing = True

        self.initial_balance = self['initial_balance'] or 0
        self.worker_name = kwargs.get('name')
        self.view = kwargs.get('view')

        # Check for conflicting settings
        if self.is_reset_on_price_change and not self.is_center_price_dynamic:
            self.log.error('"Reset orders on center price change" requires "Dynamic Center Price"')
            self.disabled = True
            return

        # Check if market has center price when using dynamic center price
        if not self.external_feed and self.empty_market and (self.is_center_price_dynamic or self.dynamic_spread):
            self.log.info('Market is empty and using dynamic market parameters. Waiting for market change...')
            return

        # Check old orders from previous run (from force-interruption) only whether we are not using
        # "Reset orders on center price change" option
        if self.is_reset_on_price_change:
            self.log.info('"Reset orders on center price change" is active, placing fresh orders')
            self.update_orders()
        else:
            self.check_orders()

    def error(self, *args, **kwargs):
        self.disabled = True

    def tick(self, d):
        """ Ticks come in on every block. We need to periodically check orders because cancelled orders
            do not triggers a market_update event
        """
        if (self.is_reset_on_price_change and not
                self.counter % 8):
            self.log.debug('Checking orders by tick threshold')
            self.check_orders()
        self.counter += 1

    @property
    def amount_to_sell(self):
        """ Get quote amount, calculate if order size is relative
        """
        amount = self.order_size
        if self.is_relative_order_size:
            quote_balance = float(self.balance(self.market["quote"]))
            amount = quote_balance * (self.order_size / 100)

        # Sell / receive amount should match x2 of minimal possible fraction of asset
        if (amount < 2 * 10 ** -self.market['quote']['precision'] or
                amount * self.sell_price < 2 * 10 ** -self.market['base']['precision']):
            amount = 0
        return amount

    @property
    def amount_to_buy(self):
        """ Get base amount, calculate if order size is relative
        """
        amount = self.order_size
        if self.is_relative_order_size:
            base_balance = float(self.balance(self.market["base"]))
            # amount = % of balance / buy_price = amount combined with calculated price to give % of balance
            amount = base_balance * (self.order_size / 100) / self.buy_price

        # Sell / receive amount should match x2 of minimal possible fraction of asset
        if (amount < 2 * 10 ** -self.market['quote']['precision'] or
                amount * self.buy_price < 2 * 10 ** -self.market['base']['precision']):
            amount = 0
        return amount

    def calculate_order_prices(self):
        # Set center price as None, in case dynamic has not amount given, center price is calculated from market orders
        center_price = None
        spread = self.spread

        # Calculate spread if dynamic spread option in use, this calculation doesn't include own orders on the market
        if self.dynamic_spread:
            spread = self.get_market_spread(quote_amount=self.market_depth_amount) * self.dynamic_spread_factor

        if self.is_center_price_dynamic:
            # Calculate center price from the market orders

            if self.external_feed:
                # Try getting center price from external source
                center_price = self.get_external_market_center_price(self.external_price_source)

            if self.center_price_depth > 0 and not self.external_feed:
                # Calculate with quote amount if given
                center_price = self.get_market_center_price(quote_amount=self.center_price_depth)

            self.center_price = self.calculate_center_price(
                center_price,
                self.is_asset_offset,
                spread,
                self['order_ids'],
                self.manual_offset
            )
        else:
            # User has given center price to use, calculate offsets and spread
            self.center_price = self.calculate_center_price(
                self.center_price,
                self.is_asset_offset,
                spread,
                self['order_ids'],
                self.manual_offset
            )

        self.buy_price = self.center_price / math.sqrt(1 + spread)
        self.sell_price = self.center_price * math.sqrt(1 + spread)

    def update_orders(self):
        self.log.debug('Starting to update orders')

        # Cancel the orders before redoing them
        self.cancel_all_orders()
        self.clear_orders()

        # Recalculate buy and sell order prices
        self.calculate_order_prices()

        order_ids = []
        expected_num_orders = 0

        amount_to_buy = self.amount_to_buy
        amount_to_sell = self.amount_to_sell

        # Buy Side
        if amount_to_buy:
            buy_order = self.place_market_buy_order(amount_to_buy, self.buy_price, True)
            if buy_order:
                self.save_order(buy_order)
                order_ids.append(buy_order['id'])
            expected_num_orders += 1

        # Sell Side
        if amount_to_sell:
            sell_order = self.place_market_sell_order(amount_to_sell, self.sell_price, True)
            if sell_order:
                self.save_order(sell_order)
                order_ids.append(sell_order['id'])
            expected_num_orders += 1

        self['order_ids'] = order_ids

        self.log.info("Done placing orders")

        # Some orders weren't successfully created, redo them
        if len(order_ids) < expected_num_orders and not self.disabled:
            self.update_orders()

    def _calculate_center_price(self, suppress_errors=False):
        highest_bid = float(self.ticker().get('highestBid'))
        lowest_ask = float(self.ticker().get('lowestAsk'))

        if highest_bid is None or highest_bid == 0.0:
            if not suppress_errors:
                self.log.critical(
                    "Cannot estimate center price, there is no highest bid."
                )
                self.disabled = True
            return None
        elif lowest_ask is None or lowest_ask == 0.0:
            if not suppress_errors:
                self.log.critical(
                    "Cannot estimate center price, there is no lowest ask."
                )
                self.disabled = True
            return None

        # Calculate center price between two closest orders on the market
        return highest_bid * math.sqrt(lowest_ask / highest_bid)

    def calculate_center_price(self, center_price=None, asset_offset=False, spread=None,
                               order_ids=None, manual_offset=0, suppress_errors=False):
        """ Calculate center price which shifts based on available funds
        """
        if center_price is None:
            # No center price was given so we simply calculate the center price
            calculated_center_price = self._calculate_center_price(suppress_errors)
        else:
            # Center price was given so we only use the calculated center price for quote to base asset conversion
            calculated_center_price = self._calculate_center_price(True)
            if not calculated_center_price:
                calculated_center_price = center_price

        if center_price:
            calculated_center_price = center_price

        # Calculate asset based offset to the center price
        if asset_offset:
            calculated_center_price = self.calculate_asset_offset(calculated_center_price, order_ids, spread)

        # Calculate final_offset_price if manual center price offset is given
        if manual_offset:
            calculated_center_price = self.calculate_manual_offset(calculated_center_price, manual_offset)

        return calculated_center_price

    def calculate_asset_offset(self, center_price, order_ids, spread):
        """ Adds offset based on the asset balance of the worker to the center price

            :param float | center_price: Center price
            :param list | order_ids: List of order ids that are used to calculate balance
            :param float | spread: Spread percentage as float (eg. 0.01)
            :return: Center price with asset offset
        """
        total_balance = self.count_asset(order_ids)
        total = (total_balance['quote'] * center_price) + total_balance['base']

        if not total:  # Prevent division by zero
            base_percent = quote_percent = 0.5
        else:
            base_percent = total_balance['base'] / total
            quote_percent = 1 - base_percent

        highest_bid = float(self.ticker().get('highestBid'))
        lowest_ask = float(self.ticker().get('lowestAsk'))

        lowest_price = center_price / (1 + spread)
        highest_price = center_price * (1 + spread)

        # Use highest_bid price if spread-based price is lower. This limits offset aggression.
        lowest_price = max(lowest_price, highest_bid)
        # Use lowest_ask price if spread-based price is higher
        highest_price = min(highest_price, lowest_ask)

        return math.pow(highest_price, base_percent) * math.pow(lowest_price, quote_percent)

    @staticmethod
    def calculate_manual_offset(center_price, manual_offset):
        """ Adds manual offset to given center price

            :param float | center_price:
            :param float | manual_offset:
            :return: Center price with manual offset

            Adjust center price by given percent in symmetrical way. Thus, -1% adjustement on BTS:USD market will be
            same as adjusting +1% on USD:BTS market.
        """
        if manual_offset < 0:
            return center_price / (1 + abs(manual_offset))
        else:
            return center_price * (1 + manual_offset)

    def check_orders(self, *args, **kwargs):
        """ Tests if the orders need updating
        """
        delta = datetime.now() - self.last_check

        # Store current available balance and balance in orders to the database for profit calculation purpose
        self.store_profit_estimation_data()

        # Only allow to check orders whether minimal time passed
        if delta < timedelta(seconds=self.min_check_interval) and not self.initializing:
            self.log.debug('Ignoring market_update event as min_check_interval is not passed')
            return

        orders = self.fetch_orders()

        # Detect complete fill, order expiration, manual cancel, or just init
        need_update = False
        if not orders:
            need_update = True
        else:
            # Loop trough the orders and look for changes
            for order_id, order in orders.items():
                current_order = self.get_order(order_id)

                if not current_order:
                    need_update = True
                    self.log.debug('Could not found order on the market, it was filled, expired or cancelled')
                    # Write a trade log entry only when we are not using custom expiration because we cannot
                    # distinguish an expired order from filled
                    if not self.is_custom_expiration:
                        self.write_order_log(self.worker_name, order)
                elif self.is_reset_on_partial_fill:
                    # Detect partially filled orders;
                    # on fresh order 'for_sale' is always equal to ['base']['amount']
                    if current_order['for_sale']['amount'] != current_order['base']['amount']:
                        diff_abs = current_order['base']['amount'] - current_order['for_sale']['amount']
                        diff_rel = diff_abs / current_order['base']['amount']
                        if diff_rel >= self.partial_fill_threshold:
                            need_update = True
                            self.log.info('Partially filled order detected, filled {:.2%}'.format(diff_rel))
                            # FIXME: Need to write trade operation; possible race condition may occur: while
                            #        we're updating order it may be filled further so trade log entry will not
                            #        be correct

        # Check center price change when using market center price with reset option on change
        if self.is_reset_on_price_change and self.is_center_price_dynamic:
            # This doesn't use external price feed because it is not allowed to be active
            # same time as reset_on_price_change
            spread = self.spread

            # Calculate spread if dynamic spread option in use, this calculation includes own orders on the market
            if self.dynamic_spread:
                spread = self.get_market_spread(quote_amount=self.market_depth_amount) * self.dynamic_spread_factor

            center_price = self.calculate_center_price(
                None,
                self.is_asset_offset,
                spread,
                self['order_ids'],
                self.manual_offset
            )
            diff = abs((self.center_price - center_price) / self.center_price)
            if diff >= self.price_change_threshold:
                self.log.debug('Center price changed, updating orders. Diff: {:.2%}'.format(diff))
                need_update = True

        if need_update:
            self.update_orders()
        elif self.initializing:
            self.log.info("Orders correct on market")

        self.initializing = False

        if self.view:
            self.update_gui_slider()
            self.update_gui_profit()

        self.last_check = datetime.now()
