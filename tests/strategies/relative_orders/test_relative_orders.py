import logging

log = logging.getLogger("dexbot")
log.setLevel(logging.DEBUG)


def test_place_order_correct_price(ro_worker, other_orders):
    """ Test that buy order is placed at correct price.
    """
    worker = ro_worker
    orderbook = worker.market.orderbook(limit=1)
    top_price_bid = orderbook['bids'][0]['price']
    top_price_ask = orderbook['asks'][0]['price']
    a = worker.market.ticker().get('lowestAsk')
    assert top_price_ask == a

    worker.update_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()

    own_buy_price = own_buy_orders[0]['price']
    own_sell_price = own_sell_orders[0]['price']

    # Our prices are on top
    assert own_buy_price < top_price_bid
    assert own_sell_price < top_price_ask

    # Difference between foreign top price and our price is in range of 10 BASE precision
    precision = worker.market['base']['precision']
    assert own_buy_price - top_price_bid < top_price_bid + 10 * 10 ** -precision
    assert top_price_ask - own_sell_price < top_price_ask - 10 * 10 ** -precision


def test_place_order_zero_price(ro_worker):
    """ Check that worker goes into error if no prices are calculated
    """
    worker = ro_worker
    worker.sell_price = 0
    worker.place_market_sell_order(amount=0, price=0)
    assert worker.disabled

    worker.disabled = False
    worker.buy_price = 0
    worker.place_market_buy_order(amount=0, price=0)
    assert worker.disabled


def test_place_order_zero_amount(ro_worker):
    """ Check that worker goes into error if amounts are 0
    """
    worker = ro_worker

    worker.place_market_sell_order(amount=0, price=0)
    assert worker.disabled

    worker.disabled = False
    worker.place_market_buy_order(amount=0, price=0)
    assert worker.disabled


def test_check_orders_fully_filled(ro_worker, ro_worker1):
    """ When our order is fully filled, the strategy should place a new one
    """
    worker = ro_worker
    worker2 = ro_worker1
    worker2.cancel_all_orders()
    log.debug('worker1 account name: {}'.format(worker.account.name))
    log.debug('worker2 account name: {}'.format(worker2.account.name))

    worker.update_orders()

    # Own order fully filled
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('RO orders: {}'.format(worker.own_orders))
    log.debug('buy orders: {}'.format(own_buy_orders))
    log.debug('sell orders: {}'.format(own_sell_orders))
    for o in own_buy_orders:
        assert worker.is_buy_order(o) == True
    assert own_buy_orders != own_sell_orders
    assert len(worker.own_orders) == 2
    to_sell = own_buy_orders[0]['quote']['amount']
    sell_price = own_buy_orders[0]['price'] / 1.01
    log.debug('Sell {} @ {}'.format(to_sell, sell_price))
    worker2.place_market_sell_order(to_sell, sell_price)
    log.debug('RO orders: {}'.format(worker.own_orders))
    assert len(worker.own_orders) == 1

    to_buy = own_sell_orders[0]['base']['amount']
    buy_price = own_sell_orders[0]['price'] * 10
    log.debug('{}'.format(own_sell_orders))
    log.debug('Buy {} @ {}'.format(to_buy, buy_price))
    worker2.place_market_buy_order(to_buy, buy_price)
    log.info('Filled RO orders from another account')
    log.debug('RO orders: {}'.format(worker.own_orders))
    log.debug('worker2 orders: {}'.format(worker2.own_orders))

    assert len(worker.own_orders) == 0

    worker.update_orders()

    # Expect new orders placed
    assert len(worker.own_orders) == 2


def test_check_orders_partially_filled(ro_worker, ro_worker1):
    """ When our order is partially filled more than threshold, order should be replaced
    """
    worker2 = ro_worker1
    worker = ro_worker
    worker.update_orders()

    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('RO orders: {}'.format(worker.own_orders))

    to_sell = own_buy_orders[0]['quote']['amount'] * worker.partial_fill_threshold * 1.02
    sell_price = own_buy_orders[0]['price'] / 1.01
    log.debug('Sell {} @ {}'.format(to_sell, sell_price))
    worker2.place_market_sell_order(to_sell, sell_price)

    to_buy = own_sell_orders[0]['base']['amount'] * worker.partial_fill_threshold * 1.02
    buy_price = own_sell_orders[0]['price'] * 1.01
    log.debug('Buy {} @ {}'.format(to_buy, buy_price))
    worker2.place_market_buy_order(to_buy, buy_price)
    log.info('Filled RO orders from another account')
    log.debug('RO orders: {}'.format(worker.own_orders))

    worker.check_orders()

    # Expect new orders replaced with full-sized ones
    assert len(worker.own_orders) == 2
    for order in worker.own_orders:
        assert order['base']['amount'] == order['for_sale']['amount']


def test_check_orders_beaten_order_cancelled(ro_worker, ro_worker1):
    """ Beaten order was cancelled, own order should be place
    """
    worker2 = ro_worker1
    worker = ro_worker
    worker.update_orders()

    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('RO orders: {}'.format(worker.own_orders))

    own_top_bid_price_before = own_buy_orders[0]['price']
    own_top_ask_price_before = own_sell_orders[0]['price']

    foreign_sell_orders = worker2.get_own_sell_orders()
    foreign_buy_orders = worker2.get_own_buy_orders()
    worker2.cancel_orders([foreign_sell_orders[0], foreign_buy_orders[0]])

    worker.update_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    own_top_bid_price_after = own_buy_orders[0]['price']
    own_top_ask_price_after = own_sell_orders[0]['price']

    assert own_top_bid_price_after == own_top_bid_price_before
    assert own_top_ask_price_after == own_top_ask_price_before


def test_check_orders_new_order_above_our(ro_worker, ro_worker1):
    """ Someone put order above ours, own order not be moved
    """
    worker2 = ro_worker1
    worker = ro_worker
    worker.update_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('RO orders: {}'.format(worker.own_orders))

    own_top_bid_price_before = own_buy_orders[0]['price']
    own_top_ask_price_before = own_sell_orders[0]['price']

    # Place top orders from another account
    buy_price = own_top_bid_price_before * 1.1
    sell_price = own_top_ask_price_before / 1.1
    order = worker2.place_market_buy_order(10, buy_price)
    buy_price_actual = order['price']
    order = worker2.place_market_sell_order(10, sell_price)
    sell_price_actual = order['price'] ** -1

    worker.update_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    own_top_bid_price_after = own_buy_orders[0]['price']
    own_top_ask_price_after = own_sell_orders[0]['price']

    assert len(worker.own_orders) == 2
    # Our orders are on top
    assert own_top_bid_price_after < buy_price_actual
    assert own_top_ask_price_after < sell_price_actual


def test_update_orders(ro_worker):
    """ Make sure order placement is correct so update_orders()
    """
    worker = ro_worker
    worker.update_orders()
    ids = [order['id'] for order in worker.own_orders]

    worker.update_orders()
    ids_new = [order['id'] for order in worker.own_orders]
    assert ids != ids_new
