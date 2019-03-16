import unittest
from dexbot import cli
class test_cli(unittest.TestCase):
	def setUp(self):
		pass
	@unittest.skip('skip cli!')
	def test_cli(self):
		cli.main()
	def tearDown(self):
		pass
#-------------------------test------------------
def suite():
	suite=unittest.TestSuite()
	suite.addTest(test_cli('test_cli'))
	return suite
if __name__=='__main__':
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())