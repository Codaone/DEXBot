"""
A module to provide an interactive text-based tool for dexbot configuration
The result is dexbot can be run without having to hand-edit config files.
If systemd is detected it will offer to install a user service unit (under ~/.local/share/systemd)
This requires a per-user systemd process to be running

Requires the 'whiptail' tool for text-based configuration (so UNIX only)
if not available, falls back to a line-based configurator ("NoWhiptail")

Note there is some common cross-UI configuration stuff: look in base.py
It's expected GUI/web interfaces will be re-implementing code in this file, but they should
understand the common code so worker strategy writers can define their configuration once
for each strategy class.
"""

import importlib
import pathlib
import os
import os.path
import sys
import re
import subprocess

from bitshares.account import Account

from dexbot.whiptail import get_whiptail
from dexbot.strategies.base import StrategyBase
from dexbot.config_validator import ConfigValidator

import dexbot.helper


STRATEGIES = [
    {'tag': 'relative',
     'class': 'dexbot.strategies.relative_orders',
     'name': 'Relative Orders'},
    {'tag': 'stagger',
     'class': 'dexbot.strategies.staggered_orders',
     'name': 'Staggered Orders'}]

tags_so_far = {'stagger', 'relative'}
for desc, module in dexbot.helper.find_external_strategies():
    tag = desc.split()[0].lower()
    # make sure tag is unique
    i = 1
    while tag in tags_so_far:
        tag = tag+str(i)
        i += 1
    tags_so_far.add(tag)
    STRATEGIES.append({'tag': tag, 'class': module, 'name': desc})

SYSTEMD_SERVICE_NAME = os.path.expanduser(
    "~/.local/share/systemd/user/dexbot.service")

SYSTEMD_SERVICE_FILE = """
[Unit]
Description=Dexbot

[Service]
Type=notify
WorkingDirectory={homedir}
ExecStart={exe} --systemd run
TimeoutSec=20m
Environment=PYTHONUNBUFFERED=true
Environment=UNLOCK={passwd}

[Install]
WantedBy=default.target
"""


def select_choice(current, choices):
    """ For the radiolist, get us a list with the current value selected
    """
    return [(tag, text, (current == tag and "ON") or "OFF")
            for tag, text in choices]


def process_config_element(element, whiptail, worker_config):
    """ Process an item of configuration metadata, display a widget as appropriate

        :param base_config.ConfigElement element: config element
        :param whiptail.Whiptail whiptail: instance of Whiptail or NoWhiptail
        :param collections.OrderedDict worker_config: the config dictionary for this worker
    """
    if element.description:
        title = '{} - {}'.format(element.title, element.description)
    else:
        title = element.title

    if element.type == "string":
        txt = whiptail.prompt(title, worker_config.get(element.key, element.default))
        if element.extra:
            while not re.match(element.extra, txt):
                whiptail.alert("The value is not valid")
                txt = whiptail.prompt(
                    title, worker_config.get(
                        element.key, element.default))
        worker_config[element.key] = txt

    if element.type == "bool":
        value = worker_config.get(element.key, element.default)
        value = 'yes' if value else 'no'
        worker_config[element.key] = whiptail.confirm(title, value)

    if element.type in ("float", "int"):
        while True:
            if element.type == 'int':
                template = '{}'
            else:
                template = '{:.8f}'
            txt = whiptail.prompt(title, template.format(worker_config.get(element.key, element.default)))
            try:
                if element.type == "int":
                    val = int(txt)
                else:
                    val = float(txt)
                if val < element.extra[0]:
                    whiptail.alert("The value is too low")
                elif element.extra[1] and val > element.extra[1]:
                    whiptail.alert("the value is too high")
                else:
                    break
            except ValueError:
                whiptail.alert("Not a valid value")
        worker_config[element.key] = val

    if element.type == "choice":
        worker_config[element.key] = whiptail.radiolist(title, select_choice(
            worker_config.get(element.key, element.default), element.extra))


def dexbot_service_running():
    """ Return True if dexbot service is running
    """
    cmd = 'systemctl --user status dexbot'
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in output.stdout.readlines():
        if b'Active:' in line and b'(running)' in line:
            return True
    return False


def setup_systemd(whiptail, config):
    """ Setup systemd unit to auto-start dexbot

        :param whiptail.Whiptail whiptail: instance of Whiptail or NoWhiptail
        :param dexbot.config.Config config: dexbot config
    """
    if not os.path.exists("/etc/systemd"):
        return  # No working systemd

    if not whiptail.confirm(
            "Do you want to run dexbot as a background (daemon) process?", default="no"):
        config['systemd_status'] = 'disabled'
        return

    redo_setup = False
    if os.path.exists(SYSTEMD_SERVICE_NAME):
        redo_setup = whiptail.confirm('Redo systemd setup?', 'no')

    if not os.path.exists(SYSTEMD_SERVICE_NAME) or redo_setup:
        path = '~/.local/share/systemd/user'
        path = os.path.expanduser(path)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        password = whiptail.prompt(
            "The uptick wallet password\n"
            "NOTE: this will be saved on disc so the worker can run unattended. "
            "This means anyone with access to this computer's files can spend all your money",
            password=True)

        # Because we hold password be restrictive
        fd = os.open(SYSTEMD_SERVICE_NAME, os.O_WRONLY | os.O_CREAT, 0o600)
        with open(fd, "w") as fp:
            fp.write(
                SYSTEMD_SERVICE_FILE.format(
                    exe=sys.argv[0],
                    passwd=password,
                    homedir=os.path.expanduser("~")))
        # The dexbot service file was edited, reload the daemon configs
        os.system('systemctl --user daemon-reload')

    # Signal cli.py to set the unit up after writing config file
    config['systemd_status'] = 'enabled'


def get_strategy_tag(strategy_class):
    """ Obtain tag for a strategy

        :param str strategy_class: strategy class name, example: dexbot.strategies.foo_bar

        It may seems that tags may be common across strategies, but it is not. Every strategy must use unique tag.
    """
    for strategy in STRATEGIES:
        if strategy_class == strategy['class']:
            return strategy['tag']
    return None


def configure_worker(whiptail, worker_config, bitshares_instance):
    """ Single worker configurator

        :param whiptail.Whiptail whiptail: instance of Whiptail or NoWhiptail
        :param collections.OrderedDict worker_config: the config dictionary for this worker
        :param bitshares.BitShares bitshares_instance: an instance of BitShares class
    """
    # By default always editing
    editing = True

    if not worker_config:
        editing = False

    default_strategy = worker_config.get('module', 'dexbot.strategies.relative_orders')
    strategy_list = []

    for strategy in STRATEGIES:
        if default_strategy == strategy['class']:
            default_strategy = strategy['tag']

        # Add strategy tag and name pairs to a list
        strategy_list.append([strategy['tag'], strategy['name']])

    # Strategy selection
    worker_config['module'] = whiptail.radiolist(
        "Choose a worker strategy",
        select_choice(default_strategy, strategy_list)
    )

    for strategy in STRATEGIES:
        if strategy['tag'] == worker_config['module']:
            worker_config['module'] = strategy['class']

    # Import the strategy class but we don't __init__ it here
    strategy_class = getattr(
        importlib.import_module(worker_config["module"]),
        'Strategy'
    )

    # Check if strategy has changed and editing existing worker
    if editing and default_strategy != get_strategy_tag(worker_config['module']):
        new_worker_config = {}
        # If strategy has changed, create new config where base elements stay the same
        for config_item in StrategyBase.configure():
            try:
                key = config_item[0]
                new_worker_config[key] = worker_config[key]
            except KeyError:
                # In case using old configuration file and there are new fields, this passes missing key
                pass

        # Add module separately to the config
        new_worker_config['module'] = worker_config['module']
        worker_config = new_worker_config

    # Use class metadata for per-worker configuration
    config_elems = strategy_class.configure()

    if config_elems:
        # Strategy options
        for elem in config_elems:
            if not editing and (elem.key == "account"):
                # only allow WIF addition for new workers
                account_name = None
                # Query user until correct account and key provided
                while not account_name:
                    account_name = add_account(whiptail, bitshares_instance)
                worker_config[elem.key] = account_name
            else:  # account name only for edit worker
                process_config_element(elem, whiptail, worker_config)
    else:
        whiptail.alert(
            "This worker type does not have configuration information. "
            "You will have to check the worker code and add configuration values to config.yml if required")

    return worker_config


def configure_dexbot(config, ctx):
    """ Main `cli configure` entrypoint

        :param dexbot.config.Config config: dexbot config
    """
    whiptail = get_whiptail('DEXBot configure')
    workers = config.get('workers', {})
    bitshares_instance = ctx.bitshares
    validator = ConfigValidator(bitshares_instance)

    if not workers:
        while True:
            txt = whiptail.prompt("Your name for the worker")
            if len(txt) == 0:
                whiptail.alert("Worker name cannot be blank. ")
            else:
                config['workers'] = {txt: configure_worker(whiptail, {}, bitshares_instance)}
                if not whiptail.confirm("Set up another worker?\n(DEXBot can run multiple workers in one instance)"):
                    break
        setup_systemd(whiptail, config)
    else:
        while True:
            action = whiptail.menu(
                "You have an existing configuration.\nSelect an action:",
                [('LIST', 'List your workers'),
                 ('NEW', 'Create a new worker'),
                 ('EDIT', 'Edit a worker'),
                 ('DEL_WORKER', 'Delete a worker'),
                 ('ADD', 'Add a bitshares account'),
                 ('DEL_ACCOUNT', 'Delete a bitshares account'),
                 ('SHOW', 'Show bitshares accounts'),
                 ('NODES', 'Edit Node Selection'),
                 ('ADD_NODE', 'Add Your Node'),
                 ('HELP', 'Where to get help'),
                 ('EXIT', 'Quit this application')])

            my_workers = [(index, index) for index in workers]

            if action == 'EXIT':
                # Cancel will also exit the application. but this is a clearer label
                # Todo: modify cancel to be "Quit" or "Exit" for the whiptail menu item.
                break
            elif action == 'LIST':
                if len(my_workers):
                    # List workers, then provide option to list config of workers
                    worker_name = whiptail.menu("List of Your Workers. Select to view Configuration.", my_workers)
                    content = config['workers'][worker_name]
                    text = '\n'
                    for key, value in content.items():
                        text += '{}: {}\n'.format(key, value)
                    whiptail.view_text(text, pager=False)
                else:
                    whiptail.alert('No workers to view.')
            elif action == 'EDIT':
                if len(my_workers):
                    worker_name = whiptail.menu("Select worker to edit", my_workers)
                    config['workers'][worker_name] = configure_worker(whiptail, config['workers'][worker_name],
                                                                      bitshares_instance)
                else:
                    whiptail.alert('No workers to edit.')
            elif action == 'DEL_WORKER':
                if len(my_workers):
                    worker_name = whiptail.menu("Select worker to delete", my_workers)
                    del config['workers'][worker_name]
                    # Pass ctx.config which is a loaded config (see ui.py configfile()), while `config` in a Config()
                    # instance, which is empty dict, but capable of returning keys via __getitem__(). We need to pass
                    # loaded config into StrategyBase to avoid loading a default config and preserve `--configfile`
                    # option
                    strategy = StrategyBase(worker_name, bitshares_instance=bitshares_instance, config=ctx.config)
                    strategy.clear_all_worker_data()
                else:
                    whiptail.alert('No workers to delete.')
            elif action == 'NEW':
                worker_name = whiptail.prompt("Your name for the new worker. ")
                if not worker_name:
                    whiptail.alert("Worker name cannot be blank. ")
                elif not validator.validate_worker_name(worker_name):
                    whiptail.alert('Worker name needs to be unique. "{}" is already in use.'.format(worker_name))
                else:
                    config['workers'][worker_name] = configure_worker(whiptail, {}, bitshares_instance)
            elif action == 'ADD':
                add_account(whiptail, bitshares_instance)
            elif action == 'DEL_ACCOUNT':
                del_account(whiptail, bitshares_instance)
            elif action == 'SHOW':
                account_list = list_accounts(bitshares_instance)
                if account_list:
                    action = whiptail.menu("Bitshares Account List (Name - Type)", account_list)
                else:
                    whiptail.alert('You do not have any bitshares accounts in the wallet')
            elif action == 'ADD_NODE':
                txt = whiptail.prompt("Your name for the new node: e.g. wss://dexnode.net/ws")
                # Insert new node on top of the list
                config['node'].insert(0, txt)
            elif action == 'NODES':
                choice = whiptail.node_radiolist(
                    msg="Choose your preferred node",
                    items=select_choice(config['node'][0],
                                        [(index, index) for index in config['node']]))
                # Move selected node as first item in the config file's node list
                config['node'].remove(choice)
                config['node'].insert(0, choice)
                setup_systemd(whiptail, config)
            elif action == 'HELP':
                whiptail.alert("Please see https://github.com/Codaone/DEXBot/wiki")

    whiptail.clear()
    return config


def add_account(whiptail, bitshares_instance):
    """ "Add account" dialog

        :param whiptail.Whiptail whiptail: instance of Whiptail or NoWhiptail
        :param bitshares.BitShares bitshares_instance: an instance of BitShares class
        :return str: user-supplied account name
    """
    validator = ConfigValidator(bitshares_instance)

    account = whiptail.prompt("Your Account Name")
    private_key = whiptail.prompt("Your Private Key", password=True)

    if not validator.validate_account_name(account):
        whiptail.alert("Account name does not exist.")
        return False
    if not validator.validate_private_key(account, private_key):
        whiptail.alert("Private key is invalid")
        return False
    if private_key and not validator.validate_private_key_type(account, private_key):
        whiptail.alert("Please use active private key.")
        return False

    # User can supply empty private key if it was added earlier
    if private_key:
        validator.add_private_key(private_key)
        whiptail.alert("Private Key added successfully.")

    return account


def del_account(whiptail, bitshares_instance):
    """ Delete account from the wallet

        :param whiptail.Whiptail whiptail: instance of Whiptail or NoWhiptail
        :param bitshares.BitShares bitshares_instance: an instance of BitShares class
    """
    account = whiptail.prompt("Account Name")
    wallet = bitshares_instance.wallet
    wallet.removeAccount(account)


def list_accounts(bitshares_instance):
    """ Get all accounts installed in local wallet in format suitable for Whiptail.menu()

        Returning format is compatible both with Whiptail and NoWhiptail.

        :return: list of tuples (int, 'account_name - key_type')
    """
    accounts = []
    pubkeys = bitshares_instance.wallet.getPublicKeys(current=True)

    for pubkey in pubkeys:
        account_ids = bitshares_instance.wallet.getAccountsFromPublicKey(pubkey)
        for account_id in account_ids:
            account = Account(account_id, bitshares_instance=bitshares_instance)
            key_type = bitshares_instance.wallet.getKeyType(account, pubkey)
            accounts.append({'name': account.name, 'type': key_type})

    account_list = [
        (str(num), '{} - {}'.format(account['name'], account['type'])) for num, account in enumerate(accounts)
    ]
    return account_list
