import os
import logging
import sys
import time

from dexbot import VERSION, APP_NAME, AUTHOR
from dexbot.helper import initialize_orders_log, initialize_data_folders
from dexbot.worker import WorkerInfrastructure
from dexbot.views.errors import PyQtHandler

from appdirs import user_data_dir
from bitshares.bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance
from bitsharesapi.bitsharesnoderpc import BitSharesNodeRPC
from grapheneapi.exceptions import NumRetriesReached


class MainController:

    def __init__(self, config):
        self.bitshares_instance = None
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

        # Initialize folders
        initialize_data_folders()

    def set_bitshares_instance(self, bitshares_instance):
        """ Set bitshares instance

            :param bitshares_instance: A bitshares instance
        """
        self.bitshares_instance = bitshares_instance
        set_shared_bitshares_instance(bitshares_instance)

    def new_bitshares_instance(self, node, retries=-1, expiration=60):
        """ Create bitshares instance

            :param retries: Number of retries to connect, -1 default to infinity
            :param expiration: Delay in seconds until transactions are supposed to expire
            :param list node: Node or a list of nodes
        """
        self.bitshares_instance = BitShares(node, num_retries=retries, expiration=expiration)
        set_shared_bitshares_instance(self.bitshares_instance)

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

    def pause_worker(self, worker_name, config=None):
        if self.worker_manager and self.worker_manager.is_alive():
            self.worker_manager.stop(worker_name, pause=True)
        else:
            self.worker_manager = WorkerInfrastructure(config, self.bitshares_instance)

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
    def measure_latency(nodes):
        """ Measures latency of first alive node from given nodes in milliseconds

            :param str,list nodes: Bitshares node address(-es)
            :return: int: latency in milliseconds
            :raises grapheneapi.exceptions.NumRetriesReached: if failed to find a working node
        """
        if isinstance(nodes, str):
            nodes = [nodes]

        # Check nodes one-by-one until first working found
        for node in nodes:
            try:
                start = time.time()
                BitSharesNodeRPC(node, num_retries=1)
                latency = (time.time() - start) * 1000
                return latency
            except (NumRetriesReached, OSError):
                # [Errno 111] Connection refused -> OSError
                continue

        raise NumRetriesReached

    @staticmethod
    def create_worker(worker_name):
        # Deletes old worker's data
        WorkerInfrastructure.remove_offline_worker_data(worker_name)
