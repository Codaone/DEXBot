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
            # 'bts0207':{
            #         'account': 'bts0207',
            #         'amount': 1,#order size:1.amount=0 ok.2.amount=None error 3.amount=9999999 error
            #         'center_price': 0,#
            #         'center_price_depth': 0,
            #         'center_price_dynamic': True,
            #         'center_price_offset': True,
            #         'custom_expiration': False,
            #         'dynamic_spread': False,
            #         'dynamic_spread_factor': 0,
            #         'expiration_time': 157680000.0,
            #         'external_feed': False,
            #         'external_price_source': 'null',
            #         'fee_asset': 'BTS',
            #         'manual_offset': 0.0,
            #         'market': 'BTS/CNY',
            #         'market_depth_amount': 0.0,
            #         'module': 'dexbot.strategies.relative_orders',
            #         'partial_fill_threshold': 30.0,
            #         'price_change_threshold': 2.0,
            #         'relative_order_size': False,
            #         'reset_on_partial_fill': True,
            #         'reset_on_price_change': False,
            #         'spread': 5.0
            #     }
            }   
        }   
        if self.bitShares.wallet.locked():
            self.bitShares.wallet.unlock('123')
        self.relative_strategy=Strategy(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares)    
        # for e in self.relative_strategy.__dict__.items():
        #         print(e)
    def setUp(self):
        # from bitshares import BitShares
        # from bitshares.account import Account
        #path='/Users/jacking/Documents/GitHub/stakemachine/config.yml'

        # print(self.relative_strategy.get_market_center_price())
        if self.bitShares.wallet.locked():
            self.bitShares.wallet.unlock('123')
        # self.relative_strategy=Strategy(name='dexbot-test1',config=TEST_CONFIG,bitshares_instance=self.bitShares)    
        # self.assertEqual(Account('dexbot-test1',bitshares_instance=self.bitShares),self.relative_strategy.account,'error')
        # self.relative_strategy=Strategy(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares)    
        # self.assertEqual(Account('bts0207',bitshares_instance=self.bitShares),Account(self.relative_strategy.account,bitshares_instance=self.bitShares),'error')
        # print('test node:There is not one buy order in TEST/USD market! Strategy() error! market.ticker() error')
    def test_configure(self):
        from dexbot.strategies.config_parts.relative_config import ConfigElement
        account=ConfigElement(key='account', type='string', default='', title='Account', description='BitShares account name for the bot to operate with', extra='')
        cf=Strategy.configure()
        self.assertIn(account,cf)
    def test_configure_details(self):
        # from dexbot.strategies.base import DetailElement
        cf_details=Strategy.configure_details()
        # print(cf_details)
        self.assertEqual(cf_details,[])
    def test_error(self):
        r=self.relative_strategy.error()
        self.assertEqual(None,r)
    def test_tick(self):
        r=self.relative_strategy.tick('d')
        self.assertEqual(None,r)
        print('[d] is not in use')
    def test_amount_to_sell(self):
        # print(self.relative_strategy.worker)
        # amount=1
        # c=self.relative_strategy.market['quote']
        # d=self.relative_strategy.market['quote']['precision']
        self.relative_strategy.sell_price=1
        # print(10 ** -5)
        # print(c,d)
        # from bitshares.asset import Asset
        # aa=Asset('1.3.0')
        # print(aa.symbol)
        # print(dict(aa))
        # print(aa.settlements)
        # if (amount < 2 * 10 ** -d or
        #         amount * self.sell_price < 2 * 10 ** -d):
        #     amount = 0
        
        print(self.relative_strategy.sell_price)
        amount_to_sell=self.relative_strategy.amount_to_sell
        print(amount_to_sell)
    def test_amount_to_buy(self):
        self.relative_strategy.buy_price=1
        amount_to_buy=self.relative_strategy.amount_to_buy
        print(amount_to_buy)
    def test_calculate_order_prices(self):
        calculate_order_prices=self.relative_strategy.calculate_order_prices()
        # print(calculate_order_prices)
        self.assertEqual(None,calculate_order_prices)
    def test_update_orders(self):
        r=self.relative_strategy.update_orders()
        self.assertEqual(None,r)
    def test_calculate_center_price(self):
        center_price = self.relative_strategy.calculate_center_price()
        self.assertIsNotNone(center_price,'error!')
        # print(center_price)
    def test_calculate_asset_offset(self):
        calculate_asset_offset=self.relative_strategy.calculate_asset_offset(center_price=1,order_ids=[],spread=0.5)
        # print(calculate_asset_offset)
        self.assertIsNotNone(calculate_asset_offset)
    def test_calculate_manual_offset(self):
        calculate_manual_offset=self.relative_strategy.calculate_manual_offset(center_price=0,manual_offset=0.1)
        # print(calculate_manual_offset)
        self.assertIsNotNone(calculate_manual_offset)
    def test_check_orders(self):
        r=self.relative_strategy.check_orders()
        self.assertIsNone(r)
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
