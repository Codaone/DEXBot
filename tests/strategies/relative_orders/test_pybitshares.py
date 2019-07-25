from bitshares.account import Account
from bitshares.asset import Asset


def test_worker_balance(bitshares, account):
    a = Account('ro-worker', bitshares_instance=bitshares)
    assert a.balance('BASEA') == 10000
    assert a.balance('QUOTEA') == 100


def test_asset_base(bitshares, assets):
    a = Asset('BASEA', full=True, bitshares_instance=bitshares)
    # assert a['dynamic_asset_data']['current_supply'] > 1000
    assert a.symbol == 'BASEA'


def test_asset_quote(bitshares, assets):
    a = Asset('QUOTEA', full=True, bitshares_instance=bitshares)
    current_supply = a['dynamic_asset_data']['current_supply']
    if isinstance(current_supply, str):
        current_supply = float(current_supply)
    # assert current_supply > 1000

    assert a.symbol == 'QUOTEA'


def test_correct_asset_names(ro_orders1):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = ro_orders1
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['BASEA', 'BASEB', 'QUOTEA', 'QUOTEB']
    assert orders[0]['base']['asset']['symbol'] in symbols

def test_correct_asset_names(ro_worker):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = ro_worker
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['BASEA', 'BASEB', 'QUOTEA', 'QUOTEB']
    assert orders[0]['base']['asset']['symbol'] in symbols
    # todo:fixture不能创建worker错误代码：center_price = buy_price * math.sqrt(float(sell_price) / float(buy_price))
    # todo:ZeroDivisionError: float division by zero