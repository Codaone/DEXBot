import unittest
from dexbot.strategies.base import StrategyBase
class test_StrategyBase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from bitshares import BitShares
        from bitshares.account import Account
        self.bitShares=BitShares('wss://node.testnet.bitshares.eu')
        self.bitShares.account='dexbot-test1'
        self.account=Account('dexbot-test1',bitshares_instance=self.bitShares)
    def setUp(self):
        self.strategy_base=StrategyBase('Worker 2',bitshares_instance=self.bitShares)
    def test_configure(self):
        from dexbot.strategies.base import ConfigElement
        base_config=StrategyBase.configure()
        for e in base_config:
            self.assertIsInstance(e,ConfigElement,'configura() not retrun a ConfigElement of object!')
            # print(e)
    def test_configure_details(self):
        from dexbot.strategies.base import ConfigElement
        config_details=StrategyBase.configure_details()
        for e in config_details:
            self.assertIsInstance(e,ConfigElement,'configura_details() not retrun a ConfigElement of object!')
    def test_account_total_value(self):
        balance_amount=self.account.balance('TEST')
        test_account_total_value=self.strategy_base.account_total_value('TEST')
        # self.assertEqual(balance_amount,test_account_total_value,"dexbot-test1's balance is wrong! ")
        print(balance_amount)
    def test_balance(self):
        balance_amount=self.account.balance('TEST')
        test_balance=self.strategy_base.balance('TEST')
        self.assertEqual(balance_amount,test_balance,"dexbot-test1's TEST balance is wrong!")
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
        total_account_balance=self.account.balance('TEST')
        total_account_calculate=self.strategy_base.calculate_worker_value('TEST')
        # self.assertEqual(total_account_balance,total_account_calculate,'calculate_worker_value() error!')
    def test_cancel_all_orders(self):
        from bitshares.market import Market
        market=Market('TEST:USD',bitshares_instance=self.bitShares)
        if market.bitshares.wallet.locked():
            market.bitshares.wallet.unlock('123')
        r=market.sell(
            1,
            10,
            expiration=60*60,
            account='dexbot-test1',
            returnOrderId=True
        )
        self.strategy_base.cancel_all_orders()
        ditc_openorders=market.accountopenorders(account='dexbot-test1')
        self.assertListEqual(ditc_openorders,[],'order is not cancel!') 
    def test_cancel_orders(self):
        from bitshares.market import Market
        market=Market('TEST:USD',bitshares_instance=self.bitShares)
        # if market.bitshares.wallet.locked():
        #     market.bitshares.wallet.unlock('123')
        # r=market.sell(
        #     1,
        #     10,
        #     expiration=60*60,
        #     account='dexbot-test1',
        #     returnOrderId=True
        # )
        # print(r['orderid'])
        flag=self.strategy_base.cancel_orders('123')
        self.assertEqual(flag,False,'cancel_orders()')
        # self.assertListEqual(ditc_openorders,[],'order is not cancel!') 
    def test_count_asset(self):
        r=self.strategy_base.count_asset()
    def test_get_allocated_assets(self):
        self.strategy_base.get_allocated_assets()
    def test_get_market_buy_orders(self):
        buy_orders=self.strategy_base.get_market_buy_orders()
        self.assertListEqual(buy_orders,[])
    def test_get_market_sell_orders(self):
        self.strategy_base.get_highest_market_buy_order()
    def test_get_highest_market_buy_order(self):
        self.strategy_base.get_highest_own_buy_order()
    def test_get_highest_own_buy_order(self):
        self.strategy_base.get_lowest_market_sell_order()
    def test_get_lowest_market_sell_order(self):
        self.strategy_base.get_lowest_own_sell_order()
    def test_get_lowest_own_sell_order(self):
        self.strategy_base.get_external_market_center_price('Binance')
    def test_get_external_market_center_price(self):
        self.strategy_base.get_market_center_price('Binance')
    def test_get_market_center_price(self):
        self.strategy_base.get_market_buy_price()
    def test_get_market_buy_price(self):
        self.strategy_base.get_market_orders()
    def test_get_market_orders(self):
        self.strategy_base.get_orderbook_orders()
    def test_get_orderbook_orders(self):
        self.strategy_base.get_market_sell_price()
    def test_get_market_sell_price(self):
        self.strategy_base.get_market_spread()
    def test_get_market_spread(self):
        self.strategy_base.get_market_spread()
    def test_get_order_cancellation_fee(self):
        self.strategy_base.get_order_cancellation_fee('TEST')
    def test_get_order_creation_fee(self):
        self.strategy_base.get_order_creation_fee('TEST')
    def test_filter_buy_orders(self):
        self.strategy_base.filter_buy_orders(['1223'])
    def test_filter_sell_orders(self):
        self.strategy_base.filter_sell_orders(['1223'])
    def test_get_own_buy_orders(self):
        self.strategy_base.get_own_buy_orders()
    def test_get_own_sell_orders(self):
        self.strategy_base.get_own_sell_orders()
    def test_get_own_spread(self):
        self.strategy_base.get_own_spread()
    def test_get_updated_order(self):
        self.strategy_base.get_updated_order(['123'])
    def test_execute(self):
        self.strategy_base.execute()
    def test_is_buy_order(self):
        self.strategy_base.is_buy_order(['123'])
    def test_is_current_market(self):
        self.strategy_base.is_current_market('1.3.13','1.3.14')
    def test_is_sell_order(self):
        self.strategy_base.is_sell_order(['123'])
    def test_pause(self):
        self.strategy_base.pause()
    def test_clear_all_worker_data(self):
        self.strategy_base.clear_all_worker_data()
    def test_place_market_buy_order(self):
        self.strategy_base.place_market_buy_order(1,0.1)
    def test_place_market_sell_order(self):
        self.strategy_base.place_market_sell_order(1,10)
    def test_retry_action(self):
        self.strategy_base.retry_action(action)
    def test_store_profit_estimation_data(self):
        self.strategy_base.store_profit_estimation_data()
    def test_get_profit_estimation_data(self):
        self.strategy_base.get_profit_estimation_data('ddd')
    def test_calc_profit(self):
        self.strategy_base.calc_profit()
    def test_write_order_log(self):
        self.strategy_base.write_order_log('worker 2',['23'])
    def test_account(self):
        self.strategy_base.account
    def test_quote_asset(self):
        self.strategy_base.quote_asset
    def test_all_own_orders(self):
        self.strategy_base.all_own_orders
    def test_get_own_orders(self):
        self.strategy_base.get_own_orders
    def test_market(self):
        self.strategy_base.market
    def test_convert_asset(self):
        self.strategy_base.convert_asset('TEST','USD')
    def test_convert_fee(self):
        self.strategy_base.convert_fee(0.001,'TEST')
    def test_get_order(self):
        self.strategy_base.get_order(123)
    def test_get_updated_limit_order(self):
        self.strategy_base.get_updated_limit_order([123])
    def test_purge_all_local_worker_data(self):
        self.strategy_base.purge_all_local_worker_data('worker 2')
    def test_sort_orders_by_price(self):
        self.strategy_base.sort_orders_by_price()
    def test_update_gui_slider(self):
        self.strategy_base.update_gui_slider()
    def test_update_gui_profit(self):
        self.strategy_base.update_gui_profit()
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        # suite.addTest(test_StrategyBase('test_configure'))
        # suite.addTest(test_StrategyBase('test_configure_details'))
        # suite.addTest(test_StrategyBase('test_account_total_value'))
        # suite.addTest(test_StrategyBase('test_balance'))
        # suite.addTest(test_StrategyBase('test_calculate_order_data'))
        # suite.addTest(test_StrategyBase('test_calculate_worker_value'))
        # suite.addTest(test_StrategyBase('test_cancel_all_orders'))
        # suite.addTest(test_StrategyBase('test_cancel_orders'))
        # suite.addTest(test_StrategyBase('test_count_asset'))
        # suite.addTest(test_StrategyBase('test_get_allocated_assets'))
        suite.addTest(test_StrategyBase('test_get_market_buy_orders'))
        # suite.addTest(test_StrategyBase('test_get_market_sell_orders'))
        # suite.addTest(test_StrategyBase('test_get_highest_market_buy_order'))
        # suite.addTest(test_StrategyBase('test_get_highest_own_buy_order'))
        # suite.addTest(test_StrategyBase('test_get_lowest_market_sell_order'))
        # suite.addTest(test_StrategyBase('test_get_lowest_own_sell_order'))
        # suite.addTest(test_StrategyBase('test_get_external_market_center_price'))
        # suite.addTest(test_StrategyBase('test_get_market_center_price'))
        # suite.addTest(test_StrategyBase('test_get_market_buy_price'))
        # suite.addTest(test_StrategyBase('test_get_market_orders'))
        # suite.addTest(test_StrategyBase('test_get_orderbook_orders'))
        # suite.addTest(test_StrategyBase('test_get_market_sell_price'))
        # suite.addTest(test_StrategyBase('test_get_market_spread'))
        # suite.addTest(test_StrategyBase('test_get_order_cancellation_fee'))
        # suite.addTest(test_StrategyBase('test_get_order_creation_fee'))
        # suite.addTest(test_StrategyBase('test_filter_buy_orders'))
        # suite.addTest(test_StrategyBase('test_filter_sell_orders'))
        # suite.addTest(test_StrategyBase('test_get_own_buy_orders'))
        # suite.addTest(test_StrategyBase('test_get_own_sell_orders'))
        # suite.addTest(test_StrategyBase('test_get_own_spread'))
        # suite.addTest(test_StrategyBase('test_get_updated_order'))
        # suite.addTest(test_StrategyBase('test_execute'))
        # suite.addTest(test_StrategyBase('test_is_buy_order'))
        # suite.addTest(test_StrategyBase('test_is_current_market'))
        # suite.addTest(test_StrategyBase('test_is_sell_order'))
        # suite.addTest(test_StrategyBase('test_pause'))
        # suite.addTest(test_StrategyBase('test_clear_all_worker_data'))
        # suite.addTest(test_StrategyBase('test_place_market_buy_order'))
        # suite.addTest(test_StrategyBase('test_place_market_sell_order'))
        # suite.addTest(test_StrategyBase('test_retry_action'))
        # suite.addTest(test_StrategyBase('test_store_profit_estimation_data'))
        # suite.addTest(test_StrategyBase('test_get_profit_estimation_data'))
        # suite.addTest(test_StrategyBase('test_calc_profit'))
        # suite.addTest(test_StrategyBase('test_write_order_log'))
        # suite.addTest(test_StrategyBase('test_account'))
        # suite.addTest(test_StrategyBase('test_quote_asset'))
        # suite.addTest(test_StrategyBase('test_all_own_orders'))
        # suite.addTest(test_StrategyBase('test_get_own_orders'))
        # suite.addTest(test_StrategyBase('test_market'))
        # suite.addTest(test_StrategyBase('test_convert_asset'))
        # suite.addTest(test_StrategyBase('test_convert_fee'))
        # suite.addTest(test_StrategyBase('test_get_order'))
        # suite.addTest(test_StrategyBase('test_get_updated_limit_order'))
        # suite.addTest(test_StrategyBase('test_purge_all_local_worker_data'))
        # suite.addTest(test_StrategyBase('test_sort_orders_by_price'))
        # suite.addTest(test_StrategyBase('test_update_gui_slider'))
        # suite.addTest(test_StrategyBase('test_update_gui_profit'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())