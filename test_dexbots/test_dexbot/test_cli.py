import unittest
from bitshares import BitShares
from dexbot.worker import WorkerInfrastructure
class test_cli(unittest.TestCase):
	@unittest.skip('skip dexbot/cli.py!')
	def setUp(self):
		pass
	@unittest.skip('skip dexbot/cli.py!')
	def test_cli(self):
		pass
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_cli('test_cli'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())