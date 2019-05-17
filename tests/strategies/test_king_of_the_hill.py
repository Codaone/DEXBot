from fixtures import fixture_data_KH
from dexbot.strategies.king_of_the_hill import Strategy
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


class Test_Strategy:
    def setup_class(self):
        self.TEST_CONFIG = fixture_data_KH()
        self.king_hill = Strategy(
            name='worker 1',
            config=self.TEST_CONFIG)

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_maintain_strategy(self):
        self.king_hill.maintain_strategy()
    # def test_check_orders(self):
    #     self.king_hill.check_orders()
    # def test_get_order_type(self):
    #     from bitshares.market import Market
    #     market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
    #     tx = market.buy(price=0.1, amount=1, returnOrderId=True)
    #     logging.info('Order created:{}'.format(tx['orderid']))
    #     for o in market.accountopenorders():
    #         r = self.king_hill.get_order_type(o)
    #         if r != 'buy':
    #             raise AssertionError('order type error!')
    #         logging.info(r)
    #     market.cancel(tx['orderid'])
    #     logging.info('Cancel order:{}'.format(tx['orderid']))
    # def test_calc_order_prices(self):
    #     self.king_hill.calc_order_prices()
    #     r=self.king_hill.buy_price
    #     if r is not None:
    #         raise AssertionError('buy_price have no  value!')

    # def test_place_order(self):
    #     self.king_hill.place_order('buy')
    # def test_place_orders(self):
    #     self.king_hill.place_orders()
    # def test_amount_quote():
    #     r=self.king_hill.amount_quote
    #     logging.info(r)

    # def test_amount_base():
    #     r=self.king_hill.amount_base
    #     logging.info(r)


if __name__ == '__main__':
    import os
    import pytest
    cur_dir = os.path.dirname(__file__)
    test_file = os.path.join(cur_dir, 'test_king_of_the_hill.py')
    pytest.main(['--capture=no', test_file])
