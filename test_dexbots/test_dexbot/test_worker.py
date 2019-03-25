import unittest
from dexbot.worker import WorkerInfrastructure
class test_WorkerInfrastructure(unittest.TestCase):
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
        self.config=TEST_CONFIG
    def setUp(self):
        self.worker=WorkerInfrastructure(config=self.config,bitshares_instance=self.bitShares)
    def test_print(self):
        for e in self.worker.__dict__.items():
            print(e)
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        suite.addTest(test_WorkerInfrastructure('test_print'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())