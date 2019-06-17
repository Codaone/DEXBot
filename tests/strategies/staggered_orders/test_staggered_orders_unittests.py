import logging

# Turn on debug for dexbot logger
logger = logging.getLogger("dexbot")
logger.setLevel(logging.DEBUG)


###################
# Methods which not depends on other methods at all, can be tested separately
###################


def test_log_maintenance_time(worker):
    """ Should just not fail
    """
    worker.log_maintenance_time()


def test_calculate_min_amounts(worker):
    """ Min amounts should be greater than assets precision
    """
    worker.calculate_min_amounts()
    assert worker.order_min_base > 10 ** -worker.market['base']['precision']
    assert worker.order_min_quote > 10 ** -worker.market['quote']['precision']


def test_calculate_asset_thresholds(worker):
    """ Check asset threshold

        Todo: https://github.com/Codaone/DEXBot/issues/554
    """
    worker.calculate_asset_thresholds()
    assert worker.base_asset_threshold > 0
    assert worker.quote_asset_threshold > 0


def test_calc_buy_orders_count(worker):
    worker.increment = 0.01
    assert worker.calc_buy_orders_count(100, 90) == 11


def test_calc_sell_orders_count(worker):
    worker.increment = 0.01
    assert worker.calc_sell_orders_count(90, 100) == 11
