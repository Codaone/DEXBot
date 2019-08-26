from bitshares.account import Account
from bitshares.asset import Asset
import math
import pytest

from dexbot.helper import truncate


def test_worker_balance(bitshares, account):
    a = Account('ro-worker', bitshares_instance=bitshares)
    assert a.balance('BASEA') == 10000
    assert a.balance('QUOTEA') == 100


def test_asset_base(bitshares, assets):
    a = Asset('BASEA', full=True, bitshares_instance=bitshares)
    # assert a['dynamic_asset_data']['current_supply'] > 1000
    assert a.symbol == 'BASEA'


def test_asset_quote(bitshares, assets):
    a = Asset('QUOTEA', full=True, bitshares_instance=bitshares)
    current_supply = a['dynamic_asset_data']['current_supply']
    if isinstance(current_supply, str):
        current_supply = float(current_supply)
    # assert current_supply > 1000

    assert a.symbol == 'QUOTEA'


def test_correct_asset_names(ro_orders1):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = ro_orders1
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['BASEA', 'BASEB', 'QUOTEA', 'QUOTEB']
    assert orders[0]['base']['asset']['symbol'] in symbols
    worker.cancel_all_orders()


def test_correct_asset_names(ro_worker):
    """ Test for https://github.com/bitshares/python-bitshares/issues/239
    """
    worker = ro_worker
    worker.account.refresh()
    orders = worker.account.openorders
    symbols = ['BASEA', 'BASEB', 'QUOTEA', 'QUOTEB']
    assert orders[0]['base']['asset']['symbol'] in symbols




#####################################
# test single account multiple workers#
######################################

def test_configure(ro_worker, config, ro_worker1, config1):
    worker = ro_worker
    worker_config = worker.config
    assert config == worker_config

    worker1 = ro_worker1
    worker_config = worker1.config
    assert config1 == worker_config
    # from pprint import pprint
    # pprint(worker.config)
    # pprint(worker1.config)


def test_error(ro_worker, ro_worker1):
    '''Event method return None'''
    worker = ro_worker
    worker.error()
    assert worker.disabled == True
    worker1 = ro_worker1
    worker1.error()
    assert worker1.disabled == True


def test_amount_to_sell(ro_worker, ro_worker1):
    worker = ro_worker
    worker.calculate_order_prices()
    amount_to_sell = worker.amount_to_sell
    amount = worker.config['workers'][worker.account.name]['amount']
    assert amount_to_sell == amount

    worker1 = ro_worker1
    worker1.calculate_order_prices()
    amount_to_sell1 = worker.amount_to_sell
    amount = worker.config['workers'][worker.account.name]['amount']
    assert amount_to_sell1 == amount


def test_amount_to_buy(ro_worker, ro_worker1, ro_worker_name1):
    worker = ro_worker
    buy_price = worker.center_price / math.sqrt(1 + worker.spread)
    sell_price = worker.center_price * math.sqrt(1 + worker.spread)
    assert buy_price == worker.buy_price
    assert sell_price == worker.sell_price
    assert worker.center_price == worker.config.get('workers').get(worker.account.name).get('center_price')
    assert worker.amount_to_buy == worker.config.get('workers').get(worker.account.name).get('amount')

    worker = ro_worker1
    buy_price = worker.center_price / math.sqrt(1 + worker.spread)
    sell_price = worker.center_price * math.sqrt(1 + worker.spread)
    assert buy_price == worker.buy_price
    assert sell_price == worker.sell_price
    assert worker.center_price == worker.config.get('workers').get(ro_worker_name1).get('center_price')
    assert worker.amount_to_buy == worker.config.get('workers').get(ro_worker_name1).get('amount')


def test_calculate_order_prices(ro_worker, ro_worker1):
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

    # another worker
    worker = ro_worker1
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


def test_update_orders(ro_worker, ro_worker1):
    worker = ro_worker
    worker.update_orders()
    orders = worker.own_orders

    for o in orders:
        if o['base']['symbol'] == worker.market['base']['symbol']:
            assert o['price'] == round(worker.buy_price, 3)
        else:
            o.invert()
            assert o['price'] == truncate(worker.sell_price, 3)
    # another worker
    worker = ro_worker1
    worker.update_orders()
    orders = worker.own_orders

    for o in orders:
        if o['base']['symbol'] == worker.market['base']['symbol']:
            assert o['price'] == round(worker.buy_price, 3)
        else:
            o.invert()
            assert o['price'] == truncate(worker.sell_price, 3)


def test_calculate_center_price(ro_orders1, ro_worker1):
    worker = ro_orders1
    highest_bid = worker.market.ticker().get('highestBid')
    lowest_ask = worker.market.ticker().get('lowestAsk')
    cp = float(highest_bid * math.sqrt(lowest_ask / highest_bid))
    center_price = worker.calculate_center_price()

    assert pytest.approx(cp, rel=1e-6) == center_price

    worker = ro_worker1
    highest_bid = worker.market.ticker().get('highestBid')
    lowest_ask = worker.market.ticker().get('lowestAsk')
    cp = float(highest_bid * math.sqrt(lowest_ask / highest_bid))
    center_price = worker.calculate_center_price()

    assert pytest.approx(cp, rel=1e-6) == center_price


def test_calculate_asset_offset(ro_orders1, ro_worker1):
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
    # another worker
    worker = ro_worker1
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


def test_calculate_manual_offset(ro_orders1, ro_worker1):
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

    # another worker
    worker = ro_worker1
    center_price = worker.center_price
    manual_offset = 0.1

    calculate_offset = worker.calculate_manual_offset(
        center_price=center_price, manual_offset=manual_offset)

    assert calculate_offset == center_price * (1 + manual_offset)

    manual_offset = -0.1

    calculate_offset = worker.calculate_manual_offset(
        center_price=center_price, manual_offset=manual_offset)

    assert calculate_offset == center_price / (1 + abs(manual_offset))


def test_check_orders(ro_worker, ro_worker1):
    worker = ro_worker
    worker.check_orders()
    worker = ro_worker1
    worker.check_orders()
