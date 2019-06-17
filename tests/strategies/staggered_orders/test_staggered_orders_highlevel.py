import logging
import math
import pytest

from dexbot.strategies.staggered_orders import VirtualOrder

# Turn on debug for dexbot logger
logger = logging.getLogger("dexbot")
logger.setLevel(logging.DEBUG)


###################
# Higher-level methods which depends on lower-level methods
###################


def test_refresh_balances(orders1):
    """ Check if balance refresh works
    """
    worker = orders1
    worker.refresh_balances()
    balance = worker.count_asset()

    assert worker.base_balance['amount'] > 0
    assert worker.quote_balance['amount'] > 0
    assert worker.base_total_balance == balance['base']
    assert worker.quote_total_balance == balance['quote']


def test_refresh_orders(orders1):
    """ Make sure orders refresh is working

        Note: this test doesn't checks orders sorting
    """
    worker = orders1
    worker.refresh_orders()
    assert worker.virtual_buy_orders[0]['base']['amount'] == 10
    assert worker.virtual_sell_orders[0]['base']['amount'] == 10
    assert worker.real_buy_orders[0]['base']['amount'] == 10
    assert worker.real_sell_orders[0]['base']['amount'] == 10
    assert len(worker.sell_orders) == 2
    assert len(worker.buy_orders) == 2


def test_check_min_order_size(worker):
    """ Make sure our orders are always match minimal allowed size
    """
    worker.calculate_min_amounts()
    if worker.order_min_quote > worker.order_min_base:
        # Limiting asset is QUOTE
        # Intentionally pass amount 2 times lower than minimum, the function should return increased amount
        corrected_amount = worker.check_min_order_size(worker.order_min_quote / 2, 1)
        assert corrected_amount == worker.order_min_quote
    else:
        # Limiting precision is BASE, at price=1 amounts are the same, so pass 2 times lower amount
        corrected_amount = worker.check_min_order_size(worker.order_min_base / 2, 1)
        assert corrected_amount >= worker.order_min_quote

    # Place/cancel real order to ensure no errors from the node
    worker.place_market_sell_order(corrected_amount, 1, returnOrderId=False)
    worker.cancel_all_orders()


def test_remove_outside_orders(orders1):
    """ All orders in orders1 fixture are outside of the range, so remove_outside_orders() should cancel all
    """
    worker = orders1
    worker.refresh_orders()
    assert worker.remove_outside_orders(worker.sell_orders, worker.buy_orders)
    assert len(worker.sell_orders) == 0
    assert len(worker.buy_orders) == 0


def test_restore_virtual_orders(orders2):
    """ Very basic test, checks if number of virtual orders at least 2
    """
    worker = orders2
    worker.restore_virtual_orders()
    assert len(worker.virtual_orders) >= 2


def test_replace_real_order_with_virtual(orders2):
    """ Try to replace 2 furthest orders with virtual, then compare difference
    """
    worker = orders2
    worker.virtual_orders = []
    num_orders_before = len(worker.real_buy_orders) + len(worker.real_sell_orders)
    worker.replace_real_order_with_virtual(worker.real_buy_orders[-1])
    worker.replace_real_order_with_virtual(worker.real_sell_orders[-1])
    worker.refresh_orders()
    num_orders_after = len(worker.real_buy_orders) + len(worker.real_sell_orders)
    assert num_orders_before - num_orders_after == 2
    assert len(worker.virtual_orders) == 2


def test_replace_virtual_order_with_real(orders3):
    """ Try to replace 2 furthest virtual orders with real orders
    """
    worker = orders3
    num_orders_before = len(worker.virtual_orders)
    num_real_orders_before = len(worker.own_orders)
    assert worker.replace_virtual_order_with_real(worker.virtual_buy_orders[-1])
    assert worker.replace_virtual_order_with_real(worker.virtual_sell_orders[-1])
    num_orders_after = len(worker.virtual_orders)
    num_real_orders_after = len(worker.own_orders)
    assert num_orders_before - num_orders_after == 2
    assert num_real_orders_after - num_real_orders_before == 2


def test_store_profit_estimation_data(worker, storage_db):
    """ Check if storing of profit estimation data works
    """
    worker.refresh_balances()
    worker.store_profit_estimation_data(force=True)
    account = worker.worker.get('account')
    data = worker.get_recent_balance_entry(account, worker.worker_name, worker.base_asset, worker.quote_asset)
    assert data.center_price == worker.market_center_price
    assert data.base_total == worker.base_total_balance
    assert data.quote_total == worker.quote_total_balance


def test_check_partial_fill(worker, partially_filled_order):
    """ Test that check_partial_fill() can detect partially filled order
    """
    is_not_partially_filled = worker.check_partial_fill(partially_filled_order, fill_threshold=0)
    assert not is_not_partially_filled
    is_not_partially_filled = worker.check_partial_fill(partially_filled_order, fill_threshold=90)
    assert is_not_partially_filled


def test_replace_partially_filled_order(worker, partially_filled_order):
    """ Test if replace_partially_filled_order() do correct replacement
    """
    worker.replace_partially_filled_order(partially_filled_order)
    new_order = worker.own_orders[0]
    assert new_order['base']['amount'] == new_order['for_sale']['amount']


def test_place_lowest_buy_order(worker2):
    """ Check if placement of lowest buy order works in general
    """
    worker = worker2
    worker.refresh_balances()
    worker.place_lowest_buy_order(worker.base_balance)
    worker.refresh_orders()

    # Expect furthest order price to be less than increment x2
    assert worker.buy_orders[-1]['price'] < worker.lower_bound * (1 + worker.increment * 2)


def test_place_highest_sell_order(worker2):
    """ Check if placement of highest sell order works in general
    """
    worker = worker2
    worker.refresh_balances()
    worker.place_highest_sell_order(worker.quote_balance)
    worker.refresh_orders()

    # Expect furthest order price to be less than increment x2
    assert worker.sell_orders[-1]['price'] ** -1 > worker.upper_bound / (1 + worker.increment * 2)


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_real_or_virtual(orders5, asset):
    """ Closer order may be real or virtual, depending on distance from the center and operational_depth

        1. Closer order within operational depth must be real
        2. Closer order outside of operational depth must be virtual if previous order is virtual
        3. Closer order outside of operational depth must be real if previous order is real
    """
    worker = orders5
    if asset == 'base':
        virtual_outside = worker.virtual_buy_orders[-1]
        virtual_within = worker.virtual_buy_orders[0]
        real_outside = worker.real_buy_orders[-1]
        real_within = worker.real_buy_orders[0]
    elif asset == 'quote':
        virtual_outside = worker.virtual_sell_orders[-1]
        virtual_within = worker.virtual_sell_orders[0]
        real_outside = worker.real_sell_orders[-1]
        real_within = worker.real_sell_orders[0]

    closer_order = worker.place_closer_order(asset, virtual_outside, place_order=True)
    assert isinstance(
        closer_order, VirtualOrder
    ), "Closer order outside of operational depth must be virtual if previous order is virtual"

    # When self.returnOrderId is True, place_market_xxx_order() will return bool
    closer_order = worker.place_closer_order(asset, virtual_within, place_order=True)
    assert closer_order, "Closer order within operational depth must be real"

    closer_order = worker.place_closer_order(asset, real_outside, place_order=True)
    assert closer_order, "Closer order outside of operational depth must be real if previous order is real"

    closer_order = worker.place_closer_order(asset, real_within, place_order=True)
    assert closer_order, "Closer order within operational depth must be real"


@pytest.mark.xfail(reason='https://github.com/bitshares/python-bitshares/issues/227')
@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_price_amount(orders5, asset):
    """ Test that closer order price and amounts are correct
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    worker.returnOrderId = True
    closer_order = worker.place_closer_order(asset, order, place_order=True)

    # Test for correct price
    assert closer_order['price'] == order['price'] * (1 + worker.increment)

    # Test for correct amount
    if (
        worker.mode == 'mountain'
        or (worker.mode == 'buy_slope' and asset == 'quote')
        or (worker.mode == 'sell_slope' and asset == 'base')
    ):
        assert closer_order['quote']['amount'] == order['quote']['amount']
    elif (
        worker.mode == 'valley'
        or (worker.mode == 'buy_slope' and asset == 'base')
        or (worker.mode == 'sell_slope' and asset == 'quote')
    ):
        assert closer_order['base']['amount'] == order['base']['amount']
    elif worker.mode == 'neutral':
        assert closer_order['base']['amount'] == order['base']['amount'] * math.sqrt(1 + worker.increment)


@pytest.mark.xfail(reason='https://github.com/bitshares/python-bitshares/issues/227')
@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_no_place_order(orders5, asset):
    """ Test place_closer_order() with place_order=False kwarg
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    closer_order = worker.place_closer_order(asset, order, place_order=False)
    worker.place_closer_order(asset, order, place_order=True)
    worker.refresh_orders()

    if asset == 'base':
        real_order = worker.buy_orders[0]
        price = real_order['price']
        amount = real_order['quote']['amount']
    elif asset == 'quote':
        real_order = worker.sell_orders[0]
        price = real_order['price'] ** -1
        amount = real_order['base']['amount']

    assert closer_order['price'] == price
    assert closer_order['amount'] == amount


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_allow_partial_hard_limit(orders2, asset):
    """ Test place_closer_order with allow_partial=True when avail balance is less than minimal allowed order size
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        price = order['price']
        # Pretend we have balance smaller than hard limit
        worker.base_balance['amount'] = worker.check_min_order_size(0, price) / 2
    elif asset == 'quote':
        order = worker.sell_orders[0]
        price = order['price'] ** -1
        worker.quote_balance['amount'] = worker.check_min_order_size(0, price) / 2

    num_orders_before = len(worker.own_orders)
    worker.place_closer_order(asset, order, place_order=True, allow_partial=True)
    num_orders_after = len(worker.own_orders)
    # Expect that order was not placed
    assert num_orders_before == num_orders_after


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_allow_partial_soft_limit(orders2, asset):
    """ Test place_closer_order with allow_partial=True when avail balance is less than self.partial_fill_threshold
        restriction
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        # Pretend we have balance smaller than soft limit
        worker.base_balance['amount'] = order['base']['amount'] * worker.partial_fill_threshold / 1.1
    elif asset == 'quote':
        order = worker.sell_orders[0]
        worker.quote_balance['amount'] = order['base']['amount'] * worker.partial_fill_threshold / 1.1

    num_orders_before = len(worker.own_orders)
    worker.place_closer_order(asset, order, place_order=True, allow_partial=True)
    num_orders_after = len(worker.own_orders)
    # Expect that order was not placed
    assert num_orders_before == num_orders_after


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_allow_partial(orders2, asset):
    """ Test place_closer_order with allow_partial=True when avail balance is more than self.partial_fill_threshold
        restriction (enough for partial order)
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        worker.base_balance['amount'] = order['base']['amount'] * worker.partial_fill_threshold * 2
    elif asset == 'quote':
        order = worker.sell_orders[0]
        worker.quote_balance['amount'] = order['base']['amount'] * worker.partial_fill_threshold * 2

    num_orders_before = len(worker.own_orders)
    worker.place_closer_order(asset, order, place_order=True, allow_partial=True)
    num_orders_after = len(worker.own_orders)
    # Expect order placed
    assert num_orders_after - num_orders_before == 1


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_not_allow_partial(orders2, asset):
    """ Test place_closer_order with allow_partial=False
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        worker.base_balance['amount'] = order['base']['amount'] * worker.partial_fill_threshold * 2
    elif asset == 'quote':
        order = worker.sell_orders[0]
        worker.quote_balance['amount'] = order['base']['amount'] * worker.partial_fill_threshold * 2

    num_orders_before = len(worker.own_orders)
    worker.place_closer_order(asset, order, place_order=True, allow_partial=False)
    num_orders_after = len(worker.own_orders)
    # Expect that order was not placed
    assert num_orders_before == num_orders_after


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_own_asset_limit(orders5, asset):
    """ Place closer order with own_asset_limit, test that amount of a new order is matching limit
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    limit = order['base']['amount'] / 2

    worker.returnOrderId = True
    closer_order = worker.place_closer_order(asset, order, place_order=True, own_asset_limit=limit)
    assert closer_order['base']['amount'] == limit


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_opposite_asset_limit(orders5, asset):
    """  Place closer order with opposite_asset_limit, test that amount of a new order is matching limit
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    limit = order['quote']['amount'] / 2

    worker.returnOrderId = True
    closer_order = worker.place_closer_order(asset, order, place_order=True, opposite_asset_limit=limit)
    assert closer_order['quote']['amount'] == limit


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_closer_order_instant_fill_disabled(orders5, asset):
    """ When instant fill is disabled, new order should not cross lowest ask or highest bid
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    worker.is_instant_fill_enabled = False
    # Bump increment so hish that closer order will inevitably cross an opposite one
    worker.increment = 100
    result = worker.place_closer_order(asset, order, place_order=True)
    assert result is None


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_further_order_real_or_virtual(orders5, asset):
    """ Further order may be real or virtual, depending on distance from the center and operational_depth

        1. Further order within operational depth must be real
        2. Further order within operational depth must be virtual if virtual=True was given
        2. Further order outside of operational depth must be virtual
    """
    worker = orders5
    if asset == 'base':
        real_outside = worker.real_buy_orders[-1]
        real_within = worker.real_buy_orders[0]
    elif asset == 'quote':
        real_outside = worker.real_sell_orders[-1]
        real_within = worker.real_sell_orders[0]

    further_order = worker.place_further_order(asset, real_within, place_order=True)
    assert further_order, "Further order within operational depth must be real"

    further_order = worker.place_further_order(asset, real_within, place_order=True, virtual=True)
    assert isinstance(
        further_order, VirtualOrder
    ), "Further order within operational depth must be virtual if virtual=True was given"

    further_order = worker.place_further_order(asset, real_outside, place_order=True)
    assert isinstance(further_order, VirtualOrder), "Further order outside of operational depth must be virtual"


@pytest.mark.xfail(reason='https://github.com/bitshares/python-bitshares/issues/227')
@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_further_order_price_amount(orders5, asset):
    """ Test that further order price and amounts are correct
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    worker.returnOrderId = True
    further_order = worker.place_further_order(asset, order, place_order=True)

    # Test for correct price
    assert further_order['price'] == order['price'] / (1 + worker.increment)

    # Test for correct amount
    if (
        worker.mode == 'mountain'
        or (worker.mode == 'buy_slope' and asset == 'quote')
        or (worker.mode == 'sell_slope' and asset == 'base')
    ):
        assert further_order['quote']['amount'] == order['quote']['amount']
    elif (
        worker.mode == 'valley'
        or (worker.mode == 'buy_slope' and asset == 'base')
        or (worker.mode == 'sell_slope' and asset == 'quote')
    ):
        assert further_order['base']['amount'] == order['base']['amount']
    elif worker.mode == 'neutral':
        assert further_order['base']['amount'] == order['base']['amount'] / math.sqrt(1 + worker.increment)


@pytest.mark.xfail(reason='https://github.com/bitshares/python-bitshares/issues/227')
@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_further_order_no_place_order(orders5, asset):
    """ Test place_further_order() with place_order=False kwarg
    """
    worker = orders5

    if asset == 'base':
        order = worker.buy_orders[0]
    elif asset == 'quote':
        order = worker.sell_orders[0]

    further_order = worker.place_further_order(asset, order, place_order=False)
    # Place real order to compare with
    worker.place_further_order(asset, order, place_order=True)
    worker.refresh_orders()

    if asset == 'base':
        real_order = worker.buy_orders[1]
        price = real_order['price']
        amount = real_order['quote']['amount']
    elif asset == 'quote':
        real_order = worker.sell_orders[1]
        price = real_order['price'] ** -1
        amount = real_order['base']['amount']

    assert further_order['price'] == price
    assert further_order['amount'] == amount


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_further_order_not_allow_partial(orders2, asset):
    """ Test place_further_order with allow_partial=False
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        worker.base_balance['amount'] = order['base']['amount'] / 2
    elif asset == 'quote':
        order = worker.sell_orders[0]
        worker.quote_balance['amount'] = order['base']['amount'] / 2

    num_orders_before = len(worker.own_orders)
    worker.place_further_order(asset, order, place_order=True, allow_partial=False)
    num_orders_after = len(worker.own_orders)
    # Expect that order was not placed
    assert num_orders_before == num_orders_after


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_further_order_allow_partial_hard_limit(orders2, asset):
    """ Test place_further_order with allow_partial=True when avail balance is less than minimal allowed order size
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        price = order['price']
        # Pretend we have balance smaller than hard limit
        worker.base_balance['amount'] = worker.check_min_order_size(0, price) / 2
    elif asset == 'quote':
        order = worker.sell_orders[0]
        price = order['price'] ** -1
        worker.quote_balance['amount'] = worker.check_min_order_size(0, price) / 2

    num_orders_before = len(worker.own_orders)
    worker.place_further_order(asset, order, place_order=True, allow_partial=True)
    num_orders_after = len(worker.own_orders)
    # Expect that order was not placed
    assert num_orders_before == num_orders_after


@pytest.mark.parametrize('asset', ['base', 'quote'])
def test_place_further_order_allow_partial(orders2, asset):
    """ Test place_further_order with allow_partial=True
    """
    worker = orders2

    if asset == 'base':
        order = worker.buy_orders[0]
        worker.base_balance['amount'] = order['base']['amount'] / 2
    elif asset == 'quote':
        order = worker.sell_orders[0]
        worker.quote_balance['amount'] = order['base']['amount'] / 2

    num_orders_before = len(worker.own_orders)
    worker.place_closer_order(asset, order, place_order=True, allow_partial=True)
    num_orders_after = len(worker.own_orders)
    # Expect order placed
    assert num_orders_after - num_orders_before == 1
