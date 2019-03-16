import unittest
from dexbot.strategies.king_of_the_hill import Strategy

class test_king_of_the_hill(unittest.TestCase):
	def setUp(self):
		pass
	def test_configure(self):
		pass
	def tearDown(self):
		pass
#---------------test-----------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_king_of_the_hill('test_configure'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())