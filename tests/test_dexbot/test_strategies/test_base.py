import pytest
from dexbot.strategies.base import StrategyBase
import logging
logging.basicConfig(format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s',
                    level=logging.WARNING)
class Test_StrategyBase:
    def setup_class(self):
        TEST_CONFIG = {
            'node':'wss://bts.open.icowallet.net/ws',
            'workers':{
                'bts0207':{
                    'account': 'bts0207',
                    'amount': 1,
                    'center_price': 0.3,
                    'center_price_depth': 0.0,
                    'center_price_dynamic': True,
                    'center_price_offset': False,
                    'custom_expiration': False,
                    'dynamic_spread': False,
                    'dynamic_spread_factor': 1.0,
                    'expiration_time': 157680000.0,
                    'external_feed': False,
                    'external_price_source': 'null',
                    'fee_asset': 'BTS',
                    'manual_offset': 0.0,
                    'market': 'BTS/CNY',
                    'market_depth_amount': 0.0,
                    'module': 'dexbot.strategies.relative_orders',
                    'partial_fill_threshold': 30.0,
                    'price_change_threshold': 2.0,
                    'relative_order_size': False,
                    'reset_on_partial_fill': True,
                    'reset_on_price_change': False,
                    'spread': 5.0
                }
            }
        } 
        from bitshares import BitShares
        nodeList=["wss://bts.open.icowallet.net/ws",
                "wss://bitshares.dacplay.org/ws",
                "wss://ws.gdex.top",
                "wss://api.bts.ai"
                ]
        self.bitShares = BitShares(nodeList)#,nobroadcast=True)
        if self.bitShares.wallet.locked():
            self.bitShares.wallet.unlock('123')
        self.strategy_base=StrategyBase(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares) 
    def teardown_class(self):
        pass
    def setup_method(self):
        pass
    def teardown_method(self):
        pass
    def test_configure(self):
        from dexbot.strategies.config_parts.base_config import ConfigElement
        base_config=StrategyBase.configure()
        logging.warning(base_config)
    # def test_configure_details(self):
    #     config_details=StrategyBase.configure_details()
    #     for e in config_details:
    #         self.assertIsInstance(e,ConfigElement,'configura_details() not retrun a ConfigElement of object!')
    # def test_account_total_value(self):
    #     balance_amount=self.account.balance('TEST')
    #     test_account_total_value=self.strategy_base.account_total_value('TEST')
    #     # self.assertEqual(balance_amount,test_account_total_value,"dexbot-test1's balance is wrong! ")
    #     print(balance_amount)
    # def test_balance(self):
    #     balance_amount=self.account.balance('TEST')
    #     test_balance=self.strategy_base.balance('TEST')
    #     self.assertEqual(balance_amount,test_balance,"dexbot-test1's TEST balance is wrong!")
    # def test_calculate_order_data(self):
    #     from bitshares.price import FilledOrder, Order, UpdateCallOrder
    #     from bitshares.amount import Amount, Asset
    #     order=Order(0.315, base="CNY", quote="BTS")
    #     amount=10
    #     price=2
    #     orders=self.strategy_base.calculate_order_data(order,amount,price)
    #     self.assertEqual(10,orders['quote'],'calculate_order_data() error!')
    #     self.assertEqual(20,orders['base'],'calculate_order_data() error!')
    #     self.assertEqual(2,orders['price'],'calculate_order_data() error!')
    # def test_calculate_worker_value(self):
    #     total_account_balance=self.account.balance('TEST')
    #     total_account_calculate=self.strategy_base.calculate_worker_value('TEST')
    #     # self.assertEqual(total_account_balance,total_account_calculate,'calculate_worker_value() error!')
    # def test_cancel_all_orders(self):
    #     from bitshares.market import Market
    #     market=Market('TEST:USD',bitshares_instance=self.bitShares)
    #     if market.bitshares.wallet.locked():
    #         market.bitshares.wallet.unlock('123')
    #     r=market.sell(
    #         1,
    #         10,
    #         expiration=60*60,
    #         account='dexbot-test1',
    #         returnOrderId=True
    #     )
    #     self.strategy_base.cancel_all_orders()
    #     ditc_openorders=market.accountopenorders(account='dexbot-test1')
    #     self.assertListEqual(ditc_openorders,[],'order is not cancel!') 
    # def test_cancel_orders(self):
    #     from bitshares.market import Market
    #     market=Market('TEST:USD',bitshares_instance=self.bitShares)
    #     # if market.bitshares.wallet.locked():
    #     #     market.bitshares.wallet.unlock('123')
    #     # r=market.sell(
    #     #     1,
    #     #     10,
    #     #     expiration=60*60,
    #     #     account='dexbot-test1',
    #     #     returnOrderId=True
    #     # )
    #     # print(r['orderid'])
    #     flag=self.strategy_base.cancel_orders('123')
    #     self.assertEqual(flag,False,'cancel_orders()')
    #     # self.assertListEqual(ditc_openorders,[],'order is not cancel!') 
    # def test_count_asset(self):
    #     r=self.strategy_base.count_asset()
    # def test_get_allocated_assets(self):
    #     self.strategy_base.get_allocated_assets()
    # def test_get_market_buy_orders(self):
    #     buy_orders=self.strategy_base.get_market_buy_orders()
    #     self.assertListEqual(buy_orders,[])
    # def test_get_market_sell_orders(self):
    #     self.strategy_base.get_highest_market_buy_order()
    # def test_get_highest_market_buy_order(self):
    #     self.strategy_base.get_highest_own_buy_order()
    # def test_get_highest_own_buy_order(self):
    #     self.strategy_base.get_lowest_market_sell_order()
    # def test_get_lowest_market_sell_order(self):
    #     self.strategy_base.get_lowest_own_sell_order()
    # def test_get_lowest_own_sell_order(self):
    #     self.strategy_base.get_external_market_center_price('Binance')
    # def test_get_external_market_center_price(self):
    #     self.strategy_base.get_market_center_price('Binance')
    # def test_get_market_center_price(self):
    #     self.strategy_base.get_market_buy_price()
    # def test_get_market_buy_price(self):
    #     self.strategy_base.get_market_orders()
    # def test_get_market_orders(self):
    #     self.strategy_base.get_orderbook_orders()
    # def test_get_orderbook_orders(self):
    #     self.strategy_base.get_market_sell_price()
    # def test_get_market_sell_price(self):
    #     self.strategy_base.get_market_spread()
    # def test_get_market_spread(self):
    #     self.strategy_base.get_market_spread()
    # def test_get_order_cancellation_fee(self):
    #     self.strategy_base.get_order_cancellation_fee('TEST')
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
if __name__=='__main__':
    path='/Users/jacking/Documents/GitHub/env/DEXBot/tests/test_dexbot/test_strategies/'
    pytest.main([path+'test_base.py'])