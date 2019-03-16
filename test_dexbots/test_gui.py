import unittest
class test_gui(unittest.TestCase):
	def setUp(self):
		pass
	@unittest.skip('skip gui.py!')
	def test_gui_main(self):
		pass
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_gui('test_gui_main'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())