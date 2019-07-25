# todo:add self.buy_price=None @line 95
# TODO:add self.sell_price=None @line 96
# todo : 183 line: own_orders_ids = [order['id'] for order in self.get_own_orders]==>>self.get_own_orders()
# todo: line 249 , Event 'is_too_small_amounts' is not declared
import datetime




def test_maintain_strategy(worker):
    worker.cancel_all_orders()
    # Undefine market_center_price
    worker.market_center_price = None

    worker.maintain_strategy()
    assert worker.market_center_price == worker.center_price




def test_check_orders(worker):
    worker.check_orders()



def test_get_order_type(orders1):
    worker = orders1
    orders = worker.own_orders
    for o in orders:
        r = worker.get_order_type(o)
        if o['base']['symbol'] == worker.market['base']['symbol']:
            assert r == 'buy'
        else:
            assert r == 'sell'


def test_calc_order_prices(other_orders, orders1):
    worker = orders1
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


def test_place_order(worker):
    print(worker.buy_price)
    worker.buy_price = 1

    worker.place_order('buy')
    print(worker.orders)
    # worker.place_order('sell')
    # print(worker.orders)


def test_place_orders(worker):
    worker.place_orders()


def test_amount_quote(worker):
    # config: 'sell_order_amount': 2.0,
    sell_order_amount = worker.amount_quote
    assert sell_order_amount == 2


def test_amount_base(worker):
    # config: 'buy_order_amount': 1.0,
    buy_order_amount = worker.amount_base
    assert buy_order_amount == 1

    base_balance = float(worker.balance(worker.market['base']))
    amount = base_balance * (buy_order_amount / 100)
    worker.is_relative_order_size = True
    buy_order_amount = worker.amount_base

    assert buy_order_amount == amount
