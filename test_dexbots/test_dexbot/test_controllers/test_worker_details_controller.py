import unittest
from dexbot.controllers.worker_details_controller import WorkerDetailsController
class test_WorkerDetailsController(unittest.TestCase):
	def setUp(self):
		pass
	def test_initialize_worker_data(self):
		pass
	def test_add_graph(self):
		pass
	def test_populate_table_from_csv(self):
		pass
	def test_populate_text_from_file(self):
		pass
	def test_status_file_not_found(self):
		pass
	def test_status_file_loaded(self):
		pass
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_WorkerDetailsController('test_initialize_worker_data'))
		suite.addTest(test_WorkerDetailsController('test_add_graph'))
		suite.addTest(test_WorkerDetailsController('test_populate_table_from_csv'))
		suite.addTest(test_WorkerDetailsController('test_populate_text_from_file'))
		suite.addTest(test_WorkerDetailsController('test_status_file_not_found'))
		suite.addTest(test_WorkerDetailsController('test_status_file_loaded'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())