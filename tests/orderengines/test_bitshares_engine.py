import pytest
from bitshares.dex import Dex
from bitshares.account import Account
from bitshares.asset import Asset
from bitshares.price import Order


# 1. Todo: place_market_sell_order(), 621 line,modify  # self.log.debug('Placed sell order {}'.format(sell_transaction))
# 2. Todo: convert_fee() 803 line, temp_market = Market(base=fee_asset, quote=Asset('1.3.0', bitshares_instance=self.bitshares))
# temp_market = Market(base=Asset(fee_asset, bitshares_instance=self.bitshares),
#                                      quote=Asset('1.3.0', bitshares_instance=self.bitshares)
#                                      , bitshares_instance=self.bitshares)
# 3. Todo:reason :set_shared_blockchain_instance
#   1. Todo:777 line add bitshares_instance=bitshares
#   2. Todo:770 line and ,bitshares_instance=None
#   3. Todo:158 line add ,bitshares_instance=self.bitshares
#   4. Todo:231 line add ,bitshares_instance=self.bitshares
#   5. Todo:233 line add ,bitshares_instance=self.bitshares
#   6. Todo:394 line add ,bitshares_instance=self.bitshares
#   7. todo:56  line modify ,bitshares_instance=self.bitshares

# 4. Todo:215 line self.base_asset Incorrect value
# 5. Todo:217 line self.quote_asset Incorrect value
# 6. todo:715 line if self.config['workers']['worker1']['market'] == order.market and self.account.openorders:
# 7. todo:429 line return self.filter_sell_orders(orders)  ,can'find filter_sell_orders()
# 8. todo:418 line return self.filter_buy_orders(orders) ,can'find filter_sell_orders()
# 9. todo:763 line copy.deepcopy()
# 10. todo:822 line order = Order(order_id, bitshares_instance=self.bitshares)
def test_balance(bitshares, accounts):
    a = Account('worker1', bitshares_instance=bitshares)
    assert a.balance('MYBASE') == 10000
    assert a.balance('MYQUOTE') == 2000
    assert a.balance('TEST') == 10000


def test_asset_base(bitshares, assets):
    a = Asset('MYBASE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000


def test_asset_quote(bitshares, assets):
    a = Asset('MYQUOTE', full=True, bitshares_instance=bitshares)
    assert a['dynamic_asset_data']['current_supply'] > 1000


def test_account_total_value(order_engines):
    a = order_engines.balance(order_engines.market['base']['symbol'])
    atv = order_engines.account_total_value(order_engines.market['base']['symbol'])
    assert atv == a


def test_account_total_value(order_engines, orders1):
    a = order_engines.balance(order_engines.market['base']['symbol'])
    atv = order_engines.account_total_value(order_engines.market['base']['symbol'])
    assert atv != a


def test_calculate_order_data(order_engines):
    base = order_engines.market['base']['symbol']
    quote = order_engines.market['quote']['symbol']

    order = Order("10 " + base, "1 " + quote, bitshares_instance=order_engines.bitshares)
    amount = 10
    price = 2
    order = order_engines.calculate_order_data(order, amount, price)
    assert 10 == order['quote']
    assert 20 == order['base']
    assert 2 == order['price']


def test_calculate_worker_value(order_engines):
    cwv = order_engines.calculate_worker_value(order_engines.market['base']['symbol'])
    assert cwv > 1000
    cwv = order_engines.calculate_worker_value(order_engines.market['quote']['symbol'])
    assert cwv > 2000



def test_cancel_all_orders(order_engines):
    o = order_engines.place_market_buy_order(1, 1, returnOrderId=True)

    assert order_engines.account.openorders != []
    order_engines.cancel_all_orders()
    order_engines.account.refresh()
    assert order_engines.account.openorders == []


def test_cancel_orders(order_engines):
    for i in range(1, 10):
        order_engines.place_market_buy_order(1 + i, 1, returnOrderId=True)
    assert order_engines.account.openorders != []
    for o in order_engines.account.openorders:
        order_engines.cancel_orders(o)
    order_engines.account.refresh()
    assert order_engines.account.openorders == []


def test_count_asset(order_engines):
    if order_engines.account.openorders == []:
        order_engines.place_market_buy_order(1, 10, returnOrderId=True)

    order_engines.account.refresh()

    assert order_engines.account.openorders != []

    balance = order_engines.account.balance(order_engines.market['base']['symbol'])

    s = 0
    for o in order_engines.account.openorders:
        s += float(o['base'])
    r = order_engines.count_asset(order_engines.account.openorders, order_engines.market['base']['symbol'])

    assert balance + s == r['base']


def test_get_allocated_assets(order_engines):
    if order_engines.account.openorders == []:
        order_engines.place_market_buy_order(1, 1)
    order_engines.account.refresh()
    assert order_engines.account.openorders != []

    s = 0
    for o in order_engines.account.openorders:
        s += float(o['base'])
    r = order_engines.get_allocated_assets(
        order_engines.account.openorders, order_engines.market['base']['symbol'])

    assert s == r['base']


def test_get_highest_own_buy_order(order_engines):
    ors = order_engines.account.openorders
    assert ors == []
    if ors == []:
        order_engines.place_market_buy_order(1, 1)
        order_engines.place_market_buy_order(1, 2)
        order_engines.place_market_buy_order(1, 3)
    order_engines.account.refresh()
    ors = order_engines.account.openorders
    o = order_engines.get_highest_own_buy_order(ors)
    assert o['price'] == 3


def test_get_market_orders(order_engines):
    order_engines.place_market_buy_order(1, 10)
    order_engines.account.refresh()
    own = order_engines.account.openorders
    market_orders = order_engines.get_market_orders(depth=50, updated=True)
    for o in own:
        assert o in market_orders


def test_get_order_cancellation_fee(order_engines):
    dex = Dex(bitshares_instance=order_engines.bitshares)
    fees = dex.returnFees()

    limit_order_cancel = fees['limit_order_cancel']['fee']
    fee = order_engines.get_order_cancellation_fee(order_engines.market['base']['symbol'])
    assert fee == limit_order_cancel
    fee = order_engines.get_order_cancellation_fee(order_engines.market['base']['symbol'])
    assert fee == limit_order_cancel
    fee = order_engines.get_order_cancellation_fee('TEST')
    assert fee == limit_order_cancel
    assert fee == limit_order_cancel


def test_get_order_creation_fee(order_engines):
    dex = Dex(bitshares_instance=order_engines.bitshares)
    fees = dex.returnFees()

    limit_order_create = fees['limit_order_create']['fee']
    fee = order_engines.get_order_creation_fee(order_engines.market['base']['symbol'])
    assert fee == limit_order_create
    fee = order_engines.get_order_creation_fee(order_engines.market['base']['symbol'])
    assert fee == limit_order_create


def test_get_own_buy_orders(order_engines, order_buy):
    orders = order_engines.account.openorders

    assert orders != []
    r = order_engines.get_own_buy_orders()

    assert orders == r


def test_get_own_sell_orders(order_engines, order_sell):
    sells = order_engines.account.openorders

    assert sells != []

    orders = order_engines.get_own_sell_orders()

    assert orders == sells


def test_get_own_spread(order_engines, orders1):
    spread = order_engines.get_own_spread()

    assert spread == 2 / 1 - 1


def test_get_updated_order(order_engines, order_part_filled):
    orders = order_engines.account.openorders
    for o in orders:
        c = order_engines.get_updated_order(o['id'])
        assert c == o


def test_execute(order_engines):
    # assert order_engines.account.openorders == []
    # order_engines.bitshares.blocking = "head"
    # assert order_engines.bitshares.blocking == "head"
    # order_engines.place_market_sell_order(20, 1.5)
    # order_engines.place_market_buy_order(10, 1.2)
    # order_engines.account.refresh()
    # assert order_engines.account.openorders != []
    # order_engines.execute()
    # assert order_engines.bitshares.blocking == False
    pass


def test_is_buy_order(order_engines, orders1):
    orders = order_engines.account.openorders
    for o in orders:
        if o['base']['symbol'] == order_engines.market['base']['symbol']:
            r = order_engines.is_buy_order(o)
            assert r == True


def test_is_current_market(order_engines):
    base_id = Asset(order_engines.market['base']['symbol'], bitshares_instance=order_engines.bitshares)['id']
    quote_id = Asset(order_engines.market['quote']['symbol'], bitshares_instance=order_engines.bitshares)['id']

    r = order_engines.is_current_market(base_asset_id=base_id, quote_asset_id=quote_id)
    assert r == True
    r = order_engines.is_current_market(quote_asset_id=quote_id, base_asset_id=base_id)
    assert r == True
    r = order_engines.is_current_market('CNY', 'USD')
    assert r == False


def test_is_sell_order(order_engines, orders1):
    orders = order_engines.get_all_own_orders()
    for o in orders:
        if o['base']['symbol'] == order_engines.market['quote']['symbol']:
            r = order_engines.is_sell_order(o)
            assert r == True


def test_place_market_buy_order(order_engines):
    o = order_engines.place_market_buy_order(10, 1)
    assert o['price'] == 1
    assert o['quote']['amount'] == 10


def test_place_market_sell_order(order_engines):
    o = order_engines.place_market_sell_order(10, 1)
    assert o['price'] == 1
    assert o['quote']['amount'] == 10


def test_retry_action(order_engines):
    r = order_engines.retry_action(order_engines.place_market_buy_order, 10, 1.1)

    order_engines.retry_action(order_engines.place_market_sell_order, 10, 2.2)

    order_engines.retry_action(order_engines.place_market_sell_order, 10, -1)

    order_engines.retry_action(order_engines.place_market_sell_order, -1, -1)


def test_account(order_engines, account_name):
    a = order_engines.account
    assert a.name == account_name


def test_balances(order_engines):
    base = order_engines.market['base']['symbol']
    quote = order_engines.market['quote']['symbol']
    r = order_engines.balances
    for b in r:
        if b['symbol'] == base:
            a = order_engines.account.balance(base)
            assert b == a
        if b['symbol'] == quote:
            a = order_engines.account.balance(quote)
            assert b == a


def test_get_all_own_orders(order_engines, orders1):
    orders = order_engines.get_all_own_orders()
    for o in orders:
        if o['base']['symbol'] == order_engines.market['base']['symbol']:
            assert o['price'] == 1


def test_all_own_orders(order_engines, orders1):
    orders = order_engines.all_own_orders
    for o in orders:
        if o['base']['symbol'] == order_engines.market['base']['symbol']:
            assert o['price'] == 1


def test_own_orders(order_engines, orders1):
    orders = order_engines.account.openorders
    r = order_engines.own_orders

    assert orders == r


def test_market(order_engines, symbol):
    assert order_engines.market['base']['symbol'] == symbol.split('/')[1]
    assert order_engines.market['quote']['symbol'] == symbol.split('/')[0]


def test_get_updated_limit_order(order_engines, orders1):
    ors = order_engines.get_all_own_orders()


def test_convert_asset(order_engines, orders1):
    r = order_engines.convert_asset(10, order_engines.market['base']['symbol'], order_engines.market['quote']['symbol'],
                                    bitshares_instance=order_engines.bitshares)
    assert r == 5


def test_convert_fee(order_engines):
    c = order_engines.market.ticker()['core_exchange_rate']

    r = order_engines.convert_fee(1, order_engines.market['base']['symbol'])

    assert float(c) == r


def test_get_order(order_engines, orders1):
    ors = order_engines.account.openorders

    for o in ors:
        r = order_engines.get_order(o['id'], return_none=False)
        # deleted
        assert r['price'] == o['price']
        assert r['base'] == o['base']
        assert r['quote'] == o['quote']
