# -*- coding: utf-8 -*-

from bitshares import BitShares
from bitshares.instance import set_shared_blockchain_instance
nodes = [
    "ws://api.weaccount.cn:9777",
    "ws://api.btspp.io:9777",
    "wss://testnet.bts.dcn.cx/ws",
    "wss://testnet.dex.trading/",
    "wss://testnet-eu.bitshares.apasia.tech/ws",
    "wss://testnet.bitshares.apasia.tech/ws",
    "wss://node.testnet.bitshares.eu"
]


def init_default(account_name='', wif=''):
    # default wifs key for testing
    wifs = [wif]
    # bitshares instance
    bitshares = BitShares(
        nodes, keys=wifs, nobroadcast=False, num_retries=1
    )

    # Set defaults
    set_shared_blockchain_instance(bitshares)
    bitshares.set_default_account(account_name)

    # Ensure we are  going to transaction anythin on chain!
    assert bitshares.nobroadcast == False


def fixture_data(type=''):
    if type == 'RO':
        init_default(account_name='dexbot-test1',
                     wif='5J6r6kzPcKyrhdUGBSxA95spFokg3uj82k5Npj54Dfc4TcACeY8')
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
    elif type == 'KH':
        init_default(account_name='dexbot-test3',
                     wif='5JAfKCfrJDt7UBUCjqoG6SnP1FUQt3G2YvPDCowGNScmyKNLrxL')
        TEST_CONFIG = {
            'node': 'wss://testnet.nodes.bitshares.ws',
            'workers': {
                    'worker 1': {
                        'account': 'dexbot-test3',
                        'buy_order_amount': 1.0,
                        'buy_order_size_threshold': 0.0,
                        'fee_asset': 'TEST',
                        'lower_bound': 1,
                        'market': 'DEXBOT/TEST',
                        'min_order_lifetime': 60,
                        'mode': 'both',
                        'module': 'dexbot.strategies.king_of_the_hill',
                        'relative_order_size': True,
                        'sell_order_amount': 1.0,
                        'sell_order_size_threshold': 0.0,
                        'upper_bound': 0.001
                    }
            }
        }
        return TEST_CONFIG
    elif type == 'OE':
        account_name = 'dexbot-test4'
        wif = '5HzX4ZJCEzT4SkNoWnhtwruFa8Eco2fwRktd8ZSLmmUGmFz7X3n'
        init_default(account_name=account_name, wif=wif)
        TEST_CONFIG = {
            'node': 'wss://testnet.nodes.bitshares.ws',
            'workers': {
                    'worker 1': {
                        'account': account_name,
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
    else:
        raise ValueError('value error!')


if __name__ == '__main__':
    print(fixture_data('RO'))
    print(fixture_data('HK'))
    print(fixture_data('OE'))
