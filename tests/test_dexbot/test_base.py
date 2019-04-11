import pytest
from dexbot.strategies.base import StrategyBase
import logging
import os
from fixtures import fixture_data
from fixtures import get_balance
from bitshares.market import Market
from bitshares.exceptions import MissingKeyError
from bitshares.price import Order
from bitshares.dex import Dex
import math
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


class Test_StrategyBase:
    def setup_class(self):
        TEST_CONFIG = fixture_data()
        self.strategy_base = StrategyBase(name='worker 1', config=TEST_CONFIG)

    def teardown_class(self):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    # def test_configure(self):
    #     base_config = StrategyBase.configure()
    #     for x in base_config:
    #         logging.info(x)
    #         assert x != ''

    # def test_configure_details(self):
    #     config_details = StrategyBase.configure_details()
    #     for x in config_details:
    #         logging.info(x)
    #         assert x == ''

    # def test_account_total_value(self):
    #     from fixtures import get_balance
    #     bts_value = float(get_balance('BTS'))
    #     msg = str(bts_value)
    #     logging.info(msg)
    #     test_account_total_value = self.strategy_base.account_total_value(
    #         'BTS')
    #     logging.info(str(test_account_total_value))
    #     assert test_account_total_value >= bts_value

    # def test_balance(self):
    #     bts_value = float(get_balance('BTS'))
    #     logging.info(str(bts_value))
    #     test_balance = self.strategy_base.balance('BTS')
    #     logging.info(str(test_balance))
    #     assert bts_value == test_balance

    # def test_calculate_order_data(self):
    #     from bitshares.price import Order
    #     order = Order(0.315, base="BADCOIN", quote="BTS")
    #     amount = 10
    #     price = 2
    #     orders = self.strategy_base.calculate_order_data(order, amount, price)
    #     assert 10 == orders['quote'], 'calculate_order_data() error!'
    #     assert 20 == orders['base'], 'calculate_order_data() error!'
    #     assert 2 == orders['price'], 'calculate_order_data() error!'

    # def test_calculate_worker_value(self):
    #     total_account_balance = get_balance('BTS')
    #     total_account_calculate = self.strategy_base.calculate_worker_value(
    #         'BTS')
    #     logging.info(total_account_balance)
    #     logging.info(total_account_calculate)
    #     assert total_account_balance <= total_account_calculate

    # def test_cancel_all_orders(self):
    #     market = Market('BTS/BADCOIN')
    #     with pytest.raises(MissingKeyError):
    #         market.sell(
    #             1,
    #             10,
    #             expiration=60 * 60,
    #             returnOrderId=True
    #         )
    #     self.strategy_base.cancel_all_orders()
    #     openorders = market.accountopenorders()
    #     logging.info(openorders)
    #     assert openorders == [], 'order is not cancel!'
#
    # # def test_cancel_orders(self):
    #     market = Market('BTS/BADCOIN')
    #     logging.info(market.accountopenorders)
    #     with pytest.raises(MissingKeyError):
    #         market.sell(
    #             1,
    #             10,
    #             expiration=60 * 60,
    #             returnOrderId=True
    #         )
    #     with pytest.raises(MissingKeyError):
    #         self.strategy_base.cancel_orders('123')
    #     order = Order(0.315, base="BADCOIN", quote="BTS")
    #     with pytest.raises(MissingKeyError):
    #         self.strategy_base.cancel_orders(order)

    # def test_count_asset(self):
    #     r = self.strategy_base.count_asset()
    #     logging.info(r)
    #     quote = get_balance()
    #     assert quote == r['quote']

    # def test_get_allocated_assets(self):
    #     r = self.strategy_base.get_allocated_assets()
    #     logging.info(r)
    #     assert r['quote'] == 0
    #     assert r['base'] == 0

    # def test_get_market_buy_orders(self):
    #     buy_orders = self.strategy_base.get_market_buy_orders()
    #     logging.info(buy_orders)
    #     assert buy_orders != []

    # def test_get_market_sell_orders(self):
    #     r=self.strategy_base.get_market_sell_orders()
    #     logging.info(r)
    #     assert r != []
    # def test_get_highest_market_buy_order(self):
    #     r = self.strategy_base.get_highest_market_buy_order()
    #     logging.info(r)
    #     assert r != []

    # def test_get_highest_own_buy_order(self):
    #     r = self.strategy_base.get_highest_own_buy_order()
    #     logging.info(r)
    #     assert r is None

    # def test_get_lowest_market_sell_order(self):
    #     r = self.strategy_base.get_lowest_market_sell_order()
    #     logging.info(r)
    #     assert r != []

    # def test_get_lowest_own_sell_order(self):
    #     r = self.strategy_base.get_lowest_own_sell_order()
    #     logging.info(r)
    #     assert r is None

    # def test_get_external_market_center_price(self):
    #     r = self.strategy_base.get_external_market_center_price('Binance')
    #     logging.info(r)

    # def test_get_market_center_price(self):
    #     r = self.strategy_base.get_market_center_price()
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     highestBid = market.ticker().get('highestBid')
    #     lowestAsk = market.ticker().get('lowestAsk')
    #     center_price = lowestAsk * math.sqrt(lowestAsk / highestBid)
    #     logging.info(r)
    #     logging.info(highestBid)
    #     logging.info(lowestAsk)
    #     logging.info(center_price)
    #     assert r < center_price

    # def test_get_market_buy_price(self):
    #     r = self.strategy_base.get_market_buy_price()
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     highestBid = market.ticker().get('highestBid')
    #     logging.info(r)
    #     logging.info(highestBid)
    #     assert r == highestBid

    # def test_get_market_orders(self):
    #     r = self.strategy_base.get_market_orders()
    #     logging.info(r)

    # def test_get_orderbook_orders(self):
    #     r = self.strategy_base.get_orderbook_orders()
    #     logging.info(r)

    # def test_get_market_sell_price(self):
    #     r = self.strategy_base.get_market_sell_price()
    #     logging.info(r)

    # def test_get_market_spread(self):
    #     r = self.strategy_base.get_market_spread()
    #     logging.info(r)

    def test_get_order_cancellation_fee(self):
        r = self.strategy_base.get_order_cancellation_fee('BTS')
        dex = Dex()
        fees = dex.returnFees()
        limit_order_cancel = fees['limit_order_cancel']['fee']
        logging.info(r)
        logging.info(limit_order_cancel)
        assert r == limit_order_cancel

    # def test_get_order_creation_fee(self):
    #     self.strategy_base.get_order_creation_fee('TEST')
    # def test_filter_buy_orders(self):
    #     self.strategy_base.filter_buy_orders(['1223'])
    # def test_filter_sell_orders(self):
    #     self.strategy_base.filter_sell_orders(['1223'])
    # def test_get_own_buy_orders(self):
    #     self.strategy_base.get_own_buy_orders()
    # def test_get_own_sell_orders(self):
    #     self.strategy_base.get_own_sell_orders()
    # def test_get_own_spread(self):
    #     self.strategy_base.get_own_spread()
    # def test_get_updated_order(self):
    #     self.strategy_base.get_updated_order(['123'])
    # def test_execute(self):
    #     self.strategy_base.execute()
    # def test_is_buy_order(self):
    #     self.strategy_base.is_buy_order(['123'])
    # def test_is_current_market(self):
    #     self.strategy_base.is_current_market('1.3.13','1.3.14')
    # def test_is_sell_order(self):
    #     self.strategy_base.is_sell_order(['123'])
    # def test_pause(self):
    #     self.strategy_base.pause()
    # def test_clear_all_worker_data(self):
    #     self.strategy_base.clear_all_worker_data()
    # def test_place_market_buy_order(self):
    #     self.strategy_base.place_market_buy_order(1,0.1)
    # def test_place_market_sell_order(self):
    #     self.strategy_base.place_market_sell_order(1,10)
    # def test_retry_action(self):
    #     self.strategy_base.retry_action(action)
    # def test_store_profit_estimation_data(self):
    #     self.strategy_base.store_profit_estimation_data()
    # def test_get_profit_estimation_data(self):
    #     self.strategy_base.get_profit_estimation_data('ddd')
    # def test_calc_profit(self):
    #     self.strategy_base.calc_profit()
    # def test_write_order_log(self):
    #     self.strategy_base.write_order_log('worker 2',['23'])
    # def test_account(self):
    #     self.strategy_base.account
    # def test_quote_asset(self):
    #     self.strategy_base.quote_asset
    # def test_all_own_orders(self):
    #     self.strategy_base.all_own_orders
    # def test_get_own_orders(self):
    #     self.strategy_base.get_own_orders
    # def test_market(self):
    #     self.strategy_base.market
    # def test_convert_asset(self):
    #     self.strategy_base.convert_asset('TEST','USD')
    # def test_convert_fee(self):
    #     self.strategy_base.convert_fee(0.001,'TEST')
    # def test_get_order(self):
    #     self.strategy_base.get_order(123)
    # def test_get_updated_limit_order(self):
    #     self.strategy_base.get_updated_limit_order([123])
    # def test_purge_all_local_worker_data(self):
    #     self.strategy_base.purge_all_local_worker_data('worker 2')
    # def test_sort_orders_by_price(self):
    #     self.strategy_base.sort_orders_by_price()
    # def test_update_gui_slider(self):
    #     self.strategy_base.update_gui_slider()
    # def test_update_gui_profit(self):
    #     self.strategy_base.update_gui_profit()
    # def tearDown(self):
    #     pass
#-------------------------test------------------
if __name__ == '__main__':
    cur_dir = os.path.dirname(__file__)
    pytest.main(['--capture=no', cur_dir + '/test_base.py'])
