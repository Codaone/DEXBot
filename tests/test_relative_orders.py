import pytest
from dexbot.strategies.relative_orders import Strategy
from dexbot.strategies.config_parts.relative_config import ConfigElement
from fixtures import fixture_data
import logging
import math
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


class Test_Strategy:
    def setup_class(self):
        self.TEST_CONFIG = fixture_data()
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
        account = ConfigElement(
            key='account', type='string', default='', title='Account',
            description='BitShares account name for the bot to operate with',
            extra=''
        )
        cf = Strategy.configure()
        logging.info(account)
        assert account in cf

    def test_configure_details(self):
        cf_details = Strategy.configure_details()
        logging.info(cf_details)
        assert cf_details == []

    def test_error(self):
        r = self.relative_strategy.error()
        logging.info(r)
        assert r is None

    def test_tick(self):
        r = self.relative_strategy.tick(
            '0228fec41a799ec45c218cb441ae249cef1bbcb2')
        logging.info(r)
        assert r is None

    def test_amount_to_sell(self):
        logging.info('sell_price:{}'.format(self.relative_strategy.sell_price))
        assert self.relative_strategy.sell_price is None

        self.relative_strategy.calculate_order_prices()
        amount_to_sell = self.relative_strategy.amount_to_sell
        logging.info('amount_to_sell:{}'.format(amount_to_sell))

        assert amount_to_sell == self.TEST_CONFIG['workers']['worker 1']['amount']

    def test_amount_to_buy(self):
        self.relative_strategy.calculate_order_prices()
        logging.info('buy_price:{}'.format(self.relative_strategy.buy_price))

        amount_to_buy = self.relative_strategy.amount_to_buy
        logging.info('amount_to_buy:{}'.format(amount_to_buy))

        assert amount_to_buy == self.TEST_CONFIG['workers']['worker 1']['amount']

    def test_calculate_order_prices(self):
        # no return
        calculate_prices = self.relative_strategy.calculate_order_prices()
        logging.info(calculate_prices)
        assert calculate_prices is None

        buy_price = self.relative_strategy.buy_price
        sell_price = self.relative_strategy.sell_price
        center_price = self.relative_strategy.center_price
        spread = self.relative_strategy.spread
        logging.info('buy_price:{}'.format(buy_price))
        logging.info('sell_price:{}'.format(sell_price))
        logging.info('center_price:{}'.format(center_price))
        logging.info('spread:{}'.format(spread))

        assert self.relative_strategy.center_price == center_price

        buy_price_ca = center_price / math.sqrt(1 + spread)
        logging.info('buy_price_ca:{}'.format(buy_price_ca))

        sell_price_ca = center_price * math.sqrt(1 + spread)
        logging.info('sell_price_ca:{}'.format(sell_price_ca))

        assert buy_price == buy_price_ca
        assert sell_price == sell_price_ca

    def test_update_orders(self):
        self.relative_strategy.update_orders()
        # 0.2927 3.2530904359141184
        from bitshares.market import Market
        market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
        for o in market.accountopenorders():
            if o.get('for_sale') == 1:
                assert o.get('price') == 3.2530904359141184
            else:
                assert o.get('price') == 0.2927

    def test_calculate_center_price(self):
        from bitshares.market import Market
        market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
        highest_bid = market.ticker().get('highestBid')
        lowest_ask = market.ticker().get('lowestAsk')

        cp = highest_bid * math.sqrt(lowest_ask / highest_bid)
        center_price = self.relative_strategy.calculate_center_price()

        assert cp == center_price

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
        assert calculate_asset_offset == r

    def test_calculate_manual_offset(self):
        center_price = 1
        manual_offset = 0.1

        calculate_offset = self.relative_strategy.calculate_manual_offset(
            center_price=center_price, manual_offset=manual_offset)
        logging.info(calculate_offset)

        assert calculate_offset == center_price * (1 + manual_offset)

        manual_offset = -0.1

        calculate_offset = self.relative_strategy.calculate_manual_offset(
            center_price=center_price, manual_offset=manual_offset)
        logging.info(calculate_offset)

        assert calculate_offset == center_price / (1 + abs(manual_offset))

    def test_check_orders(self):
        self.relative_strategy.check_orders()


if __name__ == '__main__':
    import os
    cur_dir = os.path.dirname(__file__)
    test_file = os.path.join(cur_dir, 'test_relative_orders.py')
    pytest.main(['--capture=no', test_file])
