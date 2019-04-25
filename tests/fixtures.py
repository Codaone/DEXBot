# -*- coding: utf-8 -*-

from bitshares import BitShares
from bitshares.instance import set_shared_blockchain_instance
from bitshares.account import Account
import os
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
    if bitshares.nobroadcast:
        raise AssertionError('No broadcasting, no actual transactions!')


def fixture_data_RO():
    # User needs to put a key in
    wif = os.environ['DEXBOT_TEST_RO_WIF']
    account_name = os.environ['DEXBOT_TEST_RO_ACCOUNT']
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


def get_balance(symbol='TEST'):
    account_name = os.environ['DEXBOT_TEST_RO_ACCOUNT']
    account = Account(account_name)
    return account.balance(symbol)


def fixture_data_KH():
    '''King or the hill'''
    # User needs to put a key in
    wif = os.environ['DEXBOT_TEST_KH_WIF']
    account_name = os.environ['DEXBOT_TEST_KH_ACCOUNT']
    init_default(account_name=account_name, wif=wif)
    TEST_CONFIG = {
        'node': 'wss://testnet.nodes.bitshares.ws',
        'workers': {
                'worker 1': {
                    'account': account_name,
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
