import pytest
from bitshares.account import Account
from bitshares.market import Market
import time
from dexbot.orderengines.bitshares_engine import BitsharesOrderEngine


@pytest.fixture(scope='module')
def assets(create_asset):
    create_asset('MYBASE', 0)
    create_asset('MYQUOTE', 5)


@pytest.fixture(scope='module')
def accounts(assets, prepare_account):
    prepare_account({'MYBASE': 10000, 'MYQUOTE': 2000, 'TEST': 10000}, account='worker1')


@pytest.fixture(scope='module')
def symbol():
    return 'MYQUOTE/MYBASE'


@pytest.fixture(scope='module')
def account_name():
    return 'worker1'


@pytest.fixture(scope='module')
def config(bitshares, account_name, symbol):
    c = {
        'node': '{}'.format(bitshares.rpc.url),
        'workers': {
            account_name: {
                'account': account_name,
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
                'market': symbol,
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
    return c


@pytest.fixture
def order_engines(bitshares, accounts, account_name, symbol, config):
    account = Account(account_name, bitshares_instance=bitshares)
    market = Market(symbol, bitshares_instance=bitshares)
    oe = BitsharesOrderEngine(
        name=account_name,
        config=config,
        account=account,
        market=market,
        fee_asset_symbol=symbol.split('/')[0],
        bitshares_instance=bitshares,
        bitshares_bundle=None,
    )
    yield oe
    oe.cancel_all_orders()
    oe.bitshares.txbuffer.clear()
    oe.bitshares.bundle = False


@pytest.fixture(scope='function')
def orders1(order_engines):
    order_engines.place_market_buy_order(1, 1, returnOrderId=True)
    order_engines.place_market_sell_order(1, 2, returnOrderId=True)
    order_engines.place_market_buy_order(0.5, 2, returnOrderId=True)

    yield
    order_engines.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture(scope='function')
def order_sell(order_engines, account_name):
    order_engines.place_market_sell_order(10, 1)

    yield
    order_engines.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture(scope='function')
def order_buy(order_engines):
    order_engines.place_market_buy_order(100, 1)

    yield
    order_engines.cancel_all_orders()
    time.sleep(1.1)


@pytest.fixture(scope='function')
def order_part_filled(order_engines, order_buy, order_sell):
    yield
    order_engines.cancel_all_orders()
    time.sleep(1.1)
