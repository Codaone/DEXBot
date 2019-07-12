# def test_configure(ro_worker,config):
#     worker=ro_worker
#     cf = worker.config
#
#     assert config == cf


# def test_error(ro_worker):
#     '''Event method return None'''
#     worker=ro_worker
#     worker.error()
#     assert worker.disabled == True

# def test_amount_to_sell(ro_worker):
#     worker = ro_worker
#     print(worker)
#     print(worker.sell_price)
#     sell_price = worker.sell_price
#
#     assert sell_price == None
#
#     worker.calculate_order_prices()
#     amount_to_sell = worker.amount_to_sell
#
#     amount = worker['workers']['ro_worker']['amount']
#
#     assert amount_to_sell == amount

def test_amount_to_buy(ro_worker):
    worker=ro_worker
    print(worker.sell_price)
    print(worker.buy_price)
    print(worker.center_price)
    # worker.calculate_order_prices()
    #
    # amount_to_buy = worker.amount_to_buy


    # assert amount_to_buy == amount_to_buy_cf

# def test_calculate_order_prices(self):
#     # no return
#     calculate_prices = self.relative_strategy.calculate_order_prices()
#     logging.info(calculate_prices)
#     assert calculate_prices is None
#
#     buy_price = self.relative_strategy.buy_price
#     sell_price = self.relative_strategy.sell_price
#     center_price = self.relative_strategy.center_price
#     spread = self.relative_strategy.spread
#     logging.info('buy_price:{}'.format(buy_price))
#     logging.info('sell_price:{}'.format(sell_price))
#     logging.info('center_price:{}'.format(center_price))
#     logging.info('spread:{}'.format(spread))
#
#     assert self.relative_strategy.center_price == center_price
#
#     buy_price_ca = center_price / math.sqrt(1 + spread)
#     logging.info('buy_price_ca:{}'.format(buy_price_ca))
#
#     sell_price_ca = center_price * math.sqrt(1 + spread)
#     logging.info('sell_price_ca:{}'.format(sell_price_ca))
#
#     assert buy_price == buy_price_ca
#
#     assert sell_price == sell_price_ca
#
# def test_update_orders(self):
#     self.relative_strategy.update_orders()
#     # 0.2927 3.2530904359141184
#     from bitshares.market import Market
#     market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
#     for o in market.accountopenorders():
#         if o.get('for_sale') == 1:
#             assert o.get('price') == 3.2530904359141184
#
#         else:
#             assert o.get('price') == 0.2927
#
# def test_calculate_center_price(self):
#     from bitshares.market import Market
#     market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
#     highest_bid = market.ticker().get('highestBid')
#     lowest_ask = market.ticker().get('lowestAsk')
#
#     cp = highest_bid * math.sqrt(lowest_ask / highest_bid)
#     center_price = self.relative_strategy.calculate_center_price()
#
#     assert cp == center_price
#
# def test_calculate_asset_offset(self):
#     from bitshares.market import Market
#     center_price = 1
#     spread = 0.5
#     order_ids = []
#
#     total_balance = self.relative_strategy.count_asset(order_ids)
#     total = (total_balance['quote'] * center_price) + total_balance['base']
#
#     if not total:  # Prevent division by zero
#         base_percent = quote_percent = 0.5
#     else:
#         base_percent = total_balance['base'] / total
#         quote_percent = 1 - base_percent
#
#     logging.info(base_percent)
#     logging.info(quote_percent)
#
#     market = Market(self.TEST_CONFIG['workers']['worker 1']['market'])
#     highest_bid = float(market.ticker().get('highestBid'))
#     lowest_ask = float(market.ticker().get('lowestAsk'))
#
#     logging.info(highest_bid)
#     logging.info(lowest_ask)
#
#     lowest_price = center_price / (1 + spread)
#     highest_price = center_price * (1 + spread)
#
#     logging.info(lowest_price)
#     logging.info(highest_price)
#
#     lowest_price = max(lowest_price, highest_bid)
#     highest_price = min(highest_price, lowest_ask)
#
#     logging.info(lowest_price)
#     logging.info(highest_price)
#
#     r = math.pow(highest_price, base_percent) * \
#         math.pow(lowest_price, quote_percent)
#
#     logging.info(r)
#
#     calculate_asset_offset = self.relative_strategy.calculate_asset_offset(
#         center_price=center_price, order_ids=[], spread=spread)
#
#     logging.info(calculate_asset_offset)
#     assert calculate_asset_offset == r
#
# def test_calculate_manual_offset(self):
#     center_price = 1
#     manual_offset = 0.1
#
#     calculate_offset = self.relative_strategy.calculate_manual_offset(
#         center_price=center_price, manual_offset=manual_offset)
#     logging.info(calculate_offset)
#
#     assert calculate_offset == center_price * (1 + manual_offset)
#
#     manual_offset = -0.1
#
#     calculate_offset = self.relative_strategy.calculate_manual_offset(
#         center_price=center_price, manual_offset=manual_offset)
#     logging.info(calculate_offset)
#
#     assert calculate_offset == center_price / (1 + abs(manual_offset))
#
# def test_check_orders(self):
#     self.relative_strategy.check_orders()
#
#
#
