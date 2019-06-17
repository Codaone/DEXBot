import pytest

from bitshares.account import Account
from bitshares.asset import Asset


@pytest.fixture(scope='module')
def assets(create_asset):
    create_asset('MYBASE', 0)
    create_asset('MYQUOTE', 5)


@pytest.fixture(scope='module')
def accounts(assets, prepare_account):
    prepare_account({'MYBASE': 10000, 'MYQUOTE': 2000}, account='worker1')
    prepare_account({'MYBASE': 20000, 'MYQUOTE': 5000, 'TEST': 10000}, account='worker2')


def test_worker_balance(bitshares, accounts):
    a = Account('worker2', bitshares_instance=bitshares)
    assert a.balance('MYBASE') == 20000
    assert a.balance('MYQUOTE') == 5000
    assert a.balance('TEST') == 10000


def test_asset_base(bitshares, assets):
    a = Asset('MYBASE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000
    assert a.symbol == 'MYBASE'


def test_asset_quote(bitshares, assets):
    a = Asset('MYQUOTE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000
    assert a.symbol == 'MYQUOTE'
