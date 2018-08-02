import os
import logging
import sys

from dexbot import VERSION, APP_NAME, AUTHOR
from dexbot.helper import initialize_orders_log
from dexbot.worker import WorkerInfrastructure
from dexbot.views.errors import PyQtHandler

from appdirs import user_data_dir
from bitshares.instance import set_shared_bitshares_instance


class MainController:

    def __init__(self, bitshares_instance, config):
        self.bitshares_instance = bitshares_instance
        set_shared_bitshares_instance(bitshares_instance)
        self.config = config
        self.worker_manager = None

        # Configure logging
        data_dir = user_data_dir(APP_NAME, AUTHOR)
        filename = os.path.join(data_dir, 'dexbot.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(worker_name)s using account %(account)s on %(market)s - %(levelname)s - %(message)s')
        logger = logging.getLogger("dexbot.per_worker")
        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
        self.pyqt_handler = PyQtHandler()
        self.pyqt_handler.setLevel(logging.INFO)
        logger.addHandler(self.pyqt_handler)
        logger.info("DEXBot {} on python {} {}".format(VERSION, sys.version[:6], sys.platform), extra={
                    'worker_name': 'NONE', 'account': 'NONE', 'market': 'NONE'})

        # Configure orders logging
        initialize_orders_log()

    def set_info_handler(self, handler):
        self.pyqt_handler.set_info_handler(handler)

    def start_worker(self, worker_name, config, view):
        # Todo: Add some threading here so that the GUI doesn't freeze
        if self.worker_manager and self.worker_manager.is_alive():
            self.worker_manager.add_worker(worker_name, config)
        else:
            self.worker_manager = WorkerInfrastructure(config, self.bitshares_instance, view)
            self.worker_manager.daemon = True
            self.worker_manager.start()

    def pause_worker(self, worker_name):
        self.worker_manager.stop(worker_name, pause=True)

    def remove_worker(self, worker_name):
        # Todo: Add some threading here so that the GUI doesn't freeze
        if self.worker_manager and self.worker_manager.is_alive():
            # Worker manager currently running
            if worker_name in self.worker_manager.workers:
                self.worker_manager.remove_worker(worker_name)
                self.worker_manager.stop(worker_name)
            else:
                # Worker not running
                config = self.config.get_worker_config(worker_name)
                WorkerInfrastructure.remove_offline_worker(config, worker_name, self.bitshares_instance)
        else:
            # Worker manager not running
            config = self.config.get_worker_config(worker_name)
            WorkerInfrastructure.remove_offline_worker(config, worker_name, self.bitshares_instance)

    @staticmethod
    def create_worker(worker_name):
        # Deletes old worker's data
        WorkerInfrastructure.remove_offline_worker_data(worker_name)
