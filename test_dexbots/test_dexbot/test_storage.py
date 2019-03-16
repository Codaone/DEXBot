import unittest
class test_Storage(unittest.TestCase):
    def setUp(self):
        pass
    def test_print(self):
        pass
    def tearDown(self):
        pass
#-------------------------test------------------
if __name__=='__main__':
    def suite():
        suite=unittest.TestSuite()
        suite.addTest(test_Storage('test_print'))
        return suite
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())