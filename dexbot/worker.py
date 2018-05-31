import importlib
import sys
import logging
import os.path
import threading
import copy

import dexbot.errors as errors
from dexbot.basestrategy import BaseStrategy

from bitshares.notify import Notify
from bitshares.instance import shared_bitshares_instance

log = logging.getLogger(__name__)
log_workers = logging.getLogger('dexbot.per_worker')
# NOTE this is the  special logger for per-worker events
# it returns LogRecords with extra fields: worker_name, account, market and is_disabled
# is_disabled is a callable returning True if the worker is currently disabled.
# GUIs can add a handler to this logger to get a stream of events of the running workers.


class WorkerInfrastructure(threading.Thread):

    def __init__(
        self,
        config,
        bitshares_instance=None,
        view=None
    ):
        super().__init__()

        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()
        self.config = copy.deepcopy(config)
        self.view = view
        self.jobs = set()
        self.notify = None
        self.config_lock = threading.RLock()
        self.workers = {}

        self.accounts = set()
        self.markets = set()

        # Set the module search path
        user_worker_path = os.path.expanduser("~/bots")
        if os.path.exists(user_worker_path):
            sys.path.append(user_worker_path)

    def init_workers(self, config):
        """ Initialize the workers
        """
        self.config_lock.acquire()
        for worker_name, worker in config["workers"].items():
            if "account" not in worker:
                log_workers.critical("Worker has no account", extra={
                    'worker_name': worker_name, 'account': 'unknown',
                    'market': 'unknown', 'is_disabled': (lambda: True)
                })
                continue
            if "market" not in worker:
                log_workers.critical("Worker has no market", extra={
                    'worker_name': worker_name, 'account': worker['account'],
                    'market': 'unknown', 'is_disabled': (lambda: True)
                })
                continue
            try:
                strategy_class = getattr(
                    importlib.import_module(worker["module"]),
                    'Strategy'
                )
                self.workers[worker_name] = strategy_class(
                    config=config,
                    name=worker_name,
                    bitshares_instance=self.bitshares,
                    view=self.view
                )
                self.markets.add(worker['market'])
                self.accounts.add(worker['account'])
            except BaseException:
                log_workers.exception("Worker initialisation", extra={
                    'worker_name': worker_name, 'account': worker['account'],
                    'market': 'unknown', 'is_disabled': (lambda: True)
                })
        self.config_lock.release()

    def update_notify(self):
        if not self.config['workers']:
            log.critical("No workers to launch, exiting")
            raise errors.NoWorkersAvailable()

        if self.notify:
            # Update the notification instance
            self.notify.reset_subscriptions(list(self.accounts), list(self.markets))
        else:
            # Initialize the notification instance
            self.notify = Notify(
                markets=list(self.markets),
                accounts=list(self.accounts),
                on_market=self.on_market,
                on_account=self.on_account,
                on_block=self.on_block,
                bitshares_instance=self.bitshares
            )

    # Events
    def on_block(self, data):
        if self.jobs:
            try:
                for job in self.jobs:
                    job()
            finally:
                self.jobs = set()

        self.config_lock.acquire()
        for worker_name, worker in self.config["workers"].items():
            if worker_name not in self.workers or self.workers[worker_name].disabled:
                continue
            try:
                self.workers[worker_name].ontick(data)
            except Exception as e:
                self.workers[worker_name].log.exception("in ontick()")
                try:
                    self.workers[worker_name].error_ontick(e)
                except Exception:
                    self.workers[worker_name].log.exception("in error_ontick()")
        self.config_lock.release()

    def on_market(self, data):
        if data.get("deleted", False):  # No info available on deleted orders
            return

        self.config_lock.acquire()
        for worker_name, worker in self.config["workers"].items():
            if self.workers[worker_name].disabled:
                self.workers[worker_name].log.debug('Worker "{}" is disabled'.format(worker_name))
                continue
            if worker["market"] == data.market:
                try:
                    self.workers[worker_name].onMarketUpdate(data)
                except Exception as e:
                    self.workers[worker_name].log.exception("in onMarketUpdate()")
                    try:
                        self.workers[worker_name].error_onMarketUpdate(e)
                    except Exception:
                        self.workers[worker_name].log.exception("in error_onMarketUpdate()")
        self.config_lock.release()

    def on_account(self, account_update):
        self.config_lock.acquire()
        account = account_update.account
        for worker_name, worker in self.config["workers"].items():
            if self.workers[worker_name].disabled:
                self.workers[worker_name].log.info('Worker "{}" is disabled'.format(worker_name))
                continue
            if worker["account"] == account["name"]:
                try:
                    self.workers[worker_name].onAccount(account_update)
                except Exception as e:
                    self.workers[worker_name].log.exception("in onAccountUpdate()")
                    try:
                        self.workers[worker_name].error_onAccount(e)
                    except Exception:
                        self.workers[worker_name].log.exception("in error_onAccountUpdate()")
        self.config_lock.release()

    def add_worker(self, worker_name, config):
        with self.config_lock:
            self.config['workers'][worker_name] = config['workers'][worker_name]
            self.init_workers(config)
        self.update_notify()

    def run(self):
        self.init_workers(self.config)
        self.update_notify()
        self.notify.listen()

    def stop(self, worker_name=None, clean_exit=None):
        """ Used to stop the worker(s)
            :param str worker_name: name of the worker to stop
            :param clean_exit: specify this whether you want to cleanly stop workers,
                for example workers are supposed to react on SIGINT / SIGTERM
        """
        if worker_name and len(self.workers) > 1:
            # Kill only the specified worker
            self.remove_market(worker_name)
            with self.config_lock:
                account = self.config['workers'][worker_name]['account']
                self.config['workers'].pop(worker_name)

            self.accounts.remove(account)
            if clean_exit:
                self.workers[worker_name].clean_exit()
            else:
                self.workers[worker_name].cancel_all()
            self.workers.pop(worker_name, None)
            self.update_notify()
        else:
            # Kill all of the workers
            for worker in self.workers:
                if clean_exit:
                    self.workers[worker].clean_exit()
                else:
                    self.workers[worker].cancel_all()
            if self.notify:
                self.notify.websocket.close()

    def clean_exit(self, *args, **kwargs):
        """ Call this method when you need to cleanly shutdown worker by SIGINT / SIGTERM
        """
        self.stop(clean_exit=True, *args, **kwargs)

    def remove_worker(self, worker_name=None):
        if worker_name:
            self.workers[worker_name].purge()
        else:
            for worker in self.workers:
                self.workers[worker].purge()

    def remove_market(self, worker_name):
        """ Remove the market only if the worker is the only one using it
        """
        with self.config_lock:
            market = self.config['workers'][worker_name]['market']
            for name, worker in self.config['workers'].items():
                if market == worker['market']:
                    break  # Found the same market, do nothing
            else:
                # No markets found, safe to remove
                self.markets.remove(market)

    @staticmethod
    def remove_offline_worker(config, worker_name):
        # Initialize the base strategy to get control over the data
        strategy = BaseStrategy(config, worker_name)
        strategy.purge()

    def do_next_tick(self, job):
        """ Add a callable to be executed on the next tick """
        self.jobs.add(job)
