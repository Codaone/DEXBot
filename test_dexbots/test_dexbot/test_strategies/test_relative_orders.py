import unittest
from dexbot.strategies.relative_orders import Strategy
class test_Strategy(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from bitshares import BitShares
        from bitshares.account import Account
        self.bitShares=BitShares('wss://node.testnet.bitshares.eu')
        self.bitShares.account='dexbot-test1'
        self.account=Account('dexbot-test1',bitshares_instance=self.bitShares)    
    def setUp(self):
        self.relative_strategy=Strategy('Worker 2',bitshares_instance=self.bitShares)    
    def test_configure(self):
        cf=self.relative_strategy.configure()
        print(cf)
    def test_configure_details(self):
        pass
    def test_error(self):
        pass
    def test_tick(self):
        pass
    def test_amount_to_sell(self):
        pass
    def test_amount_to_buy(self):
        pass
    def test_calculate_order_prices(self):
        pass
    def test_update_orders(self):
        pass
    def test_calculate_center_price(self):
        pass
    def test_calculate_asset_offset(self):
        pass
    def test_calculate_manual_offset(self):
        pass
    def test_check_orders(self):
        pass
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        suite.addTest(test_Strategy('test_configure'))
        # suite.addTest(test_Strategy('test_configure_details'))
        # suite.addTest(test_Strategy('test_error'))
        # suite.addTest(test_Strategy('test_tick'))
        # suite.addTest(test_Strategy('test_amount_to_sell'))
        # suite.addTest(test_Strategy('test_amount_to_buy'))
        # suite.addTest(test_Strategy('test_calculate_order_prices'))
        # suite.addTest(test_Strategy('test_update_orders'))
        # suite.addTest(test_Strategy('test_calculate_center_price'))
        # suite.addTest(test_Strategy('test_calculate_asset_offset'))
        # suite.addTest(test_Strategy('test_calculate_manual_offset'))
        # suite.addTest(test_Strategy('test_check_orders'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
