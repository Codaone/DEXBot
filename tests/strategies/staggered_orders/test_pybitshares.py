def test_correct_asset_names(orders1):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = orders1
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['BASEA', 'BASEB', 'QUOTEA', 'QUOTEB']
    assert orders[0]['base']['asset']['symbol'] in symbols
