from bitshares.account import Account
from bitshares.asset import Asset


def test_worker_balance(bitshares, account):
    a = Account('kh-worker', bitshares_instance=bitshares)
    assert a.balance('BASEA') == 10000
    assert a.balance('QUOTEA') == 100


def test_asset_base(bitshares, assets):
    a = Asset('BASEA', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000
    assert a.symbol == 'BASEA'


def test_asset_quote(bitshares, assets):
    a = Asset('QUOTEA', full=True, bitshares_instance=bitshares)
    current_supply = a['dynamic_asset_data']['current_supply']
    if isinstance(current_supply, str):
        current_supply = float(current_supply)
    assert current_supply > 1000

    assert a.symbol == 'QUOTEA'


def test_correct_asset_names(orders1):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = orders1
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['BASEA', 'BASEB', 'QUOTEA', 'QUOTEB']
    assert orders[0]['base']['asset']['symbol'] in symbols
