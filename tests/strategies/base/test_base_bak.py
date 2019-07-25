import pytest
from dexbot.strategies.base import StrategyBase
import logging
import os
from tests.fixtures import fixture_data_BASE
from fixtures import get_balance
from bitshares.market import Market
from bitshares.account import Account
from bitshares.exceptions import MissingKeyError
from bitshares.price import Order
from bitshares.dex import Dex
from bitshares.amount import Amount
import pysnooper
import math
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


class Test_StrategyBase:
    def setup_class(self):
        self.TEST_CONFIG = fixture_data_BASE()
        self.account = Account(
            self.TEST_CONFIG['workers']['worker 1']['account']
        )
        self.market_symbol = self.TEST_CONFIG['workers']['worker 1']['market']
        self.base_symbol = self.market_symbol.split('/')[0]
        self.quote_symbol = self.market_symbol.split('/')[1]
        self.market = Market(self.market_symbol)

        self.strategy_base = StrategyBase(
            name='worker 1', config=self.TEST_CONFIG)

    def teardown_class(self):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    # def test_configure(self):
    #     base_config = StrategyBase.configure()
    #     for x in base_config:
    #         logging.info(x)
    #         assert x != ''

    # def test_configure_details(self):
    #     config_details = StrategyBase.configure_details()
    #     for x in config_details:
    #         logging.info(x)
    #         assert x == ''
    # def test_account_total_value(self):
    #     value1 = self.strategy_base.account.balance(self.base_symbol)
    #     value2 = self.strategy_base.account.balance(self.quote_symbol)

    #     latest_price = self.market.ticker().get('latest')
    #     con_value2 = float(value2) * 1 / float(latest_price)

    #     value3 = 0
    #     os = self.account.openorders
    #     for o in os:
    #         if o['base']['symbol'] == self.base_symbol:
    #             value3 = value3 + o['base']['amount']
    #         else:
    #             tem = o['base']['amount']
    #             latest_price = market.ticker().get('latest')
    #             value3 = value3 + float(tem) * 1 / float(latest_price)

    #     value = float(value1) + float(con_value2) + float(value3)

    #     total_value = self.strategy_base.account_total_value(self.base_symbol)
    #     total_value = round(total_value, 3)

    #     assert total_value == value,'account_total_value() error!'

    # def test_balance(self):
    #     value = self.account.balance(self.base_symbol)
    #     test_balance = self.strategy_base.balance(self.base_symbol)
    #     assert value == test_balance, ' balance() error!'

    # def test_calculate_order_data(self):
    #     order = Order("10 " + self.quote_symbol,
    #                   "1 " + self.base_symbol)
    #     amount = 10
    #     price = 2
    #     order = self.strategy_base.calculate_order_data(order, amount, price)
    #     assert 10 == order['quote'], 'calculate_order_data() error!'
    #     assert 20 == order['base'], 'calculate_order_data() error!'
    #     assert 2 == order['price'], 'calculate_order_data() error!'

    # def test_calculate_worker_value(self):
    #     total_account_balance = get_balance('BTS')
    #     total_account_calculate = self.strategy_base.calculate_worker_value(
    #         'BTS')
    #     logging.info(total_account_balance)
    #     assert total_account_balance <= total_account_calculate

    # def test_cancel_all_orders(self):
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     with pytest.raises(MissingKeyError):
    #         market.sell(
    #             1,
    #             10,
    #             expiration=60 * 60,
    #             returnOrderId=True
    #         )
    #     self.strategy_base.cancel_all_orders()
    #     openorders = market.accountopenorders()
    #     logging.info(openorders)
    #     assert openorders == [], 'order is not cancel!'

    # # def test_cancel_orders(self):
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     logging.info(market.accountopenorders)
    #     with pytest.raises(MissingKeyError):
    #         market.sell(
    #             1,
    #             10,
    #             expiration=60 * 60,
    #             returnOrderId=True
    #         )
    #     with pytest.raises(MissingKeyError):
    #         self.strategy_base.cancel_orders('123')
    #     order = Order(0.315, base="BADCOIN", quote="BTS")
    #     with pytest.raises(MissingKeyError):
    #         self.strategy_base.cancel_orders(order)

    # def test_count_asset(self):
    #     r = self.strategy_base.count_asset()
    #     logging.info(r)
    #     quote = get_balance()
    #     assert quote == r['quote']

    # def test_get_allocated_assets(self):
    #     r = self.strategy_base.get_allocated_assets()
    #     logging.info(r)
    #     assert r['quote'] == 0
    #     assert r['base'] == 0

    # def test_get_market_buy_orders(self):
    #     buy_orders = self.strategy_base.get_market_buy_orders()
    #     logging.info(buy_orders)
    #     assert buy_orders != []

    # def test_get_market_sell_orders(self):
    #     r = self.strategy_base.get_market_sell_orders()
    #     logging.info(r)
    #     assert r != []

    # def test_get_highest_market_buy_order(self):
    #     r = self.strategy_base.get_highest_market_buy_order()
    #     logging.info(r)
    #     assert r != []

    # def test_get_highest_own_buy_order(self):
    #     r = self.strategy_base.get_highest_own_buy_order()
    #     logging.info(r)
    #     assert r is None

    # def test_get_lowest_market_sell_order(self):
    #     r = self.strategy_base.get_lowest_market_sell_order()
    #     logging.info(r)
    #     assert r != []

    # def test_get_lowest_own_sell_order(self):
    #     r = self.strategy_base.get_lowest_own_sell_order()
    #     logging.info(r)
    #     assert r is None

    # def test_get_external_market_center_price(self):
    #     r = self.strategy_base.get_external_market_center_price('Binance')
    #     logging.info(r)

    # def test_get_market_center_price(self):
    #     r = self.strategy_base.get_market_center_price()
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     highestBid = market.ticker().get('highestBid')
    #     lowestAsk = market.ticker().get('lowestAsk')
    #     center_price = lowestAsk * math.sqrt(lowestAsk / highestBid)
    #     logging.info(r)
    #     logging.info(highestBid)
    #     logging.info(lowestAsk)
    #     logging.info(center_price)
    #     assert r < center_price

    # def test_get_market_buy_price(self):
    #     r = self.strategy_base.get_market_buy_price()
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     highestBid = market.ticker().get('highestBid')
    #     logging.info(r)
    #     logging.info(highestBid)
    #     assert r == highestBid

    # def test_get_market_orders(self):
    #     r = self.strategy_base.get_market_orders()
    #     logging.info(r)

    # def test_get_orderbook_orders(self):
    #     r = self.strategy_base.get_orderbook_orders()
    #     logging.info(r)

    # def test_get_market_sell_price(self):
    #     r = self.strategy_base.get_market_sell_price()
    #     logging.info(r)

    # def test_get_market_spread(self):
    #     r = self.strategy_base.get_market_spread()
    #     logging.info(r)

    # def test_get_order_cancellation_fee(self):
    #     r = self.strategy_base.get_order_cancellation_fee('BTS')
    #     dex = Dex()
    #     fees = dex.returnFees()
    #     limit_order_cancel = fees['limit_order_cancel']['fee']
    #     logging.info(r)
    #     logging.info(limit_order_cancel)
    #     assert r == limit_order_cancel

    # def test_get_order_creation_fee(self):
    #     r = self.strategy_base.get_order_creation_fee('TEST')
    #     logging.info(r)
    #     dex = Dex()
    #     fees = dex.returnFees()
    #     limit_order_create = fees['limit_order_create']
    #     assert r == limit_order_create['fee']

    # def test_filter_buy_orders(self):
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     orders = market.orderbook().get('bids')
    #     last = orders[-1]
    #     logging.info(last)
    #     logging.info(orders)
    #     sorted_orders = self.strategy_base.filter_buy_orders(
    #         orders, sort='ASC')
    #     logging.info(sorted_orders)
    #     assert last == sorted_orders[0]

    # def test_filter_sell_orders(self):
    #     market = Market(fixture_data()['workers']['worker 1']['market'])
    #     orders = market.orderbook().get('asks')
    #     last = orders[-1]
    #     logging.info(last)
    #     logging.info(orders)
    #     sorted_orders = self.strategy_base.filter_sell_orders(
    #         orders, sort='ASC')
    #     logging.info(sorted_orders)
    #     assert last == sorted_orders[0]

    # def test_get_own_buy_orders(self):
    #     r = self.strategy_base.get_own_buy_orders()
    #     logging.info(r)

    # def test_get_own_sell_orders(self):
    #     r = self.strategy_base.get_own_sell_orders()
    #     logging.info(r)

    # def test_get_own_spread(self):
    #     symbol = self.TEST_CONFIG['workers']['worker 1']['market']
    #     market = Market(symbol)
    #     # 自己下订单来判断实际的利差是否计算正确
    #     r = self.strategy_base.get_own_spread()
    #     logging.info(r)
    #     assert r is None

    # def test_get_updated_order(self):
    #     symbol = self.TEST_CONFIG['workers']['worker 1']['market']
    #     market = Market(symbol)
    #     o = market.buy(0.1, 1, returnOrderId=True)
    #     orderid = o.get('orderid')

    #     r = self.strategy_base.get_updated_order([orderid])
    #     logging.info(r)

    # def test_execute(self):
    #     self.strategy_base.execute()

    # def test_is_buy_order(self):
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     logging.info(account_name)
    #     account = Account(account_name)
    #     os = account.openorders
    #     for o in os:
    #         logging.info(o)
    #         flag = self.strategy_base.is_buy_order(o)
    #         logging.info(o['base']['symbol'])
    #         logging.info(dict(o))

    #         assert flag == True

    # def test_is_current_market(self):
    #     r = self.strategy_base.is_current_market('1.3.1366', '1.3.0')
    #     assert r == True
    #     r = self.strategy_base.is_current_market('1.3.0', '1.3.1366')
    #     assert r == False
    #     r = self.strategy_base.is_current_market('1.3.5', '1.3.10')
    #     assert r == False

    # def test_is_sell_order(self):
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     logging.info(account_name)
    #     account = Account(account_name)
    #     os = account.openorders
    #     for o in os:
    #         logging.info(o)
    #         flag = self.strategy_base.is_sell_order(o)
    #         logging.info(o['base']['symbol'])
    #         logging.info(dict(o))

    #         assert flag == False

    # def test_pause(self):
    #     self.strategy_base.pause()

    # def test_clear_all_worker_data(self):
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     logging.info(account_name)
    #     account = Account(account_name)
    #     os = account.openorders
    #     logging.info(os)
    #     assert os != []
    #     self.strategy_base.clear_all_worker_data()
    #     account = Account(account_name)
    #     os = account.openorders
    #     logging.info(os)
    #     assert os == []

    # def test_place_market_buy_order(self):
    #     self.strategy_base.clear_all_worker_data()
    #     self.strategy_base.place_market_buy_order(1, 0.1)
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     logging.info(account_name)
    #     account = Account(account_name)
    #     os = account.openorders
    #     logging.info(os)
    #     for o in os:
    #         logging.info(o.get('quote'))
    #         logging.info(o.get('base'))
    #         logging.info(o.get('price'))
    #         assert o.get('quote') == 1
    #         assert o.get('price') == 0.1

    # def test_place_market_sell_order(self):
    #     self.strategy_base.clear_all_worker_data()
    #     self.strategy_base.place_market_sell_order(1, 0.1)
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     logging.info(account_name)
    #     account = Account(account_name)
    #     os = account.openorders
    #     logging.info(os)
    #     for o in os:
    #         logging.info(o.get('quote'))
    #         logging.info(o.get('base'))
    #         logging.info(o.get('price'))
    #         assert o.get('quote') == 0.1
    #         assert o.get('price') == 10

    # def test_retry_action(self):
    #     self.strategy_base.clear_all_worker_data()
    #     price = 0.1
    #     amount = 1
    #     sell_transaction = self.strategy_base.retry_action(
    #         self.strategy_base.market.sell,
    #         price,
    #         Amount(amount=amount, asset=self.strategy_base.market["quote"]),
    #         account=self.strategy_base.account.name,
    #         expiration=self.strategy_base.expiration,
    #         returnOrderId=True,
    #         fee_asset=self.strategy_base.fee_asset['id']
    #         # *args,
    #         # **kwargs
    #     )
    #     account_name = self.strategy_base.account.name
    #     account = Account(account_name)
    #     os = account.openorders
    #     logging.info(os)
    #     for o in os:
    #         logging.info(o.get('quote'))
    #         logging.info(o.get('base'))
    #         logging.info(o.get('price'))
    #         assert o.get('quote') == 0.1
    #         assert o.get('price') == 10

    # def test_store_profit_estimation_data(self):
    #     import time
    #     timestamp = time.time()
    #     logging.info(self.strategy_base.worker_name)
    #     self.strategy_base.store_profit_estimation_data()
    #     r = self.strategy_base.get_profit_estimation_data(timestamp)
    #     logging.info(r)

    # def test_get_profit_estimation_data(self):
    #     self.strategy_base.get_profit_estimation_data('ddd')

    # def test_calc_profit(self):
    #     r = self.strategy_base.calc_profit()
    #     logging.info(r)

    # def test_write_order_log(self):
    #     self.strategy_base.write_order_log('worker 1',
    #                                        Order('0.1 TEST',
    #                                              '1 DEXBOT')
    #                                        )

    # def test_account(self):
    #     r = self.strategy_base.account
    #     logging.info(r)
    #     logging.info(r.name)
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     assert r.name == account_name

    # def test_quote_asset(self):
    #     symbol = self.TEST_CONFIG['workers']['worker 1']['market']
    #     r = self.strategy_base.quote_asset
    #     logging.info(r)
    #     assert r == symbol.split('/')[0]

    # def test_all_own_orders(self):
    #     self.strategy_base.clear_all_worker_data()
    #     self.strategy_base.place_market_sell_order(1, 0.1)
    #     os = self.strategy_base.all_own_orders
    #     logging.info(os)
    #     for o in os:
    #         logging.info(o.get('quote'))
    #         logging.info(o.get('base'))
    #         logging.info(o.get('price'))
    #         assert o.get('quote') == 0.1
    #         assert o.get('price') == 10

    # def test_get_own_orders(self):
    #     self.strategy_base.clear_all_worker_data()
    #     self.strategy_base.place_market_sell_order(1, 0.1)
    #     os = self.strategy_base.get_own_orders
    #     logging.info(os)
    #     for o in os:
    #         logging.info(o.get('quote'))
    #         logging.info(o.get('base'))
    #         logging.info(o.get('price'))
    #         assert o.get('quote') == 0.1
    #         assert o.get('price') == 10

    # def test_market(self):
    #     symbol = self.TEST_CONFIG['workers']['worker 1']['market']
    #     r = self.strategy_base.market
    #     quote_symbol = r.get('quote').get('symbol')
    #     base_symbol = r.get('base').get('symbol')
    #     quote = symbol.split('/')[0]
    #     base = symbol.split('/')[1]
    #     logging.info(quote_symbol)
    #     logging.info(base_symbol)
    #     logging.info(symbol)
    #     logging.info(quote)
    #     logging.info(base)

    #     assert quote == quote_symbol
    #     assert base == base_symbol

    # def test_convert_asset(self):
    #     r = self.strategy_base.convert_asset(10, 'TEST', 'DEXBOT')
    #     logging.info(r)
    #     latest_price = self.strategy_base.market.ticker().get('latest')
    #     logging.info(latest_price)
    #     assert 10 * latest_price == r

    # def test_convert_fee(self):
    #     r = self.strategy_base.convert_fee(1, 'USD')
    #     logging.info(r)
    #     market = Market('USD:TEST')
    #     t = market.ticker()
    #     logging.info(t)
    #     logging.info(dict(t['core_exchange_rate']))

    #     e = t['core_exchange_rate']
    #     logging.info(e)
    #     js = 1 * float(e)
    #     logging.info(js)

    #     assert js == r

    # def test_get_order(self):
    #     self.strategy_base.clear_all_worker_data()
    #     symbol = self.TEST_CONFIG['workers']['worker 1']['market']
    #     market = Market(symbol)
    #     o = market.buy(0.1, 1, returnOrderId=True)
    #     orderid = o.get('orderid')

    #     logging.info(orderid)

    #     r = self.strategy_base.get_order(orderid)
    #     logging.info(r)
    #     logging.info(r.get('base'))
    #     logging.info(r.get('quote'))

    #     assert 0.1 == r.get('base')
    #     assert 1 == r.get('quote')

    # def test_get_updated_limit_order(self):
    #     account_name = self.TEST_CONFIG['workers']['worker 1']['account']
    #     logging.info(account_name)
    #     account = Account(account_name)
    #     os = account.openorders
    #     for o in os:
    #         logging.info(o)
    #     # r = self.strategy_base.get_updated_limit_order(o)
    #     # logging.info(r)

    # def test_purge_all_local_worker_data(self):
    #     self.strategy_base.purge_all_local_worker_data('worker 1')

    # def test_sort_orders_by_price(self):
    #     self.strategy_base.clear_all_worker_data()
    #     self.strategy_base.place_market_sell_order(1, 0.1)
    #     self.strategy_base.place_market_sell_order(1, 0.2)
    #     os = self.strategy_base.account.openorders
    #     logging.info(os)
    #     assert os[0]['price'] == 1 / 0.1
    #     assert os[1]['price'] == 1 / 0.2
    #     r = self.strategy_base.sort_orders_by_price(os, 'ASC')
    #     logging.info(r)
    #     assert r[0]['price'] == 1 / 0.2
    #     assert r[1]['price'] == 1 / 0.1

    # def test_update_gui_slider(self):
    #     pass

    # def test_update_gui_profit(self):
    #     pass

    # def tearDown(self):
    #     pass


if __name__ == '__main__':
    cur_dir = os.path.dirname(__file__)
    test_file = os.path.join(cur_dir, 'base_test.py')
    pytest.main(['--capture=no', test_file])
