import pytest
from dexbot.strategies.relative_orders import Strategy
from bitshares import BitShares
from bitshares.notify import Notify
from fixtures import fixture_data
import logging
import os
logging.basicConfig(format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s',
                    level=logging.WARNING)


class Test_Strategy:
    def setup_class(self):
        TEST_CONFIG = fixture_data()
        # ,bitshares_instance=self.bitShares)
        self.relative_strategy = Strategy(name='worker 1', config=TEST_CONFIG)

    def test_print(self):
        logging.warning('asdfasdfasdf')

    def teardown_class(self):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_configure(self):
        from dexbot.strategies.config_parts.relative_config import ConfigElement
        account = ConfigElement(key='account', type='string', default='', title='Account',
                                description='BitShares account name for the bot to operate with', extra='')
        cf = Strategy.configure()
        logging.warning(account)
        assert account in cf

    def test_configure_details(self):
        cf_details = Strategy.configure_details()
        logging.warning(cf_details)
        assert cf_details == []

    def test_error(self):
        r = self.relative_strategy.error()
        logging.warning(r)
        assert r == None

    def test_tick(self):
        r = self.relative_strategy.tick(
            '0228fec41a799ec45c218cb441ae249cef1bbcb2')
        logging.warning(r)
        assert None == r

    def test_amount_to_sell(self):
        self.relative_strategy.sell_price = 1
        amount_to_sell = self.relative_strategy.amount_to_sell
        logging.warning(amount_to_sell)

    def test_amount_to_buy(self):
        self.relative_strategy.buy_price = 1
        amount_to_buy = self.relative_strategy.amount_to_buy
        logging.warning(amount_to_buy)

    def test_calculate_order_prices(self):
        calculate_order_prices = self.relative_strategy.calculate_order_prices()
        logging.warning(calculate_order_prices)
        assert None == calculate_order_prices

    def test_update_orders(self):
        r = self.relative_strategy.update_orders()
        logging.warning(r)
        assert None == r

    def test_calculate_center_price(self):
        center_price = self.relative_strategy.calculate_center_price()
        logging.warning(center_price)
        assert center_price != None

    def test_calculate_asset_offset(self):
        calculate_asset_offset = self.relative_strategy.calculate_asset_offset(
            center_price=1, order_ids=[], spread=0.5)
        logging.warning(calculate_asset_offset)
        assert calculate_asset_offset != None

    def test_calculate_manual_offset(self):
        calculate_manual_offset = self.relative_strategy.calculate_manual_offset(
            center_price=0, manual_offset=0.1)
        logging.warning(calculate_manual_offset)
        assert calculate_manual_offset != None

    def test_check_orders(self):
        r = self.relative_strategy.check_orders()
        logging.warning(r)
        assert r == None


#--------------------------test------------------------
if __name__ == '__main__':
    cur_dir = os.path.dirname(__file__)
    pytest.main(['--capture=no', cur_dir + '/test_relative_orders.py'])
