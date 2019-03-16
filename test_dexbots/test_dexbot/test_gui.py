import unittest
from dexbot.gui import App
import sys
class test_App(unittest.TestCase):
	def setUp(self):
		pass
	@unittest.skip('skip dexbot/gui.py!')
	def test_main(self):
		app = App(sys.argv)
		sys.exit(app.exec_())
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_App('test_main'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())