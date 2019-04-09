# -*- coding: utf-8 -*-
from pprint import pprint

from bitshares import BitShares
from bitshares.instance import set_shared_blockchain_instance

# default wifs key for testing
wifs = [
    "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3",
    "5KCBDTcyDqzsqehcb52tW5nU6pXife6V2rX9Yf7c3saYSzbDZ5W",
]

# bitshares instance
bitshares = BitShares(
    "wss://node.bitshares.eu", keys=wifs, nobroadcast=True, num_retries=1
)
# Set defaults
bitshares.set_default_account("init0")
set_shared_blockchain_instance(bitshares)

# Ensure we are not going to transaction anythin on chain!
assert bitshares.nobroadcast


def fixture_data():
    # Clear tx buffer
    bitshares.clear()

    TEST_CONFIG = {
        'node': 'wss://node.bitshares.eu',
        'workers': {
                'worker 1': {
                    'account': 'init0',
                    'amount': 1.0,
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
                    'market': 'TEST:GOLD',
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


if __name__ == '__main__':
    pprint(fixture_data())
