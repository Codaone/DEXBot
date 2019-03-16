import unittest
from dexbot.controllers.settings_controller import SettingsController
from PyQt5 import QtWidgets
from dexbot.views.settings import SettingsView
from dexbot.config import Config
class test_SettingsController(unittest.TestCase):
	def setUp(self):
		self.view=SettingsView()
		self.SettingsController=SettingsController(self.view)
	@unittest.skip('skip ui test!')
	def test_add_node(self):
		self.SettingsController.add_node()
	@unittest.skip('skip ui test!')
	def test_move_up(self):
		self.SettingsController.move_up()
	@unittest.skip('skip ui test!')
	def test_move_down(self):
		self.SettingsController.move_down()
	@unittest.skip('skip ui test!')
	def test_save_settings(self):
		self.SettingsController.save_settings()
	@unittest.skip('skip ui test!')
	def test_remove_node(self):
		self.SettingsController.remove_node()
	@unittest.skip('skip ui test!')
	def test_initialize_node_list(self):
		self.SettingsController.initialize_node_list()
	@unittest.skip('skip ui test!')
	def test_restore_defaults(self):
		self.SettingsController.restore_defaults()
	@unittest.skip('skip ui test!')
	def test_remove_empty_items(self):
		SettingsController.remove_empty_items()
	@unittest.skip('skip ui test!')
	def test_nodes(self):
		self.SettingsController.nodes()
	def tearDown(self):
		pass
#-------------------------test------------------
if __name__=='__main__':
	def suite():
		suite=unittest.TestSuite()
		suite.addTest(test_SettingsController('test_add_node'))
		suite.addTest(test_SettingsController('test_move_up'))
		suite.addTest(test_SettingsController('test_move_down'))
		suite.addTest(test_SettingsController('test_save_settings'))
		suite.addTest(test_SettingsController('test_remove_node'))
		suite.addTest(test_SettingsController('test_initialize_node_list'))
		suite.addTest(test_SettingsController('test_restore_defaults'))
		suite.addTest(test_SettingsController('test_remove_empty_items'))
		suite.addTest(test_SettingsController('test_nodes'))
		return suite
	runner=unittest.TextTestRunner(verbosity=2)
	runner.run(suite())