from dexbot.strategies.king_of_the_hill import Strategy
import logging
import pytest
from bitshares.account import Account
from bitshares.asset import Asset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


def test_maintain_strategy(worker2):
    worker2.cancel_all_orders()
    # Undefine market_center_price
    worker2.market_center_price = None

    worker2.maintain_strategy()
    assert worker2.market_center_price == worker2.center_price


def test_check_orders(worker2):
    worker2.check_orders()


def test_get_order_type(orders2):
    worker = orders2
    orders = worker.own_orders
    for o in orders:
        r = worker.get_order_type(o)
        if o['base']['symbol'] == worker.market['base']['symbol']:
            assert r == 'buy'
        else:
            assert r == 'sell'


def test_calc_order_prices(other_orders, orders2):
    worker = orders2
    print('进入函数！')
    orders = worker.own_orders
    print('own_orders:', orders)
    buys = worker.filter_buy_orders(orders)
    print('buys:', buys)
    sells = worker.filter_sell_orders(orders, invert=True)
    print('sells:', sells)
    worker.calc_order_prices()
    buy_price = worker.buy_price
    sell_price = worker.sell_price
    print('buy_price:', buy_price)
    print('sell_price:', sell_price)

    for o in buys:
        new_quote = o['quote']['amount'] - 2 * \
                    10 ** -worker.market['quote']['precision']
        a_buy_price = min(
            o['base']['amount'] / new_quote, worker.upper_bound)
    assert a_buy_price == buy_price
    assert None == sell_price


def test_place_order(worker2):
    print(worker2.buy_price)
    worker2.buy_price = 1

    worker2.place_order('buy')
    print(worker2.orders)
    # worker.place_order('sell')
    # print(worker.orders)


def test_place_orders(worker2):
    worker2.place_orders()


def test_amount_quote(worker2):
    # config: 'sell_order_amount': 2.0,
    sell_order_amount = worker2.amount_quote
    assert sell_order_amount == 2


def test_amount_base(worker2):
    # config: 'buy_order_amount': 1.0,
    buy_order_amount = worker2.amount_base
    assert buy_order_amount == 1

    base_balance = float(worker2.balance(worker2.market['base']))
    amount = base_balance * (buy_order_amount / 100)
    worker2.is_relative_order_size = True
    buy_order_amount = worker2.amount_base

    assert buy_order_amount == amount
