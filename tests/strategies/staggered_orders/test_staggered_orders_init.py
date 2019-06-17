import copy
import logging
import pytest

from dexbot.strategies.staggered_orders import Strategy

# Turn on debug for dexbot logger
logger = logging.getLogger("dexbot")
logger.setLevel(logging.DEBUG)


###################
# __init__ tests here
###################


@pytest.mark.parametrize('spread, increment', [(1, 2), pytest.param(2, 2, marks=pytest.mark.xfail(reason="bug"))])
def test_spread_increment_check(bitshares, config, so_worker_name, spread, increment):
    """ Spread must be greater than increment
    """
    worker_name = so_worker_name
    incorrect_config = copy.deepcopy(config)
    incorrect_config['workers'][worker_name]['spread'] = spread
    incorrect_config['workers'][worker_name]['increment'] = increment
    worker = Strategy(config=incorrect_config, name=worker_name, bitshares_instance=bitshares)
    assert worker.disabled


def test_min_operational_depth(bitshares, config, so_worker_name):
    """ Operational depth should not be too small
    """
    worker_name = so_worker_name
    incorrect_config = copy.deepcopy(config)
    incorrect_config['workers'][worker_name]['operational_depth'] = 1
    worker = Strategy(config=incorrect_config, name=worker_name, bitshares_instance=bitshares)
    assert worker.disabled
