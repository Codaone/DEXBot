import unittest
import dexbot.controllers.strategy_controller
from dexbot.views.errors import gui_error

class test_strategy_controller(unittest.TestCase):
	@unittest.skip('skip ui test!')
	def setUp(self):
		self.view=gui_error(StrategyController())
		self.StrategyController=StrategyController(self.view,'configura','worker_controller','worker_data')
	def test_values(self):
		pass
	def test_elements(self):
		pass
	def tearDown(self):
		pass
class test_RelativeOrdersController(unittest.TestCase):
	def setUp(self):
		pass
	def test_values(self):
		pass
	def test_onchange_external_feed_input(self):
		pass
	def test_onchange_manual_offset_input(self):
		pass
	def test_onchange_dynamic_spread_input(self):
		pass
	def test_onchange_relative_order_size_input(self):
		pass
	def test_onchange_center_price_dynamic_input(self):
		pass
	def test_onchange_reset_on_partial_fill_input(self):
		pass
	def test_onchange_reset_on_price_change_input(self):
		pass
	def test_onchange_custom_expiration_input(self):
		pass
	def test_onchange_asset_labels(self):
		pass
	def test_order_size_input_to_relative(self):
		pass
	def test_order_size_input_to_static(self):
		pass
	def test_set_center_price_market_label(self):
		pass
	def test_set_quote_asset_label(self):
		pass
	def test_set_validation_errors(self):
		pass
	def tearDown(self):
		pass
class test_StaggeredOrdersController(unittest.TestCase):
	def setUp(self):
		pass
	def test_onchange_center_price_dynamic_input(self):
		pass
	def test_set_required_base(self):
		pass
	def test_set_required_quote(self):
		pass
	def test_validation_errors(self):
		pass
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_strategy_controller('test_values'))
		suite.addTest(test_strategy_controller('test_elements'))
		suite.addTest(test_RelativeOrdersController('test_values'))
		suite.addTest(test_RelativeOrdersController('test_onchange_external_feed_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_manual_offset_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_dynamic_spread_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_relative_order_size_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_center_price_dynamic_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_reset_on_partial_fill_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_reset_on_price_change_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_custom_expiration_input'))
		suite.addTest(test_RelativeOrdersController('test_onchange_asset_labels'))
		suite.addTest(test_RelativeOrdersController('test_order_size_input_to_relative'))
		suite.addTest(test_RelativeOrdersController('test_order_size_input_to_static'))
		suite.addTest(test_RelativeOrdersController('test_set_center_price_market_label'))
		suite.addTest(test_RelativeOrdersController('test_set_quote_asset_label'))
		suite.addTest(test_RelativeOrdersController('test_set_validation_errors'))
		suite.addTest(test_StaggeredOrdersController('test_onchange_center_price_dynamic_input'))
		suite.addTest(test_StaggeredOrdersController('test_set_required_base'))
		suite.addTest(test_StaggeredOrdersController('test_set_required_quote'))
		suite.addTest(test_StaggeredOrdersController('test_validation_errors'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())