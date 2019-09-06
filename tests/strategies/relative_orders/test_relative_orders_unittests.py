import math

import pytest
from dexbot.helper import truncate


def test_configure(ro_worker, config):
    worker = ro_worker
    cf = worker.config

    assert config == cf


def test_error(ro_worker):
    '''Event method return None'''
    worker = ro_worker
    worker.error()
    assert worker.disabled == True


def test_amount_to_sell(ro_worker):
    worker = ro_worker
    worker.calculate_order_prices()
    amount_to_sell = worker.amount_to_sell
    amount = worker.config['workers'][worker.account.name]['amount']
    assert amount_to_sell == amount

    worker.is_relative_order_size = True
    quote_balance = float(worker.balance(worker.market['quote']))
    amount_to_sell = worker.amount_to_sell
    amount = quote_balance * (amount / 100)
    assert amount_to_sell == amount


def test_amount_to_buy(ro_worker):
    worker = ro_worker

    buy_price = worker.center_price / math.sqrt(1 + worker.spread)
    sell_price = worker.center_price * math.sqrt(1 + worker.spread)
    assert buy_price == worker.buy_price
    assert sell_price == worker.sell_price
    assert worker.center_price == worker.config.get('workers').get(worker.account.name).get('center_price')
    amount = worker.config.get('workers').get(worker.account.name).get('amount')
    assert worker.amount_to_buy == amount

    worker.is_relative_order_size = True
    base_balance = float(worker.balance(worker.market['base']))
    amount = base_balance * (amount / 100) / worker.buy_price

    assert worker.amount_to_buy == amount


def test_calculate_order_prices(ro_worker):
    worker = ro_worker
    calculate_prices = worker.calculate_order_prices()
    assert calculate_prices == None

    buy_price = worker.buy_price
    sell_price = worker.sell_price
    center_price = worker.center_price
    spread = worker.spread

    assert worker.center_price == center_price

    buy_price_ca = center_price / math.sqrt(1 + spread)

    sell_price_ca = center_price * math.sqrt(1 + spread)

    assert buy_price == buy_price_ca

    assert sell_price == sell_price_ca


def test_update_orders(ro_worker):
    worker = ro_worker
    worker.update_orders()
    orders = worker.own_orders

    for o in orders:
        if o['base']['symbol'] == worker.market['base']['symbol']:
            assert o['price'] == round(worker.buy_price, 3)
        else:
            o.invert()
            assert o['price'] == truncate(worker.sell_price, 3)


def test_calculate_center_price(ro_orders1):
    worker = ro_orders1
    highest_bid = worker.market.ticker().get('highestBid')
    lowest_ask = worker.market.ticker().get('lowestAsk')
    cp = highest_bid * math.sqrt(lowest_ask / highest_bid)
    center_price = worker.calculate_center_price()

    assert cp == center_price


def test_calculate_asset_offset(ro_orders1):
    worker = ro_orders1
    center_price = worker.center_price
    spread = worker.spread

    total_balance = worker.count_asset()
    total = (total_balance['quote'] * center_price) + total_balance['base']

    if not total:  # Prevent division by zero
        base_percent = quote_percent = 0.5
    else:
        base_percent = total_balance['base'] / total
        quote_percent = 1 - base_percent

    highest_bid = float(worker.market.ticker().get('highestBid'))
    lowest_ask = float(worker.market.ticker().get('lowestAsk'))

    lowest_price = center_price / (1 + spread)
    highest_price = center_price * (1 + spread)

    lowest_price = max(lowest_price, highest_bid)
    highest_price = min(highest_price, lowest_ask)

    r = math.pow(highest_price, base_percent) * \
        math.pow(lowest_price, quote_percent)

    calculate_asset_offset = worker.calculate_asset_offset(
        center_price=center_price, order_ids=[], spread=spread)

    assert pytest.approx(calculate_asset_offset, abs=0.000001) == r


def test_calculate_manual_offset(ro_orders1):
    worker = ro_orders1
    center_price = worker.center_price
    manual_offset = 0.1

    calculate_offset = worker.calculate_manual_offset(
        center_price=center_price, manual_offset=manual_offset)

    assert calculate_offset == center_price * (1 + manual_offset)

    manual_offset = -0.1

    calculate_offset = worker.calculate_manual_offset(
        center_price=center_price, manual_offset=manual_offset)

    assert calculate_offset == center_price / (1 + abs(manual_offset))


def test_check_orders(ro_worker):
    worker = ro_worker
    worker.check_orders()
