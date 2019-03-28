from dexbot.config import Config

from bitshares.instance import shared_bitshares_instance
from bitshares.account import Account
from bitshares.asset import Asset
from bitshares.exceptions import KeyAlreadyInStoreException, AccountDoesNotExistsException, AssetDoesNotExistsException
from bitsharesbase.account import PrivateKey


class ConfigValidator:
    """ Config validation methods

        :param bitshares.BitShares: BitShares instance
    """

    def __init__(self, bitshares_instance):
        self.bitshares = bitshares_instance or shared_bitshares_instance()

    def validate_account_name(self, account):
        """ Check whether bitshares account exists

            :param str account: bitshares account name
        """
        if not account:
            return False
        try:
            Account(account, bitshares_instance=self.bitshares)
            return True
        except AccountDoesNotExistsException:
            return False

    def validate_private_key(self, account, private_key):
        """ Check whether private key is associated with account

            :param str account: bitshares account name
            :param str private_key: private key
        """
        wallet = self.bitshares.wallet
        if not private_key:
            # Check if the account is already in the database
            accounts = wallet.getAccounts()
            if any(account == d['name'] for d in accounts):
                return True
            return False

        try:
            pubkey = format(PrivateKey(private_key).pubkey, self.bitshares.prefix)
        except ValueError:
            return False

        # Load all accounts with corresponding public key from the blockchain
        accounts = wallet.getAllAccounts(pubkey)
        account_names = [account['name'] for account in accounts]

        if account in account_names:
            return True
        else:
            return False

    def validate_private_key_type(self, account, private_key):
        """ Check whether private key type is "active" or "owner"

            :param str account: bitshares account name
            :param str private_key: private key
        """
        account = Account(account)
        pubkey = format(PrivateKey(private_key).pubkey, self.bitshares.prefix)
        key_type = self.bitshares.wallet.getKeyType(account, pubkey)
        if key_type != 'active' and key_type != 'owner':
            return False
        return True

    @staticmethod
    def validate_worker_name(worker_name, old_worker_name=None):
        """ Check whether worker name is unique or not

            :param str worker_name: name of the new worker
            :param str old_worker_name: old name of the worker
        """
        if old_worker_name != worker_name:
            worker_names = Config().workers_data.keys()
            # Check that the name is unique
            if worker_name in worker_names:
                return False
            return True
        return True

    @staticmethod
    def validate_account_not_in_use(account):
        """ Check whether account is already used for another worker or not

            :param str account: bitshares account name
        """
        workers = Config().workers_data
        for worker_name, worker in workers.items():
            if worker['account'] == account:
                return False
        return True

    def validate_asset(self, asset):
        """ Check whether asset is exists on the network

            :param str asset: asset name
        """
        try:
            Asset(asset, bitshares_instance=self.bitshares)
            return True
        except AssetDoesNotExistsException:
            return False

    @staticmethod
    def validate_market(base_asset, quote_asset):
        """ Check whether market tickers is not the same

            :param str base_asset: BASE asset ticker
            :param str quote_asset: QUOTE asset ticker
        """
        return base_asset.lower() != quote_asset.lower()

    def add_private_key(self, private_key):
        """ Add private key into local wallet

            :param str private_key: private key
        """
        wallet = self.bitshares.wallet
        try:
            wallet.addPrivateKey(private_key)
        except KeyAlreadyInStoreException:
            # Private key already added
            pass
