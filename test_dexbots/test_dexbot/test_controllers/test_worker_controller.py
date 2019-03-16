import unittest
from dexbot.controllers.worker_controller import WorkerController
from dexbot.controllers.worker_controller import UppercaseValidator
class test_WorkerController(unittest.TestCase):
	def setUp(self):
		pass
	def test_strategies(self):
		pass
	def test_get_strategies(self):
		pass
	def test_add_private_key(self):
		pass
	def test_get_unique_worker_name(self):
		pass
	def test_get_strategy_module(self):
		pass
	def test_get_strategy_mode(self):
		pass
	def test_get_allow_instant_fill(self):
		pass
	def test_get_assets(self):
		pass
	def test_get_base_asset(self):
		pass
	def test_get_quote_asset(self):
		pass
	def test_get_account(self):
		pass
	def test_handle_save_dialog(self):
		pass
	def test_change_strategy_form(self):
		pass
	def test_validate_worker_name(self):
		pass
	def test_validate_asset(self):
		pass
	def test_validate_market(self):
		pass
	def test_validate_account_name(self):
		pass
	def test_validate_private_key(self):
		pass
	def test_validate_private_key_type(self):
		pass
	def test_validate_account_not_in_use(self):
		pass
	def test_validate_form(self):
		pass
	def test_handle_save(self):
		pass
	def tearDown(self):
		pass
class test_UppercaseValidator(unittest.TestCase):
	def setUp(self):
		pass
	def test_validate(self):
		pass
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_WorkerController('test_strategies'))
		suite.addTest(test_WorkerController('test_get_strategies'))
		suite.addTest(test_WorkerController('test_add_private_key'))
		suite.addTest(test_WorkerController('test_get_unique_worker_name'))
		suite.addTest(test_WorkerController('test_get_strategy_module'))
		suite.addTest(test_WorkerController('test_get_allow_instant_fill'))
		suite.addTest(test_WorkerController('test_get_assets'))
		suite.addTest(test_WorkerController('test_get_base_asset'))
		suite.addTest(test_WorkerController('test_get_quote_asset'))
		suite.addTest(test_WorkerController('test_get_account'))
		suite.addTest(test_WorkerController('test_handle_save_dialog'))
		suite.addTest(test_WorkerController('test_change_strategy_form'))
		suite.addTest(test_WorkerController('test_validate_worker_name'))
		suite.addTest(test_WorkerController('test_validate_asset'))
		suite.addTest(test_WorkerController('test_validate_market'))
		suite.addTest(test_WorkerController('test_validate_account_name'))
		suite.addTest(test_WorkerController('test_validate_private_key'))
		suite.addTest(test_WorkerController('test_validate_private_key_type'))
		suite.addTest(test_WorkerController('test_validate_account_not_in_use'))
		suite.addTest(test_WorkerController('test_validate_form'))
		suite.addTest(test_WorkerController('test_handle_save'))
		suite.addTest(test_UppercaseValidator('test_validate'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())