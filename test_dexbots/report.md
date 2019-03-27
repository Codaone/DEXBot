# relative_orders
1. When there is no order in the test node because there is no order in the market, Market. ticker () will make a mistake and the program will not catch it.Market. ticker ()，Many methods are used, like initialization methods.
2. When center_price is None, the program does not catch it.unsupported operand type(s) for /: 'NoneType' and 'float'
3. When the balance of base assets in an account is zero, an error is prompted:Insufficient buy balance, needed 0.3442 CNY
4. When call `self.relative_strategy=Strategy(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares)`in testusecase class,error prompted:wallet unlocked.
5. 当账户是bts0207的时候，测试数据：{'account': 'bts0207', 'amount': 1, 'center_price': 0.3, 'center_price_depth': 0.0, 'center_price_dynamic': True, 'center_price_offset': False, 'custom_expiration': False, 'dynamic_spread': False, 'dynamic_spread_factor': 1.0, 'expiration_time': 157680000.0, 'external_feed': False, 'external_price_source': 'null', 'fee_asset': 'BTS', 'manual_offset': 0.0, 'market': 'BTS/CNY', 'market_depth_amount': 0.0, 'module': 'dexbot.strategies.relative_orders', 'partial_fill_threshold': 30.0, 'price_change_threshold': 2.0, 'relative_order_size': False, 'reset_on_partial_fill': True, 'reset_on_price_change': False, 'spread': 5.0}错误提示：`======================================================================
    ERROR: test_amount_to_sell (__main__.test_Strategy)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
  File "/Users/jacking/Documents/GitHub/env/DEXBot/test_dexbots/test_dexbot/test_strategies/test_relative_orders.py", line 99, in test_amount_to_sell
    amount_to_sell=self.relative_strategy.amount_to_sell
  File "/Users/jacking/Documents/GitHub/env/lib/python3.7/site-packages/dexbot-0.9.19-py3.7.egg/dexbot/strategies/relative_orders.py", line 184, in amount_to_sell
    amount * self.sell_price < 2 * 10 ** -self.market['base']['precision']):
    TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'`
6. amount=0 order size boundary test ok
7. order size :amount=None ======================================================================
     ERROR: setUpClass (__main__.test_Strategy) 
    ----------------------------------------------------------------------
    Traceback (most recent call last):
  File "/Users/jacking/Documents/GitHub/env/DEXBot/test_dexbots/test_dexbot/test_strategies/test_relative_orders.py", line 101, in setUpClass
    self.relative_strategy=Strategy(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares)
  File "/Users/jacking/Documents/GitHub/env/lib/python3.7/site-packages/dexbot-0.9.19-py3.7.egg/dexbot/strategies/relative_orders.py", line 113, in __init__
    self.order_size = float(self.worker.get('amount', 1))
    TypeError: float() argument must be a string or a number, not 'NoneType'
8.  order size :amount=99999999 
    Insufficient buy balance, needed 37958567.5416 CNY
    Insufficient sell balance, needed 99999999.0 BTS
9. center_price:0 ok
10. center_price:None ok
11. center_price:99999999 ok
12. center_price_depth:0 ok
13. 'center_price_depth': None ======================================================================
    ERROR: test_calculate_order_prices (__main__.test_Strategy)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
  File "/Users/jacking/Documents/GitHub/env/DEXBot/test_dexbots/test_dexbot/test_strategies/test_relative_orders.py", line 139, in test_calculate_order_prices
    calculate_order_prices=self.relative_strategy.calculate_order_prices()
  File "/Users/jacking/Documents/GitHub/env/lib/python3.7/site-packages/dexbot-0.9.19-py3.7.egg/dexbot/strategies/relative_orders.py", line 220, in calculate_order_prices
    if self.center_price_depth > 0 and not self.external_feed:
    TypeError: '>' not supported between instances of 'NoneType' and 'int'

    ======================================================================
    ERROR: test_update_orders (__main__.test_Strategy)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
  File "/Users/jacking/Documents/GitHub/env/DEXBot/test_dexbots/test_dexbot/test_strategies/test_relative_orders.py", line 142, in test_update_orders
    self.relative_strategy.update_orders()
  File "/Users/jacking/Documents/GitHub/env/lib/python3.7/site-packages/dexbot-0.9.19-py3.7.egg/dexbot/strategies/relative_orders.py", line 252, in update_orders
    self.calculate_order_prices()
  File "/Users/jacking/Documents/GitHub/env/lib/python3.7/site-packages/dexbot-0.9.19-py3.7.egg/dexbot/strategies/relative_orders.py", line 220, in calculate_order_prices
    if self.center_price_depth > 0 and not self.external_feed:
    TypeError: '>' not supported between instances of 'NoneType' and 'int'
14. center_price_depth:999999999 ok
15. center_price_dynamic: true ======================================================================
    ERROR: setUpClass (__main__.test_Strategy)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
  File "/Users/jacking/Documents/GitHub/env/DEXBot/test_dexbots/test_dexbot/test_strategies/test_relative_orders.py", line 77, in setUpClass
    'center_price_dynamic': true,
    NameError: name 'true' is not defined
16. center_price_dynamic: None ok this should error  
17. center_price_dynamic:9999 ok 
18. 
