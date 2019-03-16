import unittest
from dexbot.strategies.base import StrategyBase
class test_StrategyBase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from bitshares import BitShares
        self.bitShares=BitShares('wss://node.testnet.bitshares.eu')
    def setUp(self):
        self.strategy_base=StrategyBase('Worker 2',bitshares_instance=self.bitShares)
    def test_configure(self):
        from dexbot.strategies.base import ConfigElement
        base_config=StrategyBase.configure()
        for e in base_config:
            self.assertIsInstance(e,ConfigElement,'configura() not retrun a ConfigElement of object!')
    def test_configure_details(self):
        from dexbot.strategies.base import ConfigElement
        config_details=StrategyBase.configure_details()
        for e in config_details:
            self.assertIsInstance(e,ConfigElement,'configura_details() not retrun a ConfigElement of object!')
    def test_account_total_value(self):
        test_q=self.strategy_base.account_total_value('TEST')
        self.assertEqual(1000,test_q,"dexbot-test1's balance is wrong! ")
        print(test_q)
    def test_balance(self):
        test_q=self.strategy_base.balance('TEST')
        self.assertEqual(1000,test_q,"dexbot-test1's TEST balance is wrong!")
    def test_calculate_order_data(self):
        from bitshares.price import FilledOrder, Order, UpdateCallOrder
        from bitshares.amount import Amount, Asset
        order=Order(0.315, base="CNY", quote="BTS")
        amount=10
        price=2
        orders=self.strategy_base.calculate_order_data(order,amount,price)
        self.assertEqual(10,orders['quote'],'calculate_order_data() error!')
        self.assertEqual(20,orders['base'],'calculate_order_data() error!')
        self.assertEqual(2,orders['price'],'calculate_order_data() error!')
    def test_calculate_worker_value(self):
        total_test=1000
        total_test_calculate=self.strategy_base.calculate_worker_value('TEST')
        self.assertEqual(total_test,total_test_calculate,'calculate_worker_value() error!')
    def test_cancel_all_orders(self):

        self.strategy_base.cancel_all_orders()
    def test_cancel_orders(self):
        pass
    def test_count_asset(self):
        pass
    def test_get_allocated_assets(self):
        pass
    def test_get_market_buy_orders(self):
        pass
    def test_get_market_sell_orders(self):
        pass
    def test_get_highest_market_buy_order(self):
        pass
    def test_get_highest_own_buy_order(self):
        pass
    def test_get_lowest_market_sell_order(self):
        pass
    def test_get_lowest_own_sell_order(self):
        pass
    def test_get_external_market_center_price(self):
        pass
    def test_get_market_center_price(self):
        pass
    def test_get_market_buy_price(self):
        pass
    def test_get_market_orders(self):
        pass
    def test_get_orderbook_orders(self):
        pass
    def test_get_market_sell_price(self):
        pass
    def test_get_market_spread(self):
        pass
    def test_get_order_cancellation_fee(self):
        pass
    def test_get_order_creation_fee(self):
        pass
    def test_filter_buy_orders(self):
        pass
    def test_filter_sell_orders(self):
        pass
    def test_get_own_buy_orders(self):
        pass
    def test_get_own_sell_orders(self):
        pass
    def test_get_own_spread(self):
        pass
    def test_get_updated_order(self):
        pass
    def test_execute(self):
        pass
    def test_is_buy_order(self):
        pass
    def test_is_current_market(self):
        pass
    def test_is_sell_order(self):
        pass
    def test_pause(self):
        pass
    def test_clear_all_worker_data(self):
        pass
    def test_place_market_buy_order(self):
        pass
    def test_place_market_sell_order(self):
        pass
    def test_retry_action(self):
        pass
    def test_store_profit_estimation_data(self):
        pass
    def test_get_profit_estimation_data(self):
        pass
    def test_calc_profit(self):
        pass
    def test_write_order_log(self):
        pass
    def test_account(self):
        pass
    def test_quote_asset(self):
        pass
    def test_all_own_orders(self):
        pass
    def test_get_own_orders(self):
        pass
    def test_market(self):
        pass
    def test_convert_asset(self):
        pass
    def test_convert_fee(self):
        pass
    def test_get_order(self):
        pass
    def test_get_updated_limit_order(self):
        pass
    def test_purge_all_local_worker_data(self):
        pass
    def test_sort_orders_by_price(self):
        pass
    def test_update_gui_slider(self):
        pass
    def test_update_gui_profit(self):
        pass
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        suite.addTest(test_StrategyBase('test_configure'))
        suite.addTest(test_StrategyBase('test_configure_details'))
        suite.addTest(test_StrategyBase('test_account_total_value'))
        suite.addTest(test_StrategyBase('test_balance'))
        suite.addTest(test_StrategyBase('test_calculate_order_data'))
        suite.addTest(test_StrategyBase('test_calculate_worker_value'))
        suite.addTest(test_StrategyBase('test_cancel_all_orders'))
        suite.addTest(test_StrategyBase('test_cancel_orders'))
        suite.addTest(test_StrategyBase('test_count_asset'))
        suite.addTest(test_StrategyBase('test_get_allocated_assets'))
        suite.addTest(test_StrategyBase('test_get_market_buy_orders'))
        suite.addTest(test_StrategyBase('test_get_market_sell_orders'))
        suite.addTest(test_StrategyBase('test_get_highest_market_buy_order'))
        suite.addTest(test_StrategyBase('test_get_highest_own_buy_order'))
        suite.addTest(test_StrategyBase('test_get_lowest_market_sell_order'))
        suite.addTest(test_StrategyBase('test_get_lowest_own_sell_order'))
        suite.addTest(test_StrategyBase('test_get_external_market_center_price'))
        suite.addTest(test_StrategyBase('test_get_market_center_price'))
        suite.addTest(test_StrategyBase('test_get_market_buy_price'))
        suite.addTest(test_StrategyBase('test_get_market_orders'))
        suite.addTest(test_StrategyBase('test_get_orderbook_orders'))
        suite.addTest(test_StrategyBase('test_get_market_sell_price'))
        suite.addTest(test_StrategyBase('test_get_market_spread'))
        suite.addTest(test_StrategyBase('test_get_order_cancellation_fee'))
        suite.addTest(test_StrategyBase('test_get_order_creation_fee'))
        suite.addTest(test_StrategyBase('test_filter_buy_orders'))
        suite.addTest(test_StrategyBase('test_filter_sell_orders'))
        suite.addTest(test_StrategyBase('test_get_own_buy_orders'))
        suite.addTest(test_StrategyBase('test_get_own_sell_orders'))
        suite.addTest(test_StrategyBase('test_get_own_spread'))
        suite.addTest(test_StrategyBase('test_get_updated_order'))
        suite.addTest(test_StrategyBase('test_execute'))
        suite.addTest(test_StrategyBase('test_is_buy_order'))
        suite.addTest(test_StrategyBase('test_is_current_market'))
        suite.addTest(test_StrategyBase('test_is_sell_order'))
        suite.addTest(test_StrategyBase('test_pause'))
        suite.addTest(test_StrategyBase('test_clear_all_worker_data'))
        suite.addTest(test_StrategyBase('test_place_market_buy_order'))
        suite.addTest(test_StrategyBase('test_place_market_sell_order'))
        suite.addTest(test_StrategyBase('test_retry_action'))
        suite.addTest(test_StrategyBase('test_store_profit_estimation_data'))
        suite.addTest(test_StrategyBase('test_get_profit_estimation_data'))
        suite.addTest(test_StrategyBase('test_calc_profit'))
        suite.addTest(test_StrategyBase('test_write_order_log'))
        suite.addTest(test_StrategyBase('test_account'))
        suite.addTest(test_StrategyBase('test_quote_asset'))
        suite.addTest(test_StrategyBase('test_all_own_orders'))
        suite.addTest(test_StrategyBase('test_get_own_orders'))
        suite.addTest(test_StrategyBase('test_market'))
        suite.addTest(test_StrategyBase('test_convert_asset'))
        suite.addTest(test_StrategyBase('test_convert_fee'))
        suite.addTest(test_StrategyBase('test_get_order'))
        suite.addTest(test_StrategyBase('test_get_updated_limit_order'))
        suite.addTest(test_StrategyBase('test_purge_all_local_worker_data'))
        suite.addTest(test_StrategyBase('test_sort_orders_by_price'))
        suite.addTest(test_StrategyBase('test_update_gui_slider'))
        suite.addTest(test_StrategyBase('test_update_gui_profit'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())