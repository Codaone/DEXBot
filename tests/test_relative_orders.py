from dexbot.strategies.relative_orders import Strategy
from fixtures import fixture_data_RO
import logging
import math
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


class Test_Strategy:
    def setup_class(self):
        self.TEST_CONFIG = fixture_data_RO()
        self.relative_strategy = Strategy(
            name='worker 1',
            config=self.TEST_CONFIG)

    def teardown_class(self):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_configure(self):
        logging.info(self.relative_strategy.configure())
        account = self.TEST_CONFIG['workers']['worker 1']['account']
        conditon = ('dexbot-test1' != account)

        if conditon:
            raise AssertionError('account error!')

    def test_configure_details(self):
        cf_details = self.relative_strategy.configure_details()
        logging.info(cf_details)
        conditon = (cf_details == [])
        if not conditon:
            raise AssertionError('Not empty value！')

    def test_error(self):
        '''Event method return None'''
        r = self.relative_strategy.error()
        logging.info(r)
        if r is not None:
            raise AssertionError('Event method return None!')

    def test_tick(self):
        '''Event method return None'''
        r = self.relative_strategy.tick(
            '0228fec41a799ec45c218cb441ae249cef1bbcb2')
        logging.info(r)
        if r is not None:
            raise AssertionError('Event method return None!')

    def test_amount_to_sell(self):
        logging.info('sell_price:{}'.format(self.relative_strategy.sell_price))
        r = self.relative_strategy.sell_price
        if r is not None:
            raise AssertionError('The method should have no return value!')

        self.relative_strategy.calculate_order_prices()
        amount_to_sell = self.relative_strategy.amount_to_sell
        logging.info('amount_to_sell:{}'.format(amount_to_sell))

        amount = self.TEST_CONFIG['workers']['worker 1']['amount']
        if amount_to_sell != amount:
            raise AssertionError('order size wrong!')

    def test_amount_to_buy(self):
        self.relative_strategy.calculate_order_prices()
        logging.info('buy_price:{}'.format(self.relative_strategy.buy_price))

        amount_to_buy = self.relative_strategy.amount_to_buy
        logging.info('amount_to_buy:{}'.format(amount_to_buy))

        amount_to_buy_cf = self.TEST_CONFIG['workers']['worker 1']['amount']
        if amount_to_buy != amount_to_buy_cf:
            raise AssertionError('order size wrong!')

    def test_calculate_order_prices(self):
        # no return
        calculate_prices = self.relative_strategy.calculate_order_prices()
        logging.info(calculate_prices)
        if calculate_prices is not None:
            raise AssertionError('The method should have no return value!')

        buy_price = self.relative_strategy.buy_price
        sell_price = self.relative_strategy.sell_price
        center_price = self.relative_strategy.center_price
        spread = self.relative_strategy.spread
        logging.info('buy_price:{}'.format(buy_price))
        logging.info('sell_price:{}'.format(sell_price))
        logging.info('center_price:{}'.format(center_price))
        logging.info('spread:{}'.format(spread))

        if self.relative_strategy.center_price != center_price:
            raise AssertionError('Center price calculation error!')

        buy_price_ca = center_price / math.sqrt(1 + spread)
        logging.info('buy_price_ca:{}'.format(buy_price_ca))

        sell_price_ca = center_price * math.sqrt(1 + spread)
        logging.info('sell_price_ca:{}'.format(sell_price_ca))

        if buy_price != buy_price_ca:
            raise AssertionError('buy_price calculation error!')
        if sell_price != sell_price_ca:
            raise AssertionError('sell_price calculation error!')

    def test_update_orders(self):
        self.relative_strategy.update_orders()
        # 0.2927 3.2530904359141184
        from bitshares.market import Market
        market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
        for o in market.accountopenorders():
            if o.get('for_sale') == 1:
                if o.get('price') != 3.2530904359141184:
                    raise AssertionError('Order Price Error！')
            else:
                if o.get('price') != 0.2927:
                    raise AssertionError('Order Price Error！')

    def test_calculate_center_price(self):
        from bitshares.market import Market
        market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
        highest_bid = market.ticker().get('highestBid')
        lowest_ask = market.ticker().get('lowestAsk')

        cp = highest_bid * math.sqrt(lowest_ask / highest_bid)
        center_price = self.relative_strategy.calculate_center_price()

        if cp != center_price:
            raise AssertionError('Center price calculation error!')

    def test_calculate_asset_offset(self):
        from bitshares.market import Market
        center_price = 1
        spread = 0.5
        order_ids = []

        total_balance = self.relative_strategy.count_asset(order_ids)
        total = (total_balance['quote'] * center_price) + total_balance['base']

        if not total:  # Prevent division by zero
            base_percent = quote_percent = 0.5
        else:
            base_percent = total_balance['base'] / total
            quote_percent = 1 - base_percent

        logging.info(base_percent)
        logging.info(quote_percent)

        market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
        highest_bid = float(market.ticker().get('highestBid'))
        lowest_ask = float(market.ticker().get('lowestAsk'))

        logging.info(highest_bid)
        logging.info(lowest_ask)

        lowest_price = center_price / (1 + spread)
        highest_price = center_price * (1 + spread)

        logging.info(lowest_price)
        logging.info(highest_price)

        lowest_price = max(lowest_price, highest_bid)
        highest_price = min(highest_price, lowest_ask)

        logging.info(lowest_price)
        logging.info(highest_price)

        r = math.pow(highest_price, base_percent) * \
            math.pow(lowest_price, quote_percent)

        logging.info(r)

        calculate_asset_offset = self.relative_strategy.calculate_asset_offset(
            center_price=center_price, order_ids=[], spread=spread)

        logging.info(calculate_asset_offset)
        if calculate_asset_offset != r:
            raise AssertionError('Calculate asset offset wrong!')

    def test_calculate_manual_offset(self):
        center_price = 1
        manual_offset = 0.1

        calculate_offset = self.relative_strategy.calculate_manual_offset(
            center_price=center_price, manual_offset=manual_offset)
        logging.info(calculate_offset)

        if calculate_offset != center_price * (1 + manual_offset):
            raise AssertionError('Calculate manual offset wrong!')

        manual_offset = -0.1

        calculate_offset = self.relative_strategy.calculate_manual_offset(
            center_price=center_price, manual_offset=manual_offset)
        logging.info(calculate_offset)

        if calculate_offset != center_price / (1 + abs(manual_offset)):
            raise AssertionError('Calculate manual offset wrong!')

    def test_check_orders(self):
        self.relative_strategy.check_orders()


if __name__ == '__main__':
    import os
    import pytest
    cur_dir = os.path.dirname(__file__)
    test_file = os.path.join(cur_dir, 'test_relative_orders.py')
    pytest.main(['--capture=no', test_file])
