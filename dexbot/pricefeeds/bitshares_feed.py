import logging
import math

from bitshares.instance import shared_bitshares_instance
from bitshares.price import Order


class BitsharesPriceFeed:
    """ This Price Feed class enables usage of Bitshares DEX for market center and order
        book pricing, without requiring a registered account. It may be used for both
        strategy and indicator analysis tools.

        All prices are passed and returned as BASE/QUOTE.
        (In the BREAD/USD market that would be USD/BREAD, 2.5 USD / 1 BREAD).
            - Buy orders reserve BASE
            - Sell orders reserve QUOTE
    """
    def __init__(self,
                 market,
                 bitshares_instance=None):

        self.market = market
        self.ticker = self.market.ticker
        self.disabled = False  # flag for suppress errors

        # Count of orders to be fetched from the API
        self.fetch_depth = 8
        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()

        self.log = logging.LoggerAdapter(
            logging.getLogger('dexbot.pricefeed_log'), {}
        )

    def get_limit_orders(self, depth=1):
        """ Returns orders from the current market. Orders are sorted by price. Does not require account info.

            get_limit_orders() call does not have any depth limit.

            :param int depth: Amount of orders per side will be fetched, default=1
            :return: Returns a list of orders or None
        """
        orders = self.bitshares.rpc.get_limit_orders(self.market['base']['id'], self.market['quote']['id'], depth)
        orders = [Order(o, bitshares_instance=self.bitshares) for o in orders]
        return orders

    def get_orderbook_orders(self, depth=1):
        """ Returns orders from the current market split in bids and asks. Orders are sorted by price.

            Market.orderbook() call has hard-limit of depth=50 enforced by bitshares node.

            bids = buy orders
            asks = sell orders

            :param int | depth: Amount of orders per side will be fetched, default=1
            :return: Returns a dictionary of orders or None
        """
        return self.market.orderbook(depth)

    def filter_buy_orders(self, orders, sort=None):
        """ Return own buy orders from list of orders. Can be used to pick buy orders from a list
            that is not up to date with the blockchain data.

            :param list | orders: List of orders
            :param string | sort: DESC or ASC will sort the orders accordingly, default None
            :return list | buy_orders: List of buy orders only
        """
        buy_orders = []

        # Filter buy orders
        for order in orders:
            # Check if the order is buy order, by comparing asset symbol of the order and the market
            if order['base']['symbol'] == self.market['base']['symbol']:
                buy_orders.append(order)

        if sort:
            buy_orders = self.sort_orders_by_price(buy_orders, sort)

        return buy_orders

    def filter_sell_orders(self, orders, sort=None, invert=True):
        """ Return sell orders from list of orders. Can be used to pick sell orders from a list
            that is not up to date with the blockchain data.

            :param list | orders: List of orders
            :param string | sort: DESC or ASC will sort the orders accordingly, default None
            :param bool | invert: return inverted orders or not
            :return list | sell_orders: List of sell orders only
        """
        sell_orders = []

        # Filter sell orders
        for order in orders:
            # Check if the order is buy order, by comparing asset symbol of the order and the market
            if order['base']['symbol'] != self.market['base']['symbol']:
                # Invert order before appending to the list, this gives easier comparison in strategy logic
                if invert:
                    order = order.invert()
                sell_orders.append(order)

        if sort:
            sell_orders = self.sort_orders_by_price(sell_orders, sort)

        return sell_orders

    def get_highest_market_buy_order(self, orders=None):
        """ Returns the highest buy order that is not own, regardless of order size.

            :param list | orders: Optional list of orders, if none given fetch newest from market
            :return: Highest market buy order or None
        """
        if not orders:
            orders = self.get_market_buy_orders(1)

        try:
            order = orders[0]
        except IndexError:
            self.log.info('Market has no buy orders.')
            return None

        return order

    def get_lowest_market_sell_order(self, orders=None):
        """ Returns the lowest sell order that is not own, regardless of order size.

            :param list | orders: Optional list of orders, if none given fetch newest from market
            :return: Lowest market sell order or None
        """
        if not orders:
            orders = self.get_market_sell_orders(1)

        try:
            order = orders[0]
        except IndexError:
            self.log.info('Market has no sell orders.')
            return None

        return order

    def get_market_buy_orders(self, depth=10):
        """ Fetches most recent data and returns list of buy orders.

            :param int | depth: Amount of buy orders returned, Default=10
            :return: List of market sell orders
        """
        orders = self.get_limit_orders(depth=depth)
        buy_orders = self.filter_buy_orders(orders)
        return buy_orders

    def get_market_sell_orders(self, depth=10):
        """ Fetches most recent data and returns list of sell orders.

            :param int | depth: Amount of sell orders returned, Default=10
            :return: List of market sell orders
        """
        orders = self.get_limit_orders(depth=depth)
        sell_orders = self.filter_sell_orders(orders)
        return sell_orders

    def get_market_buy_price(self, quote_amount=0, base_amount=0, **kwargs):
        # TODO: refactor to use orders instead of exclude_own_orders
        """ Returns the BASE/QUOTE price for which [depth] worth of QUOTE could be bought, enhanced with
            moving average or weighted moving average

            :param float | quote_amount:
            :param float | base_amount:
            :param dict | kwargs:
            :return: price as float
        """
        market_buy_orders = []

        # In case amount is not given, return price of the highest buy order on the market
        if quote_amount == 0 and base_amount == 0:
            return float(self.ticker().get('highestBid'))

        # Like get_market_sell_price(), but defaulting to base_amount if both base and quote are specified.
        asset_amount = base_amount

        # Since the purpose is never get both quote and base amounts, favor base amount if both given because
        # this function is looking for buy price.

        if base_amount > quote_amount:
            base = True
        else:
            asset_amount = quote_amount
            base = False

        if not market_buy_orders:
            market_buy_orders = self.get_market_buy_orders(depth=self.fetch_depth)
        market_fee = self.market['base'].market_fee_percent

        target_amount = asset_amount * (1 + market_fee)

        quote_amount = 0
        base_amount = 0
        missing_amount = target_amount

        for order in market_buy_orders:
            if base:
                # BASE amount was given
                if order['base']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['base']['amount']
                else:
                    base_amount += missing_amount
                    quote_amount += missing_amount / order['price']
                    break
            elif not base:
                # QUOTE amount was given
                if order['quote']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['quote']['amount']
                else:
                    base_amount += missing_amount * order['price']
                    quote_amount += missing_amount
                    break

        # Prevent division by zero
        if not quote_amount:
            return 0.0

        return base_amount / quote_amount

    def get_market_sell_price(self, quote_amount=0, base_amount=0, **kwargs):
        # TODO: refactor to use orders instead of exclude_own_orders
        """ Returns the BASE/QUOTE price for which [quote_amount] worth of QUOTE could be bought,
            enhanced with moving average or weighted moving average.

            [quote/base]_amount = 0 means lowest regardless of size

            :param float | quote_amount:
            :param float | base_amount:
            :param dict | kwargs:
            :return:
        """
        market_sell_orders = []

        # In case amount is not given, return price of the lowest sell order on the market
        if quote_amount == 0 and base_amount == 0:
            return float(self.ticker().get('lowestAsk'))

        asset_amount = quote_amount

        # Since the purpose is never get both quote and base amounts, favor quote amount if both given because
        # this function is looking for sell price.

        if quote_amount > base_amount:
            quote = True
        else:
            asset_amount = base_amount
            quote = False

        if not market_sell_orders:
            market_sell_orders = self.get_market_sell_orders(depth=self.fetch_depth)
        market_fee = self.market['quote'].market_fee_percent

        target_amount = asset_amount * (1 + market_fee)

        quote_amount = 0
        base_amount = 0
        missing_amount = target_amount

        for order in market_sell_orders:
            if quote:
                # QUOTE amount was given
                if order['quote']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['quote']['amount']
                else:
                    base_amount += missing_amount * order['price']
                    quote_amount += missing_amount
                    break
            elif not quote:
                # BASE amount was given
                if order['base']['amount'] <= missing_amount:
                    quote_amount += order['quote']['amount']
                    base_amount += order['base']['amount']
                    missing_amount -= order['base']['amount']
                else:
                    base_amount += missing_amount
                    quote_amount += missing_amount / order['price']
                    break

        # Prevent division by zero
        if not quote_amount:
            return 0.0

        return base_amount / quote_amount

    def get_market_center_price(self, base_amount=0, quote_amount=0, suppress_errors=False):
        """ Returns the center price of market including own orders.

            :param float base_amount:
            :param float quote_amount:
            :param bool suppress_errors: True = return None on errors, False = disable worker
            :return: Market center price as float
        """
        center_price = None
        buy_price = self.get_market_buy_price(quote_amount=quote_amount, base_amount=base_amount)
        sell_price = self.get_market_sell_price(quote_amount=quote_amount, base_amount=base_amount)

        if buy_price is None or buy_price == 0.0:
            if not suppress_errors:
                self.log.critical("Cannot estimate center price, there is no highest bid.")
                self.disabled = True
                return None

        if sell_price is None or sell_price == 0.0:
            if not suppress_errors:
                self.log.critical("Cannot estimate center price, there is no lowest ask.")
                self.disabled = True
                return None
            # Calculate and return market center price. make sure buy_price has value
        if buy_price:
            center_price = buy_price * math.sqrt(sell_price / buy_price)
            self.log.debug('Center price in get_market_center_price: {:.8f} '.format(center_price))
        return center_price

    def get_market_spread(self, quote_amount=0, base_amount=0):
        """ Returns the market spread %, including own orders, from specified depth.

            :param float | quote_amount:
            :param float | base_amount:
            :return: Market spread as float or None
        """
        ask = self.get_market_sell_price(quote_amount=quote_amount, base_amount=base_amount)
        bid = self.get_market_buy_price(quote_amount=quote_amount, base_amount=base_amount)

        # Calculate market spread
        if ask == 0 or bid == 0:
            return None

        return ask / bid - 1

    @staticmethod
    def sort_orders_by_price(orders, sort='DESC'):
        """ Return list of orders sorted ascending or descending by price

            :param list | orders: list of orders to be sorted
            :param string | sort: ASC or DESC. Default DESC
            :return list: Sorted list of orders
        """
        if sort.upper() == 'ASC':
            reverse = False
        elif sort.upper() == 'DESC':
            reverse = True
        else:
            return None

        # Sort orders by price
        return sorted(orders, key=lambda order: order['price'], reverse=reverse)
