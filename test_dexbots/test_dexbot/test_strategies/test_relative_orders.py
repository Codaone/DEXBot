import unittest
from dexbot.strategies.relative_orders import Strategy
class test_Strategy(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from bitshares import BitShares
        from bitshares.account import Account
        nodeList=["wss://bts.open.icowallet.net/ws",
                "wss://bitshares.dacplay.org/ws",
                "wss://ws.gdex.top",
                "wss://api.bts.ai"
                ]
        # nodeList=["wss://node.testnet.bitshares.eu"]
        self.bitShares = BitShares(nodeList)#,nobroadcast=True)
        self.bitShares.account='bts0207'
        self.account=Account('bts0207',bitshares_instance=self.bitShares)
        # self.bitShares.account='dexbot-test1'
        # self.account=Account('dexbot-test1',bitshares_instance=self.bitShares)    
    def setUp(self):
        from bitshares import BitShares
        from bitshares.account import Account
        #path='/Users/jacking/Documents/GitHub/stakemachine/config.yml'
        TEST_CONFIG = {
            'node':'wss://bts.open.icowallet.net/ws',
            'workers':{
                'dexbot-test1':{
                    'account': 'dexbot-test1',
                    'amount': 1.0,
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
                    'fee_asset': 'TEST',
                    'manual_offset': 0.0,
                    'market': 'TEST/BTWTY',
                    'market_depth_amount': 0.0,
                    'module': 'dexbot.strategies.relative_orders',
                    'partial_fill_threshold': 30.0,
                    'price_change_threshold': 2.0,
                    'relative_order_size': False,
                    'reset_on_partial_fill': True,
                    'reset_on_price_change': False,
                    'spread': 5.0
                },
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
        # print(self.relative_strategy.get_market_center_price())
        if self.bitShares.wallet.locked():
            self.bitShares.wallet.unlock('123')
        # self.relative_strategy=Strategy(name='dexbot-test1',config=TEST_CONFIG,bitshares_instance=self.bitShares)    
        # self.assertEqual(Account('dexbot-test1',bitshares_instance=self.bitShares),self.relative_strategy.account,'error')
        self.relative_strategy=Strategy(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares)    
        self.assertEqual(Account('bts0207',bitshares_instance=self.bitShares),self.relative_strategy.account,'error')
        # print('test node:There is not one buy order in TEST/USD market! Strategy() error! market.ticker() error')
    def test_configure(self):
        cf=Strategy.configure()
        self.assertEqual(1,1,cf) #out put configure info
    def test_configure_details(self):
        cf_details=Strategy.configure_details()
        self.assertEqual(1,1, cf_details)
    def test_error(self):
        self.relative_strategy.error()
    def test_tick(self):
        self.relative_strategy.tick('d')
        print('[d] is not in use')
    def test_amount_to_sell(self):
        print(self.relative_strategy.worker)
        amount_to_sell=self.relative_strategy.amount_to_sell
    def test_amount_to_buy(self):
        amount_to_buy=self.relative_strategy.amount_to_buy
        print(amount_to_buy)
    def test_calculate_order_prices(self):
        calculate_order_prices=self.relative_strategy.calculate_order_prices()
        print(calculate_order_prices)
    def test_update_orders(self):
        self.relative_strategy.update_orders()
    def test_calculate_center_price(self):
        center_price = self.relative_strategy.calculate_center_price()
        self.assertIsNotNone(center_price,'error!')
        print(center_price)
    def test_calculate_asset_offset(self):
        calculate_asset_offset=self.relative_strategy.calculate_asset_offset(center_price=0,order_ids=[],spread=0.5)
        print(calculate_asset_offset)
    def test_calculate_manual_offset(self):
        calculate_manual_offset=self.relative_strategy.calculate_manual_offset(center_price=0,manual_offset=0.1)
        print(calculate_manual_offset)
    def test_check_orders(self):
        self.relative_strategy.check_orders()
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        suite.addTest(test_Strategy('test_configure'))
        suite.addTest(test_Strategy('test_configure_details'))
        suite.addTest(test_Strategy('test_error'))
        suite.addTest(test_Strategy('test_tick'))
        suite.addTest(test_Strategy('test_amount_to_sell'))
        suite.addTest(test_Strategy('test_amount_to_buy'))
        suite.addTest(test_Strategy('test_calculate_order_prices'))
        suite.addTest(test_Strategy('test_update_orders'))
        suite.addTest(test_Strategy('test_calculate_center_price'))
        suite.addTest(test_Strategy('test_calculate_asset_offset'))
        suite.addTest(test_Strategy('test_calculate_manual_offset'))
        suite.addTest(test_Strategy('test_check_orders'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
