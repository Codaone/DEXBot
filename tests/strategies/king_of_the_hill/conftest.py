import pytest
import time
import logging

from dexbot.strategies.king_of_the_hill import Strategy
from dexbot.strategies.base import StrategyBase
import copy

log = logging.getLogger("dexbot")

MODES = ['both', 'buy', 'sell']


@pytest.fixture(scope='session')
def assets(create_asset):
    """ Create some assets with different precision
    """
    create_asset('BASEA', 3)
    create_asset('QUOTEA', 8)
    create_asset('BASEB', 8)
    create_asset('QUOTEB', 3)


@pytest.fixture(scope='module')
def kh_worker_name():
    """ Fixture to share king_of_the_hill Orders worker name
    """
    return 'kh-worker'


@pytest.fixture(scope='module')
def base_account(assets, prepare_account):
    """ Factory to generate random account with pre-defined balances
    """

    def func():
        account = prepare_account({'BASEA': 10000, 'QUOTEA': 100, 'BASEB': 10000, 'QUOTEB': 100, 'TEST': 1000})
        return account

    return func


@pytest.fixture(scope='module')
def account(base_account):
    """ Prepare worker account with some balance
    """
    return base_account()


@pytest.fixture(scope='module', params=[('QUOTEA', 'BASEA'), ('QUOTEB', 'BASEB')])
def config(request, bitshares, account, kh_worker_name):
    """ Define worker's config with variable assets

        This fixture should be function-scoped to use new fresh bitshares account for each test
    """
    worker_name = kh_worker_name
    config = {
        'node': '{}'.format(bitshares.rpc.url),
        'workers': {
            worker_name: {
                'account': '{}'.format(account),
                'buy_order_amount': 1.0,
                'buy_order_size_threshold': 0.0,
                'fee_asset': 'TEST',
                'lower_bound': 1.8,
                'market': '{}/{}'.format(request.param[0], request.param[1]),
                'min_order_lifetime': 60,
                'mode': 'both',
                'module': 'dexbot.strategies.king_of_the_hill',
                'relative_order_size': False,
                'sell_order_amount': 2.0,
                'sell_order_size_threshold': 0.0,
                'upper_bound': 1.2,
            }
        },
    }
    return config


@pytest.fixture(params=MODES)
def config_variable_modes(request, config, kh_worker_name):
    """ Test config which tests all modes
    """
    worker_name = kh_worker_name
    config = copy.deepcopy(config)
    config['workers'][worker_name]['mode'] = request.param
    return config


@pytest.fixture(scope='module')
def config_other_account(config, base_account, kh_worker_name):
    """ Config for other account which simulates foreign trader
    """
    config = copy.deepcopy(config)
    worker_name = kh_worker_name
    config['workers'][worker_name]['account'] = base_account()
    return config


@pytest.fixture
def base_worker(bitshares, kh_worker_name):
    """ Fixture to create KOTH worker
    """
    worker_name = kh_worker_name
    workers = []

    def _base_worker(config):
        worker = Strategy(name=worker_name, config=config, bitshares_instance=bitshares)
        log.info('Initialized {} on account {}'.format(worker_name, worker.account.name))
        workers.append(worker)
        return worker

    yield _base_worker
    for worker in workers:
        worker.cancel_all_orders()
        worker.bitshares.txbuffer.clear()
        worker.bitshares.bundle = False


@pytest.fixture
def worker(base_worker, config):
    """ Worker to test in single mode (for methods which not required to be tested against all modes)
    """
    worker = base_worker(config)
    return worker


@pytest.fixture
def worker2(base_worker, config_variable_modes):
    """ Worker to test all modes
    """
    worker = base_worker(config_variable_modes)
    return worker


@pytest.fixture
def orders1(worker):
    """ Place buy and sell order using worker account
    """
    worker.place_market_buy_order(1, 100, returnOrderId=True)
    worker.place_market_sell_order(1, 200, returnOrderId=True)
    yield worker
    worker.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture
def other_orders(bitshares, kh_worker_name, config_other_account):
    """ Place some orders from second account to simulate foreign trader
    """
    worker = StrategyBase(name=kh_worker_name, config=config_other_account, bitshares_instance=bitshares)
    worker.place_market_buy_order(10, 0.9)
    worker.place_market_buy_order(10, 1)
    worker.place_market_sell_order(10, 2.1)
    worker.place_market_sell_order(10, 2)

    yield worker
    worker.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture
def other_orders_out_of_bounds(other_orders):
    """ Extend other_orders by placing additional orders out of bounds
    """
    worker = other_orders
    worker.place_market_buy_order(10, worker.worker['upper_bound'] * 1.2)
    worker.place_market_sell_order(10, worker.worker['lower_bound'] / 1.2)
