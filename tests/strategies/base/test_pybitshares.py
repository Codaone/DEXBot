from bitshares.account import Account
from bitshares.asset import Asset


def test_worker_balance(bitshares,account):
    a = Account('base-worker', bitshares_instance=bitshares)
    assert a.balance('MYQUOTE') == 2000
    assert a.balance('MYBASE') == 10000


def test_asset_base(bitshares, assets):
    a = Asset('MYBASE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000
    assert a.symbol == 'MYBASE'


def test_asset_quote(bitshares, assets):
    a = Asset('MYQUOTE', full=True, bitshares_instance=bitshares)
    current_supply = a['dynamic_asset_data']['current_supply']
    if isinstance(current_supply, str):
        current_supply = float(current_supply)
    assert current_supply > 1000

    assert a.symbol == 'MYQUOTE'


def test_correct_asset_names(orders1):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = orders1
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['MYBASE', 'MYQUOTE']  # 'BASEB', 'QUOTEB'
    assert orders[0]['base']['asset']['symbol'] in symbols
