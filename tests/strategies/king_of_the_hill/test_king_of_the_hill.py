import logging
import pytest


log = logging.getLogger("dexbot")
log.setLevel(logging.DEBUG)


def test_amount_quote(worker):
    """ Test quote amount calculation
    """
    # config: 'sell_order_amount': 2.0,
    assert worker.amount_quote == 2

    worker.is_relative_order_size = True
    quote_balance = float(worker.balance(worker.market['quote']))
    amount = quote_balance * (worker.sell_order_amount / 100)
    assert worker.amount_quote == amount


def test_amount_base(worker):
    """ Test base amount calculation
    """
    # config: 'buy_order_amount': 1.0,
    assert worker.amount_base == 1

    worker.is_relative_order_size = True
    base_balance = float(worker.balance(worker.market['base']))
    amount = base_balance * (worker.buy_order_amount / 100)
    assert worker.amount_base == amount


def test_get_top_prices(other_orders, worker):
    """ Test if orders prices are calculated
    """
    orderbook = worker.market.orderbook(limit=1)
    top_price_bid = orderbook['bids'][0]['price']
    top_price_ask = orderbook['asks'][0]['price']
    worker.get_top_prices()

    assert pytest.approx(worker.top_buy_price) == top_price_bid
    assert pytest.approx(worker.top_sell_price) == top_price_ask


def test_place_order_correct_price(worker, other_orders):
    """ Test that buy order is placed at correct price. Similar to test_get_top_prices(), but with actual order
        placement
    """
    worker.get_top_prices()
    orderbook = worker.market.orderbook(limit=1)
    top_price_bid = orderbook['bids'][0]['price']
    top_price_ask = orderbook['asks'][0]['price']

    worker.place_order('buy')
    worker.place_order('sell')
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    own_buy_price = own_buy_orders[0]['price']
    own_sell_price = own_sell_orders[0]['price']

    # Our prices are on top
    assert own_buy_price > top_price_bid
    assert own_sell_price < top_price_ask

    # Difference between foreign top price and our price is in range of 10 BASE precision
    precision = worker.market['base']['precision']
    assert own_buy_price - top_price_bid < top_price_bid + 10 * 10 ** -precision
    assert top_price_ask - own_sell_price < top_price_ask - 10 * 10 ** -precision


def test_place_order_zero_price(worker):
    """ Check that worker goes into error if no prices are calculated
    """
    worker.sell_price = 0
    worker.place_order('sell')
    assert worker.disabled

    worker.disabled = False
    worker.buy_price = 0
    worker.place_order('buy')
    assert worker.disabled


def test_place_order_zero_amount(worker, monkeypatch):
    """ Check that worker goes into error if amounts are 0
    """
    worker.get_top_prices()

    monkeypatch.setattr(worker.__class__, 'amount_quote', 0)
    worker.place_order('sell')
    assert worker.disabled

    worker.disabled = False
    monkeypatch.setattr(worker.__class__, 'amount_base', 0)
    worker.place_order('buy')
    assert worker.disabled


def test_place_orders(worker2, other_orders):
    """ Test that orders are placed according to mode (buy, sell, buy + sell). Simple test, just make sure buy/sell
        order gets placed.
    """
    worker = worker2
    worker.place_orders()
    if worker.mode == 'both':
        assert len(worker.get_own_buy_orders()) == 1
        assert len(worker.get_own_sell_orders()) == 1
    elif worker.mode == 'buy':
        assert len(worker.get_own_buy_orders()) == 1
    elif worker.mode == 'sell':
        assert len(worker.get_own_sell_orders()) == 1


def test_place_orders_check_bounds(worker, other_orders_out_of_bounds):
    """ Test that orders aren't going out of bounds
    """
    worker.place_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    own_buy_price = own_buy_orders[0]['price']
    own_sell_price = own_sell_orders[0]['price']

    precision = min(worker.market['base']['precision'], worker.market['quote']['precision'])

    assert own_buy_price == pytest.approx(worker.upper_bound, rel=(10 ** -precision))
    assert own_sell_price == pytest.approx(worker.lower_bound, rel=(10 ** -precision))


def test_check_orders_fully_filled(worker, other_orders):
    """ When our order is fully filled, the strategy should place a new one
    """
    worker2 = other_orders

    worker.place_orders()

    # Own order fully filled
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('KOTH orders: {}'.format(worker.own_orders))

    to_sell = own_buy_orders[0]['quote']['amount']
    sell_price = own_buy_orders[0]['price'] / 1.01
    log.debug('Sell {} @ {}'.format(to_sell, sell_price))
    worker2.place_market_sell_order(to_sell, sell_price)

    to_buy = own_sell_orders[0]['base']['amount']
    buy_price = own_sell_orders[0]['price'] * 1.01
    log.debug('Buy {} @ {}'.format(to_buy, buy_price))
    worker2.place_market_buy_order(to_buy, buy_price)
    log.info('Filled KOTH orders from another account')
    log.debug('KOTH orders: {}'.format(worker.own_orders))

    worker.check_orders()

    # Expect new orders placed
    assert len(worker.own_orders) == 2


def test_check_orders_partially_filled(worker, other_orders):
    """ When our order is partially filled more than threshold, order should be replaced
    """
    worker2 = other_orders

    worker.place_orders()

    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('KOTH orders: {}'.format(worker.own_orders))

    to_sell = own_buy_orders[0]['quote']['amount'] * worker.partial_fill_threshold * 1.02
    sell_price = own_buy_orders[0]['price'] / 1.01
    log.debug('Sell {} @ {}'.format(to_sell, sell_price))
    worker2.place_market_sell_order(to_sell, sell_price)

    to_buy = own_sell_orders[0]['base']['amount'] * worker.partial_fill_threshold * 1.02
    buy_price = own_sell_orders[0]['price'] * 1.01
    log.debug('Buy {} @ {}'.format(to_buy, buy_price))
    worker2.place_market_buy_order(to_buy, buy_price)
    log.info('Filled KOTH orders from another account')
    log.debug('KOTH orders: {}'.format(worker.own_orders))

    worker.check_orders()

    # Expect new orders replaced with full-sized ones
    assert len(worker.own_orders) == 2
    for order in worker.own_orders:
        assert order['base']['amount'] == order['for_sale']['amount']


def test_check_orders_beaten_order_cancelled(worker, other_orders):
    """ Beaten order was cancelled, own order should be moved
    """
    worker2 = other_orders

    worker.place_orders()

    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('KOTH orders: {}'.format(worker.own_orders))

    own_top_bid_price_before = own_buy_orders[0]['price']
    own_top_ask_price_before = own_sell_orders[0]['price']

    foreign_sell_orders = worker2.get_own_sell_orders()
    foreign_buy_orders = worker2.get_own_buy_orders()
    worker2.cancel_orders([foreign_sell_orders[0], foreign_buy_orders[0]])

    worker.check_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    own_top_bid_price_after = own_buy_orders[0]['price']
    own_top_ask_price_after = own_sell_orders[0]['price']

    assert own_top_bid_price_after < own_top_bid_price_before
    assert own_top_ask_price_after > own_top_ask_price_before


def test_check_orders_new_order_above_our(worker, other_orders):
    """ Someone put order above ours, own order must be moved
    """
    worker2 = other_orders

    worker.place_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    log.debug('KOTH orders: {}'.format(worker.own_orders))

    own_top_bid_price_before = own_buy_orders[0]['price']
    own_top_ask_price_before = own_sell_orders[0]['price']

    # Place top orders from another account
    buy_price = own_top_bid_price_before * 1.1
    sell_price = own_top_ask_price_before / 1.1
    order = worker2.place_market_buy_order(10, buy_price)
    buy_price_actual = order['price']
    order = worker2.place_market_sell_order(10, sell_price)
    sell_price_actual = order['price'] ** -1

    worker.check_orders()
    own_buy_orders = worker.get_own_buy_orders()
    own_sell_orders = worker.get_own_sell_orders()
    own_top_bid_price_after = own_buy_orders[0]['price']
    own_top_ask_price_after = own_sell_orders[0]['price']

    assert len(worker.own_orders) == 2
    # Our orders are on top
    assert own_top_bid_price_after > buy_price_actual
    assert own_top_ask_price_after < sell_price_actual


def test_check_orders_no_looping(worker, other_orders):
    """ Make sure order placement is correct so check_orders() doesn't want to continuously move orders
    """
    worker.place_orders()
    ids = [order['id'] for order in worker.own_orders]

    worker.check_orders()
    ids_new = [order['id'] for order in worker.own_orders]

    assert ids == ids_new


def test_maintain_strategy(worker, other_orders):
    """ maintain_strategy() should run without errors.
        No logic is checked here because it's done inside other tests.
        The goal of this test is to make sure maintain_strategy() places orders
    """
    worker.maintain_strategy()
    assert len(worker.own_orders) == 2
