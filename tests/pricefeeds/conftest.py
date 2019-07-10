import pytest
import time

from dexbot.pricefeeds.bitshares_feed import BitsharesPriceFeed
from bitshares.market import Market


@pytest.fixture(scope='module')
def assets(create_asset):
    create_asset('MYBASE', 0)
    create_asset('MYQUOTE', 5)


@pytest.fixture(scope='session')
def account_name():
    """ Fixture to share  name
    """
    return 'bf'


@pytest.fixture(scope='module')
def market(bitshares, accounts, account_name):
    """ Create  market
    """
    market = Market('MYQUOTE/MYBASE', bitshares_instance=bitshares, account=account_name)
    return market


@pytest.fixture(scope='module')
def accounts(assets, prepare_account, account_name):
    prepare_account({'MYBASE': 20000, 'MYQUOTE': 5000, 'TEST': 10000}, account=account_name)


@pytest.fixture(scope='module')
def base_bitshares_feed(bitshares, market):
    """ create BitsharesPriceFeed object from dexbot.pricefeeds.bitshares_feed.py
    """

    def _base_bitshares_feed():
        bf = BitsharesPriceFeed(
            market=market, bitshares_instance=bitshares)
        return bf

    return _base_bitshares_feed


@pytest.fixture(scope='module')
def bitshares_feed(base_bitshares_feed):
    """ create BitsharesPriceFeed object from dexbot.pricefeeds.bitshares_feed.py
    """
    bf = base_bitshares_feed()
    return bf



@pytest.fixture(scope='module')
def orders1(market,account_name):
    """ Create some orders
    """
    os = []
    for i in range(1, 2):
        o = market.buy(1 + i, 1, returnOrderId=True, account=account_name)
        os.append(o['orderid'])
        o = market.sell(2 + i, 1, returnOrderId=True, account=account_name)
        os.append(o['orderid'])

    yield
    market.cancel(os, account=account_name)
    time.sleep(1.1)
