import uuid
import docker
import os.path
import pytest
import socket
import random
import time

from bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance
from bitshares.genesisbalance import GenesisBalance
from bitshares.account import Account
from bitshares.asset import Asset
from bitshares.exceptions import AssetDoesNotExistsException, AccountDoesNotExistsException

from bitsharesbase.account import PublicKey
from bitsharesbase.chains import known_chains

# Note: chain_id is generated from genesis.json, every time it's changes you need to get new chain_id from
# `bitshares.rpc.get_chain_properties()`
known_chains["TEST"]["chain_id"] = "c74ddb39b3a233445dd95d7b6fc2d0fa4ba666698db26b53855d94fffcc460af"

PRIVATE_KEYS = ['5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3']
DEFAULT_ACCOUNT = 'init0'

# Example how to split conftest.py into multiple files
# pytest_plugins = ['fixture_a.py', 'fixture_b.py']


@pytest.fixture(scope='session')
def session_id():
    """ Generate unique session id. This is needed in case testsuite may run in parallel on the same server, for example
        if CI/CD is being used. CI/CD infrastructure may run tests for each commit, so these tests should not influence
        each other.
    """
    return str(uuid.uuid4())


@pytest.fixture(scope='session')
def unused_port():
    """ Obtain unused port to bind some service
    """

    def _unused_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    return _unused_port


@pytest.fixture(scope='session')
def docker_manager():
    """ Initialize docker management client
    """
    return docker.from_env(version='auto')


@pytest.fixture(scope='session')
def bitshares_testnet(session_id, unused_port, docker_manager):
    """ Run bitshares-core inside local docker container

        Manual run example:
        $ docker run --name bitshares -p 0.0.0.0:8091:8091 -v `pwd`/cfg:/etc/bitshares/ bitshares/bitshares-core:testnet
    """
    port = unused_port()
    container = docker_manager.containers.run(
        image='bitshares/bitshares-core:testnet',
        name='bitshares-testnet-{}'.format(session_id),
        ports={'8091': port},
        volumes={
            '{}/tests/node_config'.format(os.path.abspath('.')): {'bind': '/etc/bitshares/', 'mode': 'ro'},
            '{}/tests/node_config/logging.ini'.format(os.path.abspath('.')): {
                'bind': '/var/lib/bitshares/logging.ini',
                'mode': 'ro',
            },
        },
        detach=True,
    )
    container.service_port = port
    time.sleep(3)
    yield container
    container.remove(v=True, force=True)


@pytest.fixture(scope='session')
def bitshares_instance(bitshares_testnet):
    """ Initialize BitShares instance connected to a local testnet
    """
    bitshares = BitShares(
        node='ws://127.0.0.1:{}'.format(bitshares_testnet.service_port), keys=PRIVATE_KEYS, num_retries=-1
    )
    # Shared instance allows to avoid any bugs when bitshares_instance is not passed explicitly when instantiating
    # objects
    set_shared_bitshares_instance(bitshares)
    # Todo: show chain params when connectiong to unknown network
    # https://github.com/bitshares/python-bitshares/issues/221

    return bitshares


@pytest.fixture(scope='session')
def claim_balance(bitshares_instance):
    """ Transfer balance from genesis into actual account
    """
    genesis_balance = GenesisBalance('1.15.0', bitshares_instance=bitshares_instance)
    genesis_balance.claim(account=DEFAULT_ACCOUNT)


@pytest.fixture(scope='session')
def bitshares(bitshares_instance, claim_balance):
    """ Prepare the testnet and return BitShares instance
    """
    return bitshares_instance


@pytest.fixture(scope='session')
def create_asset(bitshares):
    """ Create a new asset
    """

    def _create_asset(asset, precision):
        max_supply = 1000000000000000 / 10 ** precision if precision > 0 else 1000000000000000
        bitshares.create_asset(asset, precision, max_supply, account=DEFAULT_ACCOUNT)

    return _create_asset


@pytest.fixture(scope='session')
def issue_asset(bitshares):
    """ Issue asset shares to specified account

        :param str asset: asset symbol to issue
        :param float amount: amount to issue
        :param str to: account name to receive new shares
    """

    def _issue_asset(asset, amount, to):
        asset = Asset(asset, bitshares_instance=bitshares)
        asset.issue(amount, to)

    return _issue_asset


@pytest.fixture(scope='session')
def create_account(bitshares):
    """ Create new account
    """

    def _create_account(account):
        parent_account = Account(DEFAULT_ACCOUNT, bitshares_instance=bitshares)
        public_key = PublicKey.from_privkey(PRIVATE_KEYS[0], prefix=bitshares.prefix)
        bitshares.create_account(
            account,
            registrar=DEFAULT_ACCOUNT,
            referrer=parent_account['id'],
            referrer_percent=0,
            owner_key=public_key,
            active_key=public_key,
            memo_key=public_key,
            storekeys=False,
        )

    return _create_account


@pytest.fixture(scope='session')
def unused_account(bitshares):
    """ Find unexistent account
    """

    def _unused_account():
        _range = 100000
        while True:
            account = 'worker-{}'.format(random.randint(1, _range))  # nosec
            try:
                Account(account, bitshares_instance=bitshares)
            except AccountDoesNotExistsException:
                return account

    return _unused_account


@pytest.fixture(scope='session')
def prepare_account(bitshares, unused_account, create_account, create_asset, issue_asset):
    """ Ensure an account with specified amounts of assets. Account must not exist!

        :param dict assets: assets to credit account balance with
        :param str account: (optional) account name to prepare (default: generate random account name)
        :return: account name
        :rtype: str

        Example assets: {'FOO': 1000, 'BAR': 5000}
    """

    def _prepare_account(assets, account=None):
        # Account name is optional, take unused account name if not specified
        if not account:
            account = unused_account()

        create_account(account)

        for asset, amount in assets.items():
            # If asset does not exists, create it
            try:
                Asset(asset, bitshares_instance=bitshares)
            except AssetDoesNotExistsException:
                create_asset(asset, 5)

            if asset == 'TEST':
                bitshares.transfer(account, amount, 'TEST', memo='prepare account', account=DEFAULT_ACCOUNT)
            else:
                issue_asset(asset, amount, account)

        return account

    return _prepare_account
