# todo:add self.buy_price=None @line 95
# TODO:add self.sell_price=None @line 96
# todo : 183 line: own_orders_ids = [order['id'] for order in self.get_own_orders]==>>self.get_own_orders()
# todo: line 249 , Event 'is_too_small_amounts' is not declared

from dexbot.strategies.king_of_the_hill import Strategy
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)
import pytest
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


def test_maintain_strategy(kh):

    kh.maintain_strategy()


def test_check_orders(kh):
    kh.check_orders()


def test_get_order_type(kh, orders1):
    orders = kh.own_orders
    for o in orders:
        r = kh.get_order_type(o)
        if o['base']['symbol'] == kh.market['base']['symbol']:
            assert r == 'buy'
        else:
            assert r == 'sell'


def test_calc_order_prices(other_orders, kh, orders1):

    print('进入函数！')
    orders = kh.own_orders
    print('own_orders:', orders)
    buys = kh.filter_buy_orders(orders)
    print('buys:', buys)
    sells = kh.filter_sell_orders(orders, invert=True)
    print('sells:', sells)
    kh.calc_order_prices()
    buy_price = kh.buy_price
    sell_price = kh.sell_price
    print('buy_price:', buy_price)
    print('sell_price:', sell_price)

    for o in buys:
        new_quote = o['quote']['amount'] - 2 * \
                    10 ** -kh.market['quote']['precision']
        a_buy_price = min(
            o['base']['amount'] / new_quote, kh.upper_bound)
    assert a_buy_price == buy_price
    assert None == sell_price

def test_place_order(kh):
    print(kh.buy_price)
    kh.buy_price=1

    kh.place_order('buy')
    print(kh.orders)
    # kh.place_order('sell')
    # print(kh.orders)


def test_place_orders(kh):
    kh.place_orders()


def test_amount_quote(kh):
    # config: 'sell_order_amount': 2.0,
    sell_order_amount = kh.amount_quote
    assert sell_order_amount == 2


def test_amount_base(kh):
    # config: 'buy_order_amount': 1.0,
    buy_order_amount = kh.amount_base
    assert buy_order_amount == 1

    base_balance = float(kh.balance(kh.market['base']))
    amount = base_balance * (buy_order_amount / 100)
    kh.is_relative_order_size = True
    buy_order_amount = kh.amount_base

    assert buy_order_amount == amount
