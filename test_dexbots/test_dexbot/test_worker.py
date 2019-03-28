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
                # 'dexbot-test1':{
                #     'account': 'dexbot-test1',
                #     'amount': 1.0,
                #     'center_price': 0.3,
                #     'center_price_depth': 0.0,
                #     'center_price_dynamic': True,
                #     'center_price_offset': False,
                #     'custom_expiration': False,
                #     'dynamic_spread': False,
                #     'dynamic_spread_factor': 1.0,
                #     'expiration_time': 157680000.0,
                #     'external_feed': False,
                #     'external_price_source': 'null',
                #     'fee_asset': 'TEST',
                #     'manual_offset': 0.0,
                #     'market': 'TEST/BTWTY',
                #     'market_depth_amount': 0.0,
                #     'module': 'dexbot.strategies.relative_orders',
                #     'partial_fill_threshold': 30.0,
                #     'price_change_threshold': 2.0,
                #     'relative_order_size': False,
                #     'reset_on_partial_fill': True,
                #     'reset_on_price_change': False,
                #     'spread': 5.0
                # },
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
    def test_init_workers(self):
        # for e in self.worker.__dict__.items():
        #     print(e)
        self.worker.init_workers(self.config)
    def test_update_notify(self):
        from dexbot.errors import NoWorkersAvailable
        self.assertRaises(NoWorkersAvailable,self.worker.update_notify)
    def test_on_block(self):
        self.worker.on_block(None)
    def test_on_market(self):
        from dexbot.strategies.base import StrategyBase
        self.worker.on_market(data)
    def test_on_account(self):
        self.worker.on_account(None)
    def test_add_worker(self):
        pass
    def test_run(self):
        pass
    def test_stop(self):
        pass
    def test_remove_worker(self):
        pass
    def test_remove_market(self):
        pass
    def test_remove_offline_worker(self):
        pass    
    def test_remove_offline_worker_data(self):
        pass
    def test_do_next_tick(self):
        pass
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        suite.addTest(test_WorkerInfrastructure('test_init_workers'))
        suite.addTest(test_WorkerInfrastructure('test_update_notify'))
        suite.addTest(test_WorkerInfrastructure('test_on_block'))
        suite.addTest(test_WorkerInfrastructure('test_on_market'))
        suite.addTest(test_WorkerInfrastructure('test_on_account'))
        suite.addTest(test_WorkerInfrastructure('test_add_worker'))
        suite.addTest(test_WorkerInfrastructure('test_run'))
        suite.addTest(test_WorkerInfrastructure('test_stop'))
        suite.addTest(test_WorkerInfrastructure('test_remove_worker'))
        suite.addTest(test_WorkerInfrastructure('test_remove_market'))
        suite.addTest(test_WorkerInfrastructure('test_remove_offline_worker'))
        suite.addTest(test_WorkerInfrastructure('test_remove_offline_worker_data'))
        suite.addTest(test_WorkerInfrastructure('test_do_next_tick'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())