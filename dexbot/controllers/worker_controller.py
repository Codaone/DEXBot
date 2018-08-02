import collections
import re

from dexbot.views.errors import gui_error
from dexbot.config import Config
from dexbot.views.notice import NoticeDialog
from dexbot.views.confirmation import ConfirmationDialog
from dexbot.views.strategy_form import StrategyFormWidget

import bitshares
from bitshares.instance import shared_bitshares_instance
from bitshares.asset import Asset
from bitshares.account import Account
from bitsharesbase.account import PrivateKey
from PyQt5 import QtGui


class WorkerController:

    def __init__(self, view, bitshares_instance, mode):
        self.view = view
        self.bitshares = bitshares_instance or shared_bitshares_instance()
        self.mode = mode

    @property
    def strategies(self):
        strategies = collections.OrderedDict()
        strategies['dexbot.strategies.relative_orders'] = {
            'name': 'Relative Orders',
            'form_module': 'dexbot.views.ui.forms.relative_orders_widget_ui'
        }
        strategies['dexbot.strategies.staggered_orders'] = {
            'name': 'Staggered Orders',
            'form_module': 'dexbot.views.ui.forms.staggered_orders_widget_ui'
        }
        return strategies

    @classmethod
    def get_strategies(cls):
        """ Class method for getting the strategies
        """
        return cls(None, None, None).strategies

    @property
    def base_assets(self):
        assets = [
            'USD', 'OPEN.BTC', 'CNY', 'BTS', 'BTC'
        ]
        return assets

    @staticmethod
    def is_worker_name_valid(worker_name):
        worker_names = Config().workers_data.keys()
        # Check that the name is unique
        if worker_name in worker_names:
            return False
        return True

    def is_asset_valid(self, asset):
        try:
            Asset(asset, bitshares_instance=self.bitshares)
            return True
        except bitshares.exceptions.AssetDoesNotExistsException:
            return False

    def account_exists(self, account):
        try:
            Account(account, bitshares_instance=self.bitshares)
            return True
        except bitshares.exceptions.AccountDoesNotExistsException:
            return False

    def is_account_valid(self, account, private_key):
        if not private_key or not account:
            return False

        wallet = self.bitshares.wallet
        try:
            pubkey = format(PrivateKey(private_key).pubkey, self.bitshares.prefix)
        except ValueError:
            return False

        accounts = wallet.getAllAccounts(pubkey)
        account_names = [account['name'] for account in accounts]

        if account in account_names:
            return True
        else:
            return False

    @staticmethod
    def is_account_in_use(account):
        workers = Config().workers_data
        for worker_name, worker in workers.items():
            if worker['account'] == account:
                return True
        return False

    def add_private_key(self, private_key):
        wallet = self.bitshares.wallet
        try:
            wallet.addPrivateKey(private_key)
        except ValueError:
            # Private key already added
            pass

    @staticmethod
    def get_unique_worker_name():
        """ Returns unique worker name "Worker %n", where %n is the next available index
        """
        index = 1
        workers = Config().workers_data.keys()
        worker_name = "Worker {0}".format(index)
        while worker_name in workers:
            worker_name = "Worker {0}".format(index)
            index += 1

        return worker_name

    def get_strategy_name(self, module):
        return self.strategies[module]['name']

    @staticmethod
    def get_strategy_module(worker_data):
        return worker_data['module']

    @staticmethod
    def get_assets(worker_data):
        return re.split("[/:]", worker_data['market'])

    def get_base_asset(self, worker_data):
        return self.get_assets(worker_data)[1]

    def get_quote_asset(self, worker_data):
        return self.get_assets(worker_data)[0]

    @staticmethod
    def get_account(worker_data):
        return worker_data['account']

    @staticmethod
    def handle_save_dialog():
        dialog = ConfirmationDialog('Saving the worker will cancel all the current orders.\n'
                                    'Are you sure you want to do this?')
        return dialog.exec_()

    @gui_error
    def change_strategy_form(self, worker_data=None):
        # Make sure the container is empty
        for index in reversed(range(self.view.strategy_container.count())):
            self.view.strategy_container.itemAt(index).widget().setParent(None)

        strategy_module = self.view.strategy_input.currentData()
        self.view.strategy_widget = StrategyFormWidget(self, strategy_module, worker_data)
        self.view.strategy_container.addWidget(self.view.strategy_widget)

        # Resize the dialog to be minimum possible height
        width = self.view.geometry().width()
        self.view.setMinimumHeight(0)
        self.view.resize(width, 1)

    def validate_worker_name(self, worker_name, old_worker_name=None):
        if self.mode == 'add':
            return self.is_worker_name_valid(worker_name)
        elif self.mode == 'edit':
            if old_worker_name != worker_name:
                return self.is_worker_name_valid(worker_name)
            return True

    def validate_asset(self, asset):
        return self.is_asset_valid(asset)

    def validate_market(self, base_asset, quote_asset):
        return base_asset.lower() != quote_asset.lower()

    def validate_account_name(self, account):
        return self.account_exists(account)

    def validate_account(self, account, private_key):
        return self.is_account_valid(account, private_key)

    def validate_account_not_in_use(self, account):
        return not self.is_account_in_use(account)

    @gui_error
    def validate_form(self):
        error_texts = []
        base_asset = self.view.base_asset_input.currentText()
        quote_asset = self.view.quote_asset_input.text()
        worker_name = self.view.worker_name_input.text()

        if not self.validate_asset(base_asset):
            error_texts.append('Field "Base Asset" does not have a valid asset.')
        if not self.validate_asset(quote_asset):
            error_texts.append('Field "Quote Asset" does not have a valid asset.')
        if not self.validate_market(base_asset, quote_asset):
            error_texts.append("Market {}/{} doesn't exist.".format(base_asset, quote_asset))
        if self.mode == 'add':
            account = self.view.account_input.text()
            private_key = self.view.private_key_input.text()
            if not self.validate_worker_name(worker_name):
                error_texts.append('Worker name needs to be unique. "{}" is already in use.'.format(worker_name))
            if not self.validate_account_name(account):
                error_texts.append("Account doesn't exist.")
            if not self.validate_account(account, private_key):
                error_texts.append('Private key is invalid.')
            if not self.validate_account_not_in_use(account):
                error_texts.append('Use a different account. "{}" is already in use.'.format(account))
        elif self.mode == 'edit':
            if not self.validate_worker_name(worker_name, self.view.worker_name):
                error_texts.append('Worker name needs to be unique. "{}" is already in use.'.format(worker_name))

        error_texts.extend(self.view.strategy_widget.strategy_controller.validation_errors())
        error_text = '\n'.join(error_texts)

        if error_text:
            dialog = NoticeDialog(error_text)
            dialog.exec_()
            return False
        else:
            return True

    @gui_error
    def handle_save(self):
        if not self.validate_form():
            return

        if self.mode == 'add':
            # Add the private key to the database
            private_key = self.view.private_key_input.text()
            self.add_private_key(private_key)

            account = self.view.account_input.text()
        else:
            account = self.view.account_name.text()

        base_asset = self.view.base_asset_input.currentText()
        quote_asset = self.view.quote_asset_input.text()
        strategy_module = self.view.strategy_input.currentData()

        self.view.worker_data = {
            'account': account,
            'market': '{}/{}'.format(quote_asset, base_asset),
            'module': strategy_module,
            **self.view.strategy_widget.values
        }
        self.view.worker_name = self.view.worker_name_input.text()
        self.view.accept()


class UppercaseValidator(QtGui.QValidator):

    @staticmethod
    def validate(string, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos
