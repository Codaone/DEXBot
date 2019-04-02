import pytest
from dexbot.strategies.relative_orders import Strategy
from bitshares import BitShares
from bitshares.notify import Notify
import logging
logging.basicConfig(format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s',
                    level=logging.WARNING)
class Test_Strategy:
    def setup_class(self):
        TEST_CONFIG = {
            'node':'wss://bts.open.icowallet.net/ws',
            'workers':{
                'bts0207':{
                    'account': 'bts0207',
                    'amount': 1,
                    'center_price': 0.3,
                    'center_price_depth': 0.0,
                    'center_price_dynamic': True,
                    'center_price_offset': False,
                    'custom_expiration': False,
                    'dynamic_spread': False,
                    'dynamic_spread_factor': 1.0,
                    'expiration_time': 157680000.0,
                    'external_feed': False,
                    'external_price_source': 'null',
                    'fee_asset': 'BTS',
                    'manual_offset': 0.0,
                    'market': 'BTS/CNY',
                    'market_depth_amount': 0.0,
                    'module': 'dexbot.strategies.relative_orders',
                    'partial_fill_threshold': 30.0,
                    'price_change_threshold': 2.0,
                    'relative_order_size': False,
                    'reset_on_partial_fill': True,
                    'reset_on_price_change': False,
                    'spread': 5.0
                }
            }
        } 
        nodeList=["wss://bts.open.icowallet.net/ws",
                "wss://bitshares.dacplay.org/ws",
                "wss://ws.gdex.top",
                "wss://api.bts.ai"
                ]
        self.bitShares = BitShares(nodeList)#,nobroadcast=True)
        if self.bitShares.wallet.locked():
            self.bitShares.wallet.unlock('123')
        self.relative_strategy=Strategy(name='bts0207',config=TEST_CONFIG,bitshares_instance=self.bitShares) 
    def teardown_class(self):
        pass
    def setup_method(self):
        if self.bitShares.wallet.locked():
            self.bitShares.wallet.unlock('123')
    def teardown_method(self):
        pass
    def test_configure(self):
        from dexbot.strategies.config_parts.relative_config import ConfigElement
        account=ConfigElement(key='account', type='string', default='', title='Account', description='BitShares account name for the bot to operate with', extra='')
        cf=Strategy.configure()
        logging.warning(account)
        assert account in cf
    def test_configure_details(self):
        cf_details=Strategy.configure_details()
        logging.warning(cf_details)
        assert cf_details==[]
    def test_error(self):
        r=self.relative_strategy.error()
        logging.warning(r)
        assert r==None
    def test_tick(self):
        r=self.relative_strategy.tick('0228fec41a799ec45c218cb441ae249cef1bbcb2')
        logging.warning(r)
        assert None==r
    def test_amount_to_sell(self):
        self.relative_strategy.sell_price=1
        amount_to_sell=self.relative_strategy.amount_to_sell
        logging.warning(amount_to_sell)
    def test_amount_to_buy(self):
        self.relative_strategy.buy_price=1
        amount_to_buy=self.relative_strategy.amount_to_buy
        logging.warning(amount_to_buy)
    def test_calculate_order_prices(self):
        calculate_order_prices=self.relative_strategy.calculate_order_prices()
        logging.warning(calculate_order_prices)
        assert None==calculate_order_prices
    def test_update_orders(self):
        r=self.relative_strategy.update_orders()
        logging.warning(r)
        assert None==r
    def test_calculate_center_price(self):
        center_price = self.relative_strategy.calculate_center_price()
        logging.warning(center_price)
        assert center_price!=None
    def test_calculate_asset_offset(self):
        calculate_asset_offset=self.relative_strategy.calculate_asset_offset(center_price=1,order_ids=[],spread=0.5)
        logging.warning(calculate_asset_offset)
        assert calculate_asset_offset!=None
    def test_calculate_manual_offset(self):
        calculate_manual_offset=self.relative_strategy.calculate_manual_offset(center_price=0,manual_offset=0.1)
        logging.warning(calculate_manual_offset)
        assert calculate_manual_offset!=None
    def test_check_orders(self):
        r=self.relative_strategy.check_orders()
        logging.warning(r)
        assert r==None


#--------------------------test------------------------
if __name__=='__main__':
    # a=Test_Strategy()
    # notify=Notify(
    #     markets=['BTS:CNY'],
    #     accounts=['BTS0207'],
    #     on_market=a.test_tick,
    #     # on_account=self.on_account,
    #     # on_block=self.on_block,
    #     # bitshares_instance=self.bitshares
    # )
    # notify.listen()
    path='/Users/jacking/Documents/GitHub/env/DEXBot/tests/test_dexbot/test_strategies/'
    pytest.main([path+'test_relative_orders.py'])