from dexbot.pricefeeds.bitshares_feed import BitsharesPriceFeed
from bitshares.bitshares import BitShares
from grapheneapi.exceptions import RPCError
from bitshares.market import Market
import logging
import os
import pytest
import math
import operator
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)


class Test_PriceFeed:
    def setup_class(self):
        test_config = {'node': "wss://bts.open.icowallet.net/ws",
                       'market': 'CNY:BTS'}
        assert test_config['node'] == "wss://bts.open.icowallet.net/ws"
        self.bts = BitShares(node=test_config['node'])
        assert test_config['market'] == 'CNY:BTS'
        self.market = Market(test_config['market'])

        self.pf = BitsharesPriceFeed(
            market=self.market, bitshares_instance=self.bts)

        assert self.bts.info == self.pf.bitshares.info
        assert self.market == self.pf.market
        assert self.pf.fetch_depth == 8
        assert self.pf.ticker == self.pf.market.ticker

    def teardown_class(self):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_get_ticker(self):
        ticker = self.pf.ticker
        assert ticker() == self.market.ticker()

    def test_get_limit_orders(self):
        # test default=1
        mkt_orders = self.pf.get_limit_orders()
        assert len(mkt_orders) == 2
        # test depth=0
        mkt_orders = self.pf.get_limit_orders(depth=0)
        assert len(mkt_orders) == 0
        # test depth=-1
        with pytest.raises(RPCError):
            mkt_orders = self.pf.get_limit_orders(depth=-1)
        # bitshares Assert limit <= 300
        mkt_orders = self.pf.get_limit_orders(depth=300)
        assert len(mkt_orders) == 600
        # test depth=10000
        with pytest.raises(RPCError):
            mkt_orders = self.pf.get_limit_orders(depth=10000)

    def test_get_orderbook_orders(self):
        # test default=1
        orderbook = self.pf.get_orderbook_orders()
        assert len(orderbook['bids']) == 1
        assert len(orderbook['asks']) == 1
        # test depth=-1
        with pytest.raises(RPCError):
            orderbook = self.pf.get_orderbook_orders(depth=-1)
        # test depth=0
        orderbook = self.pf.get_orderbook_orders(depth=0)
        assert len(orderbook['bids']) == 0
        assert len(orderbook['asks']) == 0
        # test depth=50
        orderbook = self.pf.get_orderbook_orders(depth=50)
        assert len(orderbook['bids']) == 50
        assert len(orderbook['asks']) == 50
        # test depth=60 orderbook() call has hard-limit of depth=50
        with pytest.raises(RPCError):
            orderbook = self.pf.get_orderbook_orders(depth=60)

    def test_filter_buy_orders(self):
        buy_orders = self.pf.get_market_buy_orders(depth=10)
        price_list = []
        for o in buy_orders:
            if o['base']['symbol'] == self.market['base']['symbol']:
                price_list.append(o['price'])
        asc = sorted(price_list, reverse=False)
        desc = sorted(price_list, reverse=True)

        asc_orders = self.pf.filter_buy_orders(buy_orders, sort='ASC')
        asc_orders_prices = []
        for o in asc_orders:
            asc_orders_prices.append(o['price'])

        desc_orders = self.pf.filter_buy_orders(buy_orders, sort='DESC')
        desc_orders_prices = []
        for o in desc_orders:
            desc_orders_prices.append(o['price'])

        assert asc == asc_orders_prices
        assert desc == desc_orders_prices

        assert operator.eq(asc, asc_orders_prices)
        assert operator.eq(desc, desc_orders_prices)

    def test_filter_sell_orders(self):
        sell_orders = self.pf.get_market_sell_orders(depth=10)

        price_list = []
        for o in sell_orders:
            if o['base']['symbol'] != self.market['base']['symbol']:
                price_list.append(o['price'])
        asc = sorted(price_list, reverse=False)
        desc = sorted(price_list, reverse=True)

        asc_orders = self.pf.filter_sell_orders(sell_orders, sort='ASC')
        asc_orders_prices = []
        for o in asc_orders:
            asc_orders_prices.append(o['price'])

        desc_orders = self.pf.filter_sell_orders(sell_orders, sort='DESC')
        desc_orders_prices = []
        for o in desc_orders:
            desc_orders_prices.append(o['price'])

        assert asc == asc_orders_prices
        assert desc == desc_orders_prices

        assert operator.eq(asc, asc_orders_prices)
        assert operator.eq(desc, desc_orders_prices)

    def test_get_highest_market_buy_order(self):
        buy_orders = self.pf.get_market_buy_orders(depth=10)
        price_list = []
        for o in buy_orders:
            price_list.append(o['price'])
        max_price = max(price_list)

        highest = self.pf.get_highest_market_buy_order(buy_orders)

        assert max_price == highest['price']

    def test_get_lowest_market_sell_order(self):
        sell_orders = self.pf.get_market_sell_orders(depth=10)
        price_list = []
        for o in sell_orders:
            price_list.append(o['price'])
        min_price = min(price_list)

        lowest = self.pf.get_lowest_market_sell_order(sell_orders)

        assert min_price == lowest['price']

    def test_get_market_buy_orders(self):
        buy_orders = self.pf.get_market_buy_orders(depth=10)
        for o in buy_orders:
            assert o['base']['symbol'] == self.market['base']['symbol']

    def test_get_market_sell_orders(self):
        sell_orders = self.pf.get_market_sell_orders(depth=10)
        for o in sell_orders:
            assert o['base']['symbol'] == self.market['base']['symbol']

    def test_get_market_buy_price(self):
        highestBid = self.market.ticker().get('highestBid')
        mkt_buy_price = self.pf.get_market_buy_price(
            quote_amount=0, base_amount=0)

        assert float(highestBid) == mkt_buy_price

        mkt_buy_price = self.pf.get_market_buy_price(
            quote_amount=10, base_amount=1)

    def test_get_market_sell_price(self):
        lowestAsk = self.market.ticker().get('lowestAsk')
        mkt_sell_price = self.pf.get_market_sell_price(
            quote_amount=0, base_amount=0)

        assert float(lowestAsk) == mkt_sell_price

        mkt_sell_price = self.pf.get_market_sell_price(
            quote_amount=10, base_amount=1)

    def test_get_market_center_price(self):
        lowestAsk = self.market.ticker().get('lowestAsk')
        highestBid = self.market.ticker().get('highestBid')
        cp = highestBid * math.sqrt(lowestAsk / highestBid)
        center_price = self.pf.get_market_center_price(
            base_amount=0, quote_amount=0, suppress_errors=False)

        assert float(cp) == center_price

    def test_get_market_spread(self):
        lowestAsk = self.market.ticker().get('lowestAsk')
        highestBid = self.market.ticker().get('highestBid')
        spread = lowestAsk / highestBid - 1
        mkt_spread = self.pf.get_market_spread(quote_amount=0, base_amount=0)

        assert spread == mkt_spread

    def test_sort_orders_by_price(self):
        buy_orders = self.pf.get_market_buy_orders(depth=10)
        price_list = []
        for o in buy_orders:
            if o['base']['symbol'] == self.market['base']['symbol']:
                price_list.append(o['price'])
        asc = sorted(price_list, reverse=False)
        desc = sorted(price_list, reverse=True)

        asc_orders = self.pf.sort_orders_by_price(buy_orders, sort='ASC')
        asc_orders_prices = []
        for o in asc_orders:
            asc_orders_prices.append(o['price'])

        desc_orders = self.pf.sort_orders_by_price(buy_orders, sort='DESC')
        desc_orders_prices = []
        for o in desc_orders:
            desc_orders_prices.append(o['price'])

        assert asc == asc_orders_prices
        assert desc == desc_orders_prices

        assert operator.eq(asc, asc_orders_prices)
        assert operator.eq(desc, desc_orders_prices)


if __name__ == '__main__':
    cur_dir = os.path.dirname(__file__)
    test_file = os.path.join(cur_dir, 'test_bitshares_feed.py')
    pytest.main(['--capture=no', test_file])
