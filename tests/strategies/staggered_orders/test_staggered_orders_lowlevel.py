import logging

# Turn on debug for dexbot logger
logger = logging.getLogger("dexbot")
logger.setLevel(logging.DEBUG)


###################
# Lower-level methods used by higher-level methods
###################


def test_cancel_orders_wrapper(orders4):
    worker = orders4

    # test real order
    orders = worker.own_orders
    before = len(orders)
    worker.cancel_orders_wrapper(orders[0])
    after = len(worker.own_orders)
    assert before - after == 1
    # test virtual order
    before = len(worker.virtual_orders)
    worker.cancel_orders_wrapper(worker.virtual_orders[0])
    after = len(worker.virtual_orders)
    assert before - after == 1


def test_place_virtual_buy_order(worker, init_empty_balances):
    worker.place_virtual_buy_order(100, 1)
    assert len(worker.virtual_orders) == 1
    assert worker.virtual_orders[0]['base']['amount'] == 100
    assert worker.virtual_orders[0]['for_sale']['amount'] == 100
    assert worker.virtual_orders[0]['quote']['amount'] == 100
    assert worker.virtual_orders[0]['price'] == 1


def test_place_virtual_sell_order(worker, init_empty_balances):
    worker.place_virtual_sell_order(100, 1)
    assert len(worker.virtual_orders) == 1
    assert worker.virtual_orders[0]['base']['amount'] == 100
    assert worker.virtual_orders[0]['for_sale']['amount'] == 100
    assert worker.virtual_orders[0]['quote']['amount'] == 100
    assert worker.virtual_orders[0]['price'] == 1
