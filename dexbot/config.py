import os
import pathlib

from dexbot import APP_NAME, AUTHOR

import appdirs
from ruamel import yaml
from collections import OrderedDict


DEFAULT_CONFIG_DIR = appdirs.user_config_dir(APP_NAME, appauthor=AUTHOR)
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, 'config.yml')


class Config(dict):

    def __init__(self, config=None, path=None):
        """ Creates or loads the config file based on if it exists.
            :param dict config: data used to create the config file
            :param str path: path to the config file
        """
        super().__init__()
        if path:
            self.config_dir = os.path.dirname(path)
            self.config_file = path
        else:
            self.config_dir = DEFAULT_CONFIG_DIR
            self.config_file = DEFAULT_CONFIG_FILE

        if config:
            self.create_config(config, self.config_file)
            self._config = self.load_config(self.config_file)
        else:
            if not os.path.isfile(self.config_file):
                self.create_config(self.default_data, self.config_file)
            self._config = self.load_config(self.config_file)

        # In case there is not a list of nodes in the config file,
        # the node will be replaced by a list of pre-defined nodes.
        if isinstance(self._config['node'], str):
            self._config['node'] = self.node_list
            self.save_config()

    def __setitem__(self, key, value):
        self._config[key] = value

    def __getitem__(self, key):
        return self._config[key]

    def __delitem__(self, key):
        del self._config[key]

    def __contains__(self, key):
        return key in self._config

    def get(self, key, default=None):
        return self._config.get(key, default)

    @property
    def default_data(self):
        return {'node': self.node_list, 'workers': {}}

    @property
    def workers_data(self):
        """ Returns dict of all the workers data
        """
        return self._config['workers']

    def dict(self):
        """ Returns a dict instance of the stored data
        """
        return self._config

    @staticmethod
    def create_config(config, path=None):
        if not path:
            config_dir = DEFAULT_CONFIG_DIR
            config_file = DEFAULT_CONFIG_FILE
        else:
            config_dir = os.path.dirname(path)
            config_file = path

        if not os.path.exists(config_dir):
            pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    @staticmethod
    def load_config(path=None):
        if not path:
            path = DEFAULT_CONFIG_FILE

        with open(path, 'r') as f:
            return Config.ordered_load(f, loader=yaml.SafeLoader)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def refresh_config(self):
        self._config = self.load_config(self.config_file)

    @staticmethod
    def get_worker_config_file(worker_name, path=None):
        """ Returns config file data with only the data from a specific worker.
            Config loaded from a file
        """
        if not path:
            path = DEFAULT_CONFIG_FILE

        with open(path, 'r') as f:
            config = Config.ordered_load(f, loader=yaml.SafeLoader)

        config['workers'] = OrderedDict({worker_name: config['workers'][worker_name]})
        return config

    def get_worker_config(self, worker_name):
        """ Returns config file data with only the data from a specific worker.
            Config loaded from memory
        """
        config = self._config.copy()
        config['workers'] = OrderedDict({worker_name: config['workers'][worker_name]})
        return config

    def remove_worker_config(self, worker_name):
        self._config['workers'].pop(worker_name, None)

        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def add_worker_config(self, worker_name, worker_data):
        self._config['workers'][worker_name] = worker_data

        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def replace_worker_config(self, worker_name, new_worker_name, worker_data):
        workers = self._config['workers']
        # Rotate the dict keys to keep order
        for _ in range(len(workers)):
            key, value = workers.popitem(False)
            if worker_name == key:
                workers[new_worker_name] = worker_data
            else:
                workers[key] = value

        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    @staticmethod
    def ordered_load(stream, loader=None, object_pairs_hook=OrderedDict):
        if loader is None:
            loader = yaml.UnsafeLoader

        class OrderedLoader(loader):
            pass

        def construct_mapping(mapping_loader, node):
            mapping_loader.flatten_mapping(node)
            return object_pairs_hook(mapping_loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return yaml.load(stream, OrderedLoader)

    @property
    def node_list(self):
        """ A pre-defined list of Bitshares nodes. """
        return [
            "wss://status200.bitshares.apasia.tech/ws",
            "wss://eu.openledger.info/ws",
            "wss://bitshares.openledger.info/ws",
            "wss://dexnode.net/ws",
            "wss://japan.bitshares.apasia.tech/ws",
            "wss://bitshares-api.wancloud.io/ws",
            "wss://openledger.hk/ws",
            "wss://bitshares.apasia.tech/ws",
            "wss://bitshares.crypto.fans/ws",
            "wss://kc-us-dex.xeldal.com/ws",
            "wss://api.bts.blckchnd.com",
            "wss://btsza.co.za:8091/ws",
            "wss://bitshares.dacplay.org/ws",
            "wss://bit.btsabc.org/ws",
            "wss://bts.ai.la/ws",
            "wss://ws.gdex.top"
        ]
