import math
import operator
import pytest

from grapheneapi.exceptions import RPCError
from bitshares.asset import Asset
from bitshares.account import Account


def test_balance(bitshares, accounts, account_name):
    a = Account(account_name, bitshares_instance=bitshares)
    assert a.balance('MYBASE') == 20000
    assert a.balance('MYQUOTE') == 5000
    assert a.balance('TEST') == 10000


def test_asset_base(bitshares, assets):
    a = Asset('MYBASE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000


def test_asset_quote(bitshares, assets):
    a = Asset('MYQUOTE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000


def test_market(bitshares_feed, market):
    assert market == bitshares_feed.market
    assert bitshares_feed.fetch_depth == 8
    assert bitshares_feed.ticker == bitshares_feed.market.ticker


def test_get_ticker(bitshares_feed):
    bitshares_feed.ticker


def test_get_limit_orders(bitshares_feed, orders1):
    # test default=1
    mkt_orders = bitshares_feed.get_limit_orders()
    assert len(mkt_orders) == 2
    # test depth=0
    mkt_orders = bitshares_feed.get_limit_orders(depth=0)
    assert len(mkt_orders) == 0
    # test depth=-1
    with pytest.raises(RPCError):
        mkt_orders = bitshares_feed.get_limit_orders(depth=-1)
    # test depth=10000
    with pytest.raises(RPCError):
        mkt_orders = bitshares_feed.get_limit_orders(depth=10000)


def test_get_orderbook_orders(bitshares_feed, orders1):
    # test default=1
    orderbook = bitshares_feed.get_orderbook_orders()
    assert len(orderbook['bids']) == 1
    assert len(orderbook['asks']) == 1
    # test depth=-1
    with pytest.raises(RPCError):
        orderbook = bitshares_feed.get_orderbook_orders(depth=-1)
    # test depth=0
    orderbook = bitshares_feed.get_orderbook_orders(depth=0)
    assert len(orderbook['bids']) == 0
    assert len(orderbook['asks']) == 0

    # test depth=60 orderbook() call has hard-limit of depth=50
    with pytest.raises(RPCError):
        orderbook = bitshares_feed.get_orderbook_orders(depth=60)


def test_filter_buy_orders(bitshares_feed, orders1):
    buy_orders = bitshares_feed.get_market_buy_orders(depth=10)
    price_list = []
    for o in buy_orders:
        if o['base']['symbol'] == bitshares_feed.market['base']['symbol']:
            price_list.append(o['price'])
    asc = sorted(price_list, reverse=False)
    desc = sorted(price_list, reverse=True)

    asc_orders = bitshares_feed.filter_buy_orders(buy_orders, sort='ASC')
    asc_orders_prices = []
    for o in asc_orders:
        asc_orders_prices.append(o['price'])

    desc_orders = bitshares_feed.filter_buy_orders(buy_orders, sort='DESC')
    desc_orders_prices = []
    for o in desc_orders:
        desc_orders_prices.append(o['price'])

    assert asc == asc_orders_prices
    assert desc == desc_orders_prices

    assert operator.eq(asc, asc_orders_prices)
    assert operator.eq(desc, desc_orders_prices)

@pytest.mark.xfail(reason='order.invert()-->graphenecommon/blockchainobject.py:262 self.refresh()')
def test_filter_sell_orders(bitshares_feed, orders1):
    sell_orders = bitshares_feed.get_market_sell_orders(depth=10)

    price_list = []
    for o in sell_orders:
        if o['base']['symbol'] != bitshares_feed.market['base']['symbol']:
            price_list.append(o['price'])
    asc = sorted(price_list, reverse=False)
    desc = sorted(price_list, reverse=True)

    asc_orders = bitshares_feed.filter_sell_orders(sell_orders, sort='ASC')
    asc_orders_prices = []
    for o in asc_orders:
        asc_orders_prices.append(o['price'])

    desc_orders = bitshares_feed.filter_sell_orders(sell_orders, sort='DESC')
    desc_orders_prices = []
    for o in desc_orders:
        desc_orders_prices.append(o['price'])

    assert asc == asc_orders_prices
    assert desc == desc_orders_prices

    assert operator.eq(asc, asc_orders_prices)
    assert operator.eq(desc, desc_orders_prices)


def test_get_highest_market_buy_order(bitshares_feed, orders1):
    buy_orders = bitshares_feed.get_market_buy_orders(depth=10)
    price_list = []
    for o in buy_orders:
        price_list.append(o['price'])
    max_price = max(price_list)

    highest = bitshares_feed.get_highest_market_buy_order(buy_orders)

    assert max_price == highest['price']

@pytest.mark.xfail(reason='order.invert()-->graphenecommon/blockchainobject.py:262 self.refresh()')
def test_get_lowest_market_sell_order(bitshares_feed, orders1):
    sell_orders = bitshares_feed.get_market_sell_orders(depth=10)
    price_list = []
    for o in sell_orders:
        price_list.append(o['price'])
    min_price = min(price_list)

    lowest = bitshares_feed.get_lowest_market_sell_order(sell_orders)

    assert min_price == lowest['price']


def test_get_market_buy_orders(bitshares_feed, orders1):
    buy_orders = bitshares_feed.get_market_buy_orders(depth=10)
    for o in buy_orders:
        assert o['base']['symbol'] == bitshares_feed.market['base']['symbol']

@pytest.mark.xfail(reason='order.invert()-->graphenecommon/blockchainobject.py:262 self.refresh()')
def test_get_market_sell_orders(bitshares_feed, orders1):
    os = bitshares_feed.get_limit_orders()
    for order in os:
        if order['base']['symbol'] == bitshares_feed.market['quote']['symbol']:
            assert order['base']['symbol'] == bitshares_feed.market['quote']['symbol']

    sell_orders = bitshares_feed.get_market_sell_orders(depth=1)
    for o in sell_orders:
        assert o['base']['symbol'] == bitshares_feed.market['quote']['symbol']


def test_get_market_buy_price(bitshares_feed):
    highestBid = bitshares_feed.market.ticker().get('highestBid')
    mkt_buy_price = bitshares_feed.get_market_buy_price(
        quote_amount=0, base_amount=0)

    assert float(highestBid) == mkt_buy_price


def test_get_market_sell_price(bitshares_feed):
    lowestAsk = bitshares_feed.market.ticker().get('lowestAsk')
    mkt_sell_price = bitshares_feed.get_market_sell_price(
        quote_amount=0, base_amount=0)

    assert float(lowestAsk) == mkt_sell_price


def test_get_market_center_price(bitshares_feed, orders1):
    lowestAsk = bitshares_feed.market.ticker().get('lowestAsk')
    highestBid = bitshares_feed.market.ticker().get('highestBid')
    if highestBid == 0:
        cp = None
    else:
        cp = highestBid * math.sqrt(lowestAsk / highestBid)
        cp = float(cp)
    center_price = bitshares_feed.get_market_center_price(
        base_amount=0, quote_amount=0, suppress_errors=False)
    assert cp == center_price


def test_get_market_spread(bitshares_feed):
    lowestAsk = bitshares_feed.market.ticker().get('lowestAsk')
    highestBid = bitshares_feed.market.ticker().get('highestBid')
    if highestBid == 0:
        spread = None
    else:
        spread = lowestAsk / highestBid - 1
        spread = float(spread)
    mkt_spread = bitshares_feed.get_market_spread(quote_amount=0, base_amount=0)

    assert spread == mkt_spread


def test_sort_orders_by_price(bitshares_feed, orders1):
    buy_orders = bitshares_feed.get_market_buy_orders(depth=10)
    price_list = []
    for o in buy_orders:
        if o['base']['symbol'] == bitshares_feed.market['base']['symbol']:
            price_list.append(o['price'])
    asc = sorted(price_list, reverse=False)
    desc = sorted(price_list, reverse=True)

    asc_orders = bitshares_feed.sort_orders_by_price(buy_orders, sort='ASC')
    asc_orders_prices = []
    for o in asc_orders:
        asc_orders_prices.append(o['price'])

    desc_orders = bitshares_feed.sort_orders_by_price(buy_orders, sort='DESC')
    desc_orders_prices = []
    for o in desc_orders:
        desc_orders_prices.append(o['price'])

    assert asc == asc_orders_prices
    assert desc == desc_orders_prices

    assert operator.eq(asc, asc_orders_prices)
    assert operator.eq(desc, desc_orders_prices)
