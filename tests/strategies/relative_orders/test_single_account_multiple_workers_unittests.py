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

def test_configure(ro_worker, config, multiple_worker, single_account_config):
    worker = ro_worker
    worker_config = worker.config
    assert config == worker_config

    worker = multiple_worker
    worker_config = worker.config
    assert single_account_config == worker_config

    # make sure single account multiple workers
    assert worker.account.name == worker.account.name


def test_error(ro_worker, ro_worker1, multiple_worker):
    '''Event method return None'''
    worker = ro_worker
    worker.error()
    assert worker.disabled == True
    worker = ro_worker1
    worker.error()
    assert worker.disabled == True

    worker = multiple_worker
    worker.error()
    assert worker.disabled == True


def test_amount_to_sell(ro_worker, ro_worker1, ro_worker_name1, multiple_worker, multiple_worker_name):
    def _amount_to_sell(worker, worker_name):
        worker.calculate_order_prices()
        amount_to_sell = worker.amount_to_sell
        amount = worker.config['workers'][worker_name]['amount']
        assert amount_to_sell == amount

    worker = ro_worker
    _amount_to_sell(worker, worker.account.name)
    # another worker
    worker = ro_worker1
    _amount_to_sell(worker, ro_worker_name1)
    # another worker
    worker = multiple_worker
    _amount_to_sell(worker, multiple_worker_name)


def test_amount_to_buy(ro_worker, ro_worker1, ro_worker_name1, multiple_worker, multiple_worker_name):
    def _amount_to_buy(worker, worker_name):
        buy_price = worker.center_price / math.sqrt(1 + worker.spread)
        sell_price = worker.center_price * math.sqrt(1 + worker.spread)
        assert buy_price == worker.buy_price
        assert sell_price == worker.sell_price
        assert worker.center_price == worker.config.get('workers').get(worker_name).get('center_price')
        assert worker.amount_to_buy == worker.config.get('workers').get(worker_name).get('amount')

    worker = ro_worker
    _amount_to_buy(worker, worker.account.name)
    # another worker
    worker = ro_worker1
    _amount_to_buy(worker, ro_worker_name1)
    # another worker
    worker = multiple_worker
    _amount_to_buy(worker, multiple_worker_name)


def test_calculate_order_prices(ro_worker, ro_worker1, multiple_worker):
    def _calculate_order_prices(worker):
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

    worker = ro_worker
    _calculate_order_prices(worker)
    # another worker
    worker = ro_worker1
    _calculate_order_prices(worker)
    # another worker
    worker = multiple_worker
    _calculate_order_prices(worker)


def test_update_orders(ro_worker, ro_worker1, multiple_worker):
    def _update_orders(worker):
        worker.update_orders()
        orders = worker.own_orders

        for o in orders:
            if o['base']['symbol'] == worker.market['base']['symbol']:
                assert o['price'] == round(worker.buy_price, 3)
            else:
                o.invert()
                assert o['price'] == truncate(worker.sell_price, 3)

    worker = ro_worker
    _update_orders(worker)
    # another worker
    worker = ro_worker1
    _update_orders(worker)
    # another worker
    worker = multiple_worker
    _update_orders(worker)


def test_calculate_center_price(ro_orders1, ro_worker1, multiple_worker):
    def _calculate_center_price(worker):
        highest_bid = worker.market.ticker().get('highestBid')
        lowest_ask = worker.market.ticker().get('lowestAsk')
        cp = float(highest_bid * math.sqrt(lowest_ask / highest_bid))
        center_price = worker.calculate_center_price()

        assert pytest.approx(cp, rel=1e-6) == center_price

    worker = ro_orders1
    _calculate_center_price(worker)
    # another worker
    worker = ro_worker1
    _calculate_center_price(worker)
    # another worker
    worker = multiple_worker
    _calculate_center_price(worker)


def test_calculate_asset_offset(ro_orders1, ro_worker1, multiple_worker):
    def _calculate_asset_offset(worker):
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

    worker = ro_orders1
    _calculate_asset_offset(worker)
    # another worker
    worker = ro_worker1
    _calculate_asset_offset(worker)
    # another worker
    worker = multiple_worker
    _calculate_asset_offset(worker)


def test_calculate_manual_offset(ro_orders1, ro_worker1, multiple_worker):
    def _calculate_manual_offset(worker):
        center_price = worker.center_price
        manual_offset = 0.1

        calculate_offset = worker.calculate_manual_offset(
            center_price=center_price, manual_offset=manual_offset)

        assert calculate_offset == center_price * (1 + manual_offset)

        manual_offset = -0.1

        calculate_offset = worker.calculate_manual_offset(
            center_price=center_price, manual_offset=manual_offset)

        assert calculate_offset == center_price / (1 + abs(manual_offset))

    worker = ro_orders1
    _calculate_manual_offset(worker)
    # another worker
    worker = ro_worker1
    _calculate_manual_offset(worker)
    # another worker
    worker = multiple_worker
    _calculate_manual_offset(worker)


def test_check_orders(ro_worker, ro_worker1, multiple_worker):
    worker = ro_worker
    worker.check_orders()
    worker = ro_worker1
    worker.check_orders()
    worker = ro_worker1
    worker.check_orders()
