import pytest
import time
import copy
from dexbot.strategies.relative_orders import Strategy
from bitshares.market import Market


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
def base_account(assets, prepare_account, ro_worker_name):
    """ Factory to generate random account with pre-defined balances
    """

    def func():
        account = prepare_account({'BASEA': 10000, 'QUOTEA': 100, 'BASEB': 10000, 'QUOTEB': 100, 'TEST': 1000},
                                  account=ro_worker_name)
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
    time.sleep(1.1)


@pytest.fixture(scope='session')
def ro_worker_name():
    """ Fixture to share ro Orders worker name
    """
    return 'ro-worker'


@pytest.fixture(scope='module', params=[('QUOTEA', 'BASEA')])
def config(request, bitshares, account, ro_worker_name):
    """ Define worker's config with variable assets

        This fixture should be function-scoped to use new fresh bitshares account for each test
    """
    worker_name = ro_worker_name
    config = {
        'node': '{}'.format(bitshares.rpc.url),
        'workers': {
            worker_name: {
                'account': '{}'.format(account),
                'amount': 1.0,
                'center_price': 0.3,
                'center_price_depth': 0.0,
                'center_price_dynamic': False,
                'center_price_offset': False,
                'custom_expiration': False,
                'dynamic_spread': False,
                'dynamic_spread_factor': 1.0,
                'expiration_time': 157680000.0,
                'external_feed': False,
                'external_price_source': 'null',
                'fee_asset': 'TEST',
                'manual_offset': 0.0,
                'market': '{}/{}'.format(request.param[0], request.param[1]),
                'market_depth_amount': 0.0,
                'module': 'dexbot.strategies.relative_orders',
                'partial_fill_threshold': 30.0,
                'price_change_threshold': 2.0,
                'relative_order_size': False,
                'reset_on_partial_fill': True,
                'reset_on_price_change': False,
                'spread': 5.0
            }
        }
    }
    return config


@pytest.fixture(scope='module')
def ro_base_worker(bitshares, ro_worker_name):
    """ Fixture to share relative_orders object
    """
    worker_name = ro_worker_name
    workers = []

    def _base_worker(config):
        def _make_orders():
            market = Market('QUOTEA/BASEA', bitshares_instance=bitshares)
            market.buy(1, 10, returnOrderId=True, account=ro_worker_name)
            market.sell(2, 20, returnOrderId=True, account=ro_worker_name)

        _make_orders()
        worker = Strategy(
            name=worker_name,
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
def ro_worker(ro_base_worker, config):
    """ Worker to test in single mode (for methods which not required to be tested against all modes)
    """
    worker = ro_base_worker(config)
    return worker


@pytest.fixture(scope='function')
def ro_orders1(ro_worker):
    worker = ro_worker
    worker.place_market_buy_order(1, 100, returnOrderId=True)
    worker.place_market_sell_order(1, 200, returnOrderId=True)

    yield worker
    worker.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture(scope='session')
def ro_worker_name1():
    """ Fixture to share ro Orders worker name
    """
    return 'ro-worker1'


@pytest.fixture(scope='module')
def ro_base_worker1(bitshares, config1, ro_worker_name1):
    """ Fixture to share relative_orders object
    """
    worker_name = ro_worker_name1
    workers = []

    def _base_worker(config1):
        worker = Strategy(
            name=worker_name,
            config=config1,
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
def ro_worker1(ro_base_worker1, config1):
    """ Worker to test in single mode (for methods which not required to be tested against all modes)
    """
    worker = ro_base_worker1(config1)
    return worker


@pytest.fixture(scope='module', params=[('QUOTEA', 'BASEA')])
def config1(bitshares, config, account_other, ro_worker_name1, ro_worker_name):
    """ Define multiple worker's config with variable assets

    """
    worker_name = ro_worker_name1
    config = copy.deepcopy(config)
    a = config['workers'][ro_worker_name]
    a['account'] = 'other'
    b = {worker_name: a}
    config['workers'] = b
    return config


#######################################
# test single account multiple workers#
#######################################


@pytest.fixture(scope='session')
def multiple_worker_name():
    """ Fixture to share ro Orders worker name
    """
    return 'ro-worker-multiple'


@pytest.fixture(scope='module')
def multiple_base_worker(bitshares, single_account_config, multiple_worker_name):
    """ Fixture to share relative_orders object
    """
    worker_name = multiple_worker_name
    workers = []

    def _base_worker(single_account_config):
        worker = Strategy(
            name=worker_name,
            config=single_account_config,
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
def multiple_worker(multiple_base_worker, single_account_config):
    """ Worker to test in single mode (for methods which not required to be tested against all modes)
    """
    worker = multiple_base_worker(single_account_config)
    return worker


@pytest.fixture(scope='module')
def single_account_config(bitshares, config, multiple_worker_name, ro_worker_name):
    """ Define multiple worker's config with single account

    """
    worker_name = multiple_worker_name
    config = copy.deepcopy(config)
    a = config['workers'][ro_worker_name]
    b = {worker_name: a}
    config['workers'] = b
    return config
