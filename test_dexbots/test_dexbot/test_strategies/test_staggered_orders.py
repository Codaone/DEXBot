import unittest
from dexbot.strategies.staggered_orders import Strategy


class test_Strategy(unittest.TestCase):
    def setUp(self):
        pass

    def test_configure(self):
        pass
    def test_configure_details(self):
        pass
    def test_maintain_strategy(self):
        pass
    def test_log_maintenance_time(self):
        pass
    def test_calculate_min_amounts(self):
        pass
    def test_calculate_asset_thresholds(self):
        pass
    def test_refresh_balances(self):
        pass
    def test_refresh_orders(self):
        pass
    def test_remove_outside_orders(self):
        pass
    def test_restore_virtual_orders(self):
        pass
    def test_replace_real_order_with_virtual(self):
        pass
    def test_replace_virtual_order_with_real(self):
        pass
    def test_store_profit_estimation_data(self):
        pass
    def test_allocate_asset(self):
        pass
    def test_increase_order_sizes(self):
        pass
    def test_check_partial_fill(self):
        pass
    def test_replace_partially_filled_order(self):
        pass
    def test_place_closer_order(self):
        pass
    def test_place_further_order(self):
        pass
    def test_place_highest_sell_order(self):
        pass
    def test_place_lowest_buy_order(self):
        pass
    def test_calc_buy_orders_count(self):
        pass
    def test_calc_sell_orders_count(self):
        pass
    def test_check_min_order_size(self):
        pass
    def test_place_virtual_buy_order(self):
        pass
    def test_place_virtual_sell_order(self):
        pass
    def test_cancel_orders_wrapper(self):
        pass
    def test_error(self):
        pass
    def test_pause(self):
        pass
    def test_purge(self):
        pass
    def test_tick(self):
        pass
    def tearDown(self):
        pass

# -------------------------test------------------
if __name__ == '__main__':
    def suite():
        suite = unittest.TestSuite()
        suite.addTest(test_Strategy('test_configure'))
        suite.addTest(test_Strategy('test_configure_details'))
        suite.addTest(test_Strategy('test_log_maintenance_time'))
        suite.addTest(test_Strategy('test_calculate_min_amounts'))
        suite.addTest(test_Strategy('test_calculate_asset_thresholds'))
        suite.addTest(test_Strategy('test_calculate_asset_thresholds'))
        suite.addTest(test_Strategy('test_refresh_orders'))
        suite.addTest(test_Strategy('test_remove_outside_orders'))
        suite.addTest(test_Strategy('test_restore_virtual_orders'))
        suite.addTest(test_Strategy('test_replace_real_order_with_virtual'))
        suite.addTest(test_Strategy('test_replace_virtual_order_with_real'))
        suite.addTest(test_Strategy('test_store_profit_estimation_data'))
        suite.addTest(test_Strategy('test_allocate_asset'))
        suite.addTest(test_Strategy('test_increase_order_sizes'))
        suite.addTest(test_Strategy('test_check_partial_fill'))
        suite.addTest(test_Strategy('test_replace_partially_filled_order'))
        suite.addTest(test_Strategy('test_place_closer_order'))
        suite.addTest(test_Strategy('test_place_further_order'))
        suite.addTest(test_Strategy('test_place_highest_sell_order'))
        suite.addTest(test_Strategy('test_place_lowest_buy_order'))
        suite.addTest(test_Strategy('test_calc_buy_orders_count'))
        suite.addTest(test_Strategy('test_calc_sell_orders_count'))
        suite.addTest(test_Strategy('test_check_min_order_size'))
        suite.addTest(test_Strategy('test_place_virtual_buy_order'))
        suite.addTest(test_Strategy('test_place_virtual_sell_order'))
        suite.addTest(test_Strategy('test_cancel_orders_wrapper'))
        suite.addTest(test_Strategy('test_error'))
        suite.addTest(test_Strategy('test_pause'))
        suite.addTest(test_Strategy('test_purge'))
        suite.addTest(test_Strategy('test_tick'))
        return suite
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
