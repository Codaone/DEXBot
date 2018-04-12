import logging

from dexbot import config_file
from dexbot.worker import WorkerInfrastructure

from ruamel.yaml import YAML
from bitshares.instance import set_shared_bitshares_instance


class MainController:

    def __init__(self, bitshares_instance):
        self.bitshares_instance = bitshares_instance
        set_shared_bitshares_instance(bitshares_instance)
        self.worker_manager = None

        # Configure logging
        formatter = logging.Formatter(
            '%(asctime)s - %(worker_name)s using account %(account)s on %(market)s - %(levelname)s - %(message)s')
        logger = logging.getLogger("dexbot.per_worker")
        fh = logging.FileHandler('dexbot.log')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)

    def create_worker(self, worker_name, config, view):
        # Todo: Add some threading here so that the GUI doesn't freeze
        if self.worker_manager and self.worker_manager.is_alive():
            self.worker_manager.add_worker(worker_name, config)
        else:
            self.worker_manager = WorkerInfrastructure(config, self.bitshares_instance, view)
            self.worker_manager.daemon = True
            self.worker_manager.start()

    def stop_worker(self, worker_name):
        self.worker_manager.stop(worker_name)

    def remove_worker(self, worker_name):
        # Todo: Add some threading here so that the GUI doesn't freeze
        if self.worker_manager and self.worker_manager.is_alive():
            # Worker manager currently running
            if worker_name in self.worker_manager.workers:
                self.worker_manager.remove_worker(worker_name)
                self.worker_manager.stop(worker_name)
            else:
                # Worker not running
                config = self.get_worker_config(worker_name)
                WorkerInfrastructure.remove_offline_worker(config, worker_name)
        else:
            # Worker manager not running
            config = self.get_worker_config(worker_name)
            WorkerInfrastructure.remove_offline_worker(config, worker_name)

    @staticmethod
    def load_config():
        yaml = YAML()
        with open(config_file, 'r') as f:
            return yaml.load(f)

    @staticmethod
    def get_workers_data():
        """
        Returns dict of all the workers data
        """
        with open(config_file, 'r') as f:
            yaml = YAML()
            return yaml.load(f)['workers']

    @staticmethod
    def get_worker_config(worker_name):
        """
        Returns config file data with only the data from a specific worker
        """
        with open(config_file, 'r') as f:
            yaml = YAML()
            config = yaml.load(f)
            config['workers'] = {worker_name: config['workers'][worker_name]}
            return config

    @staticmethod
    def remove_worker_config(worker_name):
        yaml = YAML()
        with open(config_file, 'r') as f:
            config = yaml.load(f)

        config['workers'].pop(worker_name, None)

        with open(config_file, "w") as f:
            yaml.dump(config, f)

    @staticmethod
    def add_worker_config(worker_name, worker_data):
        yaml = YAML()
        with open(config_file, 'r') as f:
            config = yaml.load(f)

        config['workers'][worker_name] = worker_data

        with open(config_file, "w") as f:
            yaml.dump(config, f)

    @staticmethod
    def replace_worker_config(worker_name, new_worker_name, worker_data):
        yaml = YAML()
        with open(config_file, 'r') as f:
            config = yaml.load(f)

        workers = config['workers']
        # Rotate the dict keys to keep order
        for _ in range(len(workers)):
            key, value = workers.popitem(False)
            if worker_name == key:
                workers[new_worker_name] = worker_data
            else:
                workers[key] = value

        with open(config_file, "w") as f:
            yaml.dump(config, f)
