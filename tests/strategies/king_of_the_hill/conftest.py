import pytest
import time

from dexbot.strategies.king_of_the_hill import Strategy
from bitshares.market import Market
import copy

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
def account_other(assets, prepare_account):
    prepare_account({'BASEA': 10000, 'QUOTEA': 100, 'BASEB': 10000, 'QUOTEB': 100, 'TEST': 1000},
                    account='other')


@pytest.fixture(scope='module')
def base_account(assets, prepare_account, kh_worker_name):
    """ Factory to generate random account with pre-defined balances
    """

    def func():
        account = prepare_account({'BASEA': 10000, 'QUOTEA': 100, 'BASEB': 10000, 'QUOTEB': 100, 'TEST': 1000},
                                  account=kh_worker_name)
        return account

    return func


@pytest.fixture(scope='module')
def account(base_account):
    """ Prepare worker account with some balance
    """
    return base_account()


@pytest.fixture(scope='function')
def other_orders(bitshares, account_other):
    market = Market('QUOTEA/BASEA', bitshares_instance=bitshares)
    ors_ids = []
    o = market.buy(1, 10, returnOrderId=True, account='other')
    ors_ids.append(o.get('orderid'))
    o = market.sell(2, 20, returnOrderId=True, account='other')
    ors_ids.append(o.get('orderid'))
    o = market.buy(1.5, 20, returnOrderId=True, account='other')
    ors_ids.append(o.get('orderid'))
    yield
    # if order filled then market.cancel() error
    market.cancel(ors_ids, account='other')
    time.sleep(1.1)


@pytest.fixture(scope='module')
def kh_worker_name():
    """ Fixture to share king_or_the_hill Orders worker name
    """
    return 'kh-worker'


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
                'lower_bound': 1,
                'market': '{}/{}'.format(request.param[0], request.param[1]),
                'min_order_lifetime': 60,
                'mode': 'both',
                'module': 'dexbot.strategies.king_of_the_hill',
                'relative_order_size': False,
                'sell_order_amount': 2.0,
                'sell_order_size_threshold': 0.0,
                'upper_bound': 0.001
            }
        }
    }
    return config


@pytest.fixture(scope='module')
def base_worker(bitshares, kh_worker_name):
    """ Fixture to share king_or_the_hill object
    """
    worker_name = kh_worker_name
    workers = []

    def _base_worker(config):
        worker = Strategy(
            name=kh_worker_name,
            config=config,
            bitshares_instance=bitshares
        )
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


@pytest.fixture(params=MODES)
def config_variable_modes(request, config, kh_worker_name):
    """ Test config which tests all modes
    """
    worker_name = kh_worker_name
    config = copy.deepcopy(config)
    config['workers'][worker_name]['mode'] = request.param
    return config


@pytest.fixture(scope='function')
def orders1(worker):
    worker.place_market_buy_order(1, 100, returnOrderId=True)
    worker.place_market_sell_order(1, 200, returnOrderId=True)

    # worker.place_market_buy_order(0.5, 200, returnOrderId=True)

    yield worker
    worker.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture(scope='function')
def orders2(worker2):
    worker2.place_market_buy_order(1, 100, returnOrderId=True)
    worker2.place_market_sell_order(1, 200, returnOrderId=True)

    # worker.place_market_buy_order(0.5, 200, returnOrderId=True)

    yield worker2
    worker2.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture
def worker2(base_worker, config_variable_modes):
    """ Worker to test all modes
    """
    print('进入worker2')
    worker = base_worker(config_variable_modes)
    return worker
