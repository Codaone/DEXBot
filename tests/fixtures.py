# -*- coding: utf-8 -*-
from pprint import pprint

from bitshares import BitShares
from bitshares.instance import set_shared_blockchain_instance
from bitshares.account import Account
# default wifs key for testing
wifs = [
    "5J6r6kzPcKyrhdUGBSxA95spFokg3uj82k5Npj54Dfc4TcACeY8"
]
nodes = [
    "ws://api.weaccount.cn:9777",
    "ws://api.btspp.io:9777",
    "wss://testnet.bts.dcn.cx/ws",
    "wss://testnet.dex.trading/",
    "wss://testnet-eu.bitshares.apasia.tech/ws",
    "wss://testnet.bitshares.apasia.tech/ws",
    "wss://node.testnet.bitshares.eu"
]
# bitshares instance
bitshares = BitShares(
    nodes, keys=wifs, nobroadcast=False, num_retries=1
)
config = bitshares.config

# Set defaults
set_shared_blockchain_instance(bitshares)
bitshares.set_default_account('dexbot-test1')

# Ensure we are  going to transaction anythin on chain!
assert not bitshares.nobroadcast


def fixture_data():
    # Clear tx buffer
    # bitshares.clear()

    # Account.clear_cache()

    TEST_CONFIG = {
        'node': 'wss://testnet.nodes.bitshares.ws',
        'workers': {
                'worker 1': {
                    'account': 'dexbot-test1',
                    'amount': 1.0,
                    'center_price': 0.3,
                    'center_price_depth': 0.0,
                    'center_price_dynamic': False,
                    'center_price_offset': False,
                    'custom_expiration': False,
                    'dynamic_spread': False,
                    'dynamic_spread_factor': 1.0,
                    'expiration_time': 157680000.0,
                    'external_feed': False,
                    'external_price_source': 'null',
                    'fee_asset': 'TEST',
                    'manual_offset': 0.0,
                    'market': 'TEST/DEXBOT',
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
    return TEST_CONFIG


def get_balance(symbol='TEST'):
    account = Account('dexbot-test1')
    return account.balance(symbol)


if __name__ == '__main__':
    pprint(fixture_data())
    pprint(get_balance('TEST'))
    pprint(bitshares.config)
