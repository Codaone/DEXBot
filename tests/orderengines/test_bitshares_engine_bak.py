import os
import pytest
from tests.fixtures import fixture_data
from dexbot.orderengines.bitshares_engine import BitsharesOrderEngine
from bitshares.account import Account
from bitshares.market import Market
from bitshares.price import Order
from bitshares import BitShares
from bitshares.asset import Asset


class Test_BitsharesOrderEngine:
    def setup_class(self):
        # fixture
        self.TEST_CONFIG = fixture_data('OE')
        self.bts = BitShares(self.TEST_CONFIG['node'])
        self.account = Account(
            self.TEST_CONFIG['workers']['worker 1']['account']
        )
        assert self.account['name'] == 'dexbot-test4'
        self.market_symbol = self.TEST_CONFIG['workers']['worker 1']['market']
        assert self.market_symbol == 'TEST/DEXBOT'
        self.base_symbol = self.market_symbol.split('/')[1]
        assert self.base_symbol == 'DEXBOT'
        self.quote_symbol = self.market_symbol.split('/')[0]
        assert self.quote_symbol == 'TEST'
        self.market = Market(self.market_symbol)
        assert self.base_symbol == self.market['base']['symbol']
        assert self.quote_symbol == self.market['quote']['symbol']
        self.fee_asset = self.TEST_CONFIG['workers']['worker 1']['fee_asset']
        self.fee_asset == 'TEST'
        self.oe = BitsharesOrderEngine(
            name='worker 1',
            config=self.TEST_CONFIG,
            account=self.account,
            market=self.market,
            fee_asset_symbol=self.fee_asset,
            bitshares_instance=None,
            bitshares_bundle=None,
        )

    def teardown_class(self):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_account_total_value(self):
        from_value = self.account.balance(self.quote_symbol)
        cv = BitsharesOrderEngine.convert_asset(
            from_value, self.quote_symbol, self.base_symbol)
        ncv = self.account.balance(self.base_symbol)
        ors = self.account.openorders
        if ors:
            for o in ors:
                if o['base']['symbol'] == self.base_symbol:
                    ncv += o['base']['amount']
                else:
                    cv += BitsharesOrderEngine.convert_asset(
                        o['base']['amount'],
                        o['base']['symbol'],
                        self.base_symbol)
        cal = float(ncv + cv)
        atv = self.oe.account_total_value(self.base_symbol)
        assert round(atv, 4) == float(cal)

    def test_balance(self):
        value = self.account.balance(self.base_symbol)
        test_balance = self.oe.balance(self.base_symbol)
        assert value == test_balance
        value = self.account.balance(self.quote_symbol)
        test_balance = self.oe.balance(self.quote_symbol)
        assert value == test_balance

    def test_calculate_order_data(self):
        order = Order("10 " + self.quote_symbol,
                      "1 " + self.base_symbol)
        amount = 10
        price = 2
        order = self.oe.calculate_order_data(order, amount, price)
        assert 10 == order['quote']
        assert 20 == order['base']
        assert 2 == order['price']

    def test_calculate_worker_value(self):
        cwv = self.oe.calculate_worker_value(self.base_symbol)
        cwv = self.oe.calculate_worker_value(self.quote_symbol)

    def test_cancel_all_orders(self):
        self.market.buy(0.1, 1)
        assert self.account.openorders != []
        self.oe.cancel_all_orders()
        assert self.account.openorders == []

    def test_cancel_orders(self):
        self.market.buy(0.1, 1)
        assert self.account.openorders != []
        for o in self.account.openorders:
            self.oe.cancel_orders(o)
        assert self.account.openorders == []
        self.market.buy(0.2, 1)
        for o in self.account.openorders:
            self.oe.cancel_orders(o, batch_only=True)
        assert self.account.openorders == []

    def test_count_asset(self):
        if self.account.openorders == []:
            self.market.buy(0.1, 1)
        assert self.account.openorders != []

        balance = self.account.balance(self.base_symbol)

        s = 0
        for o in self.account.openorders:
            s += float(o['base'])
        r = self.oe.count_asset(self.account.openorders, self.base_symbol)

        assert balance + s == r['base']

    def test_get_allocated_assets(self):
        if self.account.openorders == []:
            self.market.buy(0.1, 1)
        assert self.account.openorders != []

        s = 0
        for o in self.account.openorders:
            s += float(o['base'])
        r = self.oe.get_allocated_assets(
            self.account.openorders, self.base_symbol)

        assert s == r['base']

    def test_get_highest_own_buy_order(self, orders=None):
        self.oe.cancel_all_orders()
        ors = self.account.openorders
        assert ors == []
        if ors == []:
            self.market.buy(0.1, 1)
            self.market.buy(0.2, 1)
        ors_id = []
        for o in ors:
            ors_id.append(o['id'])
        r = self.oe.get_highest_own_buy_order(ors_id)
        o = Order(r)
        assert o['price'] == 0.2

    def test_get_market_orders(self):
        self.oe.cancel_all_orders()
        if self.account.openorders == []:
            self.market.buy(0.1, 1)
        own = self.account.openorders
        market_orders = self.oe.get_market_orders(depth=50, updated=True)
        for o in own:
            assert o in market_orders

    def test_get_order_cancellation_fee(self):
        fee = self.oe.get_order_cancellation_fee(self.base_symbol)
        assert fee == 0
        fee = self.oe.get_order_cancellation_fee(self.quote_symbol)
        assert fee == 0

    def test_get_order_creation_fee(self):
        fee = self.oe.get_order_cancellation_fee(self.base_symbol)
        assert fee == 0
        fee = self.oe.get_order_cancellation_fee(self.quote_symbol)
        assert fee == 0

    def test_get_own_buy_orders(self):
        orders = self.oe.get_own_buy_orders()

    def test_get_own_sell_orders(self):
        orders = self.oe.get_own_sell_orders()

    def test_get_own_spread(self):
        spread = self.oe.get_own_spread()

    def test_get_updated_order(self):
        if self.account.openorders == []:
            self.market.buy(0.1, 1)
        orders = self.account.openorders
        for o in orders:
            self.oe.get_updated_order(o['id'])

    # def test_execute(self):
    #     self.market.sell(0.1, 1)
    #     self.oe.execute()

    def test_is_buy_order(self):
        if self.account.openorders == []:
            self.market.buy(0.1, 1)
        orders = self.account.openorders
        for o in orders:
            if o['base']['symbol'] == self.market['base']['symbol']:
                r = self.oe.is_buy_order(o)
                assert r == True

    def test_is_current_market(self):
        base_id = Asset(self.base_symbol)['id']
        quote_id = Asset(self.quote_symbol)['id']
        r = self.oe.is_current_market(base_id, quote_id)
        assert r == True
        r = self.oe.is_current_market(quote_id, base_id)
        assert r == True
        r = self.oe.is_current_market('CNY', 'USD')
        assert r == False

    def test_is_sell_order(self):
        if self.account.openorders == []:
            self.market.sell(0.1, 1)
        orders = self.account.openorders
        for o in orders:
            if o['base']['symbol'] == self.market['quote']['symbol']:
                r = self.oe.is_sell_order(o)
                assert r == True

    def test_place_market_buy_order(self):
        r = self.oe.place_market_buy_order(10, 1)
        assert r['price'] == 1
        assert r['quote']['amount'] == 10

    def test_place_market_sell_order(self):
        r = self.oe.place_market_sell_order(10, 1)
        assert r['price'] == 1
        assert r['quote']['amount'] == 10

    def test_retry_action(self):
        self.oe.retry_action(self.market.buy, 1, 10)
        self.oe.retry_action(self.market.sell, 1, 10)

    def test_account(self):
        acc = self.oe.account
        assert acc == self.account

    def test_balances(self):
        r = self.oe.balances
        for b in r:
            if b['symbol'] == self.base_symbol:
                a = self.account.balance(self.base_symbol)
                assert b == a
            if b['symbol'] == self.quote_symbol:
                a = self.account.balance(self.quote_symbol)
                assert b == a

    def test_get_all_own_orders(self):
        r = self.oe.get_own_orders()

    def test_all_own_orders(self):
        self.oe.all_own_orders()

    def test_own_orders(self):
        self.oe.own_orders()

    def test_market(self):
        market = self.oe.market
        assert market['base']['symbol'] == self.base_symbol
        assert market['quote']['symbol'] == self.quote_symbol

    def test_get_updated_limit_order(self):
        ors = self.account.openorders
        for o in ors:
            r = self.oe.get_updated_limit_order(o)
            assert r['price'] == o['price']

    def test_convert_asset(self):
        ticker = self.market.ticker()
        lp = ticker.get('latest', {}).get('price', None)
        r = self.oe.convert_asset(10, self.base_symbol, self.quote_symbol)
        assert lp * 10 == r

    def test_convert_fee(self):
        c = self.market.ticker()['core_exchange_rate']
        r = self.oe.convert_fee(1, self.base_symbol)

        assert float(c) == r

    def test_get_order(self):
        ors = self.account.openorders
        for o in ors:
            r = self.oe.get_order(o['id'])
            assert r['price'] == o['price']
            assert r['base'] == o['base']
            assert r['quote'] == o['quote']


if __name__ == '__main__':
    cur_dir = os.path.dirname(__file__)
    test_file = os.path.join(cur_dir, 'test_bitshares_engine_bak.py')
    print(test_file)
    pytest.main(['--capture=no', test_file])
