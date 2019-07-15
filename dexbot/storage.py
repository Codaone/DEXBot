import os
import json
import threading
import queue
import uuid
from appdirs import user_data_dir

from . import helper
from dexbot import APP_NAME, AUTHOR

from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# For dexbot.sqlite file
storageDatabase = "dexbot.sqlite"


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    category = Column(String)
    key = Column(String)
    value = Column(String)

    def __init__(self, c, k, v):
        self.category = c
        self.key = k
        self.value = v


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    worker = Column(String)
    order_id = Column(String)
    order = Column(String)

    def __init__(self, worker, order_id, order):
        self.worker = worker
        self.order_id = order_id
        self.order = order


class Balances(Base):
    __tablename__ = 'balances'

    id = Column(Integer, primary_key=True)
    account = Column(String)
    worker = Column(String)
    base_total = Column(Float)
    base_symbol = Column(String)
    quote_total = Column(Float)
    quote_symbol = Column(String)
    center_price = Column(Float)
    timestamp = Column(Integer)

    def __init__(self, account, worker, base_total, base_symbol, quote_total, quote_symbol, center_price, timestamp):
        self.account = account
        self.worker = worker
        self.base_total = base_total
        self.base_symbol = base_symbol
        self.quote_total = quote_total
        self.quote_symbol = quote_symbol
        self.center_price = center_price
        self.timestamp = timestamp


class Storage(dict):
    """ Storage class

        :param string category: The category to distinguish
                                different storage namespaces
    """

    def __init__(self, category):
        self.category = category

    def __setitem__(self, key, value):
        db_worker.set_item(self.category, key, value)

    def __getitem__(self, key):
        return db_worker.get_item(self.category, key)

    def __delitem__(self, key):
        db_worker.del_item(self.category, key)

    def __contains__(self, key):
        return db_worker.contains(self.category, key)

    def items(self):
        return db_worker.get_items(self.category)

    def clear(self):
        db_worker.clear(self.category)

    def save_order(self, order):
        """ Save the order to the database
        """
        order_id = order['id']
        db_worker.save_order(self.category, order_id, order)

    def remove_order(self, order):
        """ Removes an order from the database
        """
        order_id = order['id']
        db_worker.remove_order(self.category, order_id)

    def clear_orders(self):
        """ Removes all worker's orders from the database
        """
        db_worker.clear_orders(self.category)

    def fetch_orders(self, worker=None):
        """ Get all the orders (or just specific worker's orders) from the database
        """
        if not worker:
            worker = self.category
        return db_worker.fetch_orders(worker)

    @staticmethod
    def clear_worker_data(worker):
        db_worker.clear_orders(worker)
        db_worker.clear(worker)

    @staticmethod
    def store_balance_entry(account, worker, base_total, base_symbol, quote_total, quote_symbol,
                            center_price, timestamp):
        balance = Balances(account, worker, base_total, base_symbol,
                           quote_total, quote_symbol, center_price, timestamp)
        # Save balance to db
        db_worker.save_balance(balance)

    @staticmethod
    def get_balance_history(account, worker, timestamp, base_asset, quote_asset):
        return db_worker.get_balance(account, worker, timestamp, base_asset, quote_asset)

    @staticmethod
    def get_recent_balance_entry(account, worker, base_asset, quote_asset):
        return db_worker.get_recent_balance_entry(account, worker, base_asset, quote_asset)


class DatabaseWorker(threading.Thread):
    """ Thread safe database worker
    """

    def __init__(self):
        super().__init__()

        # Obtain engine and session
        engine = create_engine('sqlite:///%s' % sqlDataBaseFile, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        Base.metadata.create_all(engine)
        self.session.commit()

        self.task_queue = queue.Queue()
        self.results = {}

        self.lock = threading.Lock()
        self.event = threading.Event()
        # Daemon thread means it will be abruptly killed on parent thread shutdown
        self.daemon = True
        self.start()

    def run(self):
        # Continuously iterate over task queue and execute tasks
        for func, args, token in iter(self.task_queue.get, None):
            if token is not None:
                args = args+(token,)
            func(*args)

    def _get_result(self, token):
        """ Get task result from all results by token

            This function is invoked from self.execute() when caller thread executes a method which needs to return some
            result back to caller. On each loop iteration results are being examined for specified task token. If it is
            not yet available, the loop execution suspended until DatabaseWorker thread will set self.event flag
            indicating some task processing is completed. _get_result() is called from another thread while queue
            processing is performed inside the current thread.
        """
        while True:
            with self.lock:
                if token in self.results:
                    # Find and return task results by token
                    return_value = self.results[token]
                    del self.results[token]
                    return return_value
                else:
                    # Suspend loop execution and wait for flag
                    self.event.clear()
            # Block loop execution waiting Event flag set() from DatabaseWorker thread
            self.event.wait()

    def _set_result(self, token, result):
        """ Associate query results with task token
        """
        with self.lock:
            self.results[token] = result
            self.event.set()

    def execute(self, func, *args):
        """ Create queue task and return task result
        """
        # Token is an unique task identifier
        token = str(uuid.uuid4)
        # Schedule query execution into DatabaseWorker thread queue
        self.task_queue.put((func, args, token))
        # Return results when they will be available
        return self._get_result(token)

    def execute_noreturn(self, func, *args):
        """ Create queue task without returning a result
        """
        self.task_queue.put((func, args, None))

    def set_item(self, category, key, value):
        self.execute_noreturn(self._set_item, category, key, value)

    def _set_item(self, category, key, value):
        value = json.dumps(value)
        e = self.session.query(Config).filter_by(
            category=category,
            key=key
        ).first()
        if e:
            e.value = value
        else:
            e = Config(category, key, value)
            self.session.add(e)
        self.session.commit()

    def get_item(self, category, key):
        return self.execute(self._get_item, category, key)

    def _get_item(self, category, key, token):
        e = self.session.query(Config).filter_by(
            category=category,
            key=key
        ).first()
        if not e:
            result = None
        else:
            result = json.loads(e.value)
        self._set_result(token, result)

    def del_item(self, category, key):
        self.execute_noreturn(self._del_item, category, key)

    def _del_item(self, category, key):
        e = self.session.query(Config).filter_by(
            category=category,
            key=key
        ).first()
        self.session.delete(e)
        self.session.commit()

    def contains(self, category, key):
        return self.execute(self._contains, category, key)

    def _contains(self, category, key, token):
        e = self.session.query(Config).filter_by(
            category=category,
            key=key
        ).first()
        self._set_result(token, bool(e))

    def get_items(self, category):
        return self.execute(self._get_items, category)

    def _get_items(self, category, token):
        es = self.session.query(Config).filter_by(
            category=category
        ).all()
        result = [(e.key, e.value) for e in es]
        self._set_result(token, result)

    def clear(self, category):
        self.execute_noreturn(self._clear, category)

    def _clear(self, category):
        rows = self.session.query(Config).filter_by(
            category=category
        )
        for row in rows:
            self.session.delete(row)
            self.session.commit()

    def save_order(self, worker, order_id, order):
        self.execute_noreturn(self._save_order, worker, order_id, order)

    def _save_order(self, worker, order_id, order):
        value = json.dumps(order)
        e = self.session.query(Orders).filter_by(
            order_id=order_id
        ).first()
        if e:
            e.value = value
        else:
            e = Orders(worker, order_id, value)
            self.session.add(e)
        self.session.commit()

    def remove_order(self, worker, order_id):
        self.execute_noreturn(self._remove_order, worker, order_id)

    def _remove_order(self, worker, order_id):
        e = self.session.query(Orders).filter_by(
            worker=worker,
            order_id=order_id
        ).first()
        self.session.delete(e)
        self.session.commit()

    def clear_orders(self, worker):
        self.execute_noreturn(self._clear_orders, worker)

    def _clear_orders(self, worker):
        rows = self.session.query(Orders).filter_by(
            worker=worker
        )
        for row in rows:
            self.session.delete(row)
            self.session.commit()

    def fetch_orders(self, category):
        return self.execute(self._fetch_orders, category)

    def _fetch_orders(self, worker, token):
        results = self.session.query(Orders).filter_by(
            worker=worker,
        ).all()
        if not results:
            result = None
        else:
            result = {}
            for row in results:
                result[row.order_id] = json.loads(row.order)
        self._set_result(token, result)

    def save_balance(self, balance):
        self.execute_noreturn(self._save_balance, balance)

    def _save_balance(self, balance):
        self.session.add(balance)
        self.session.commit()

    def get_balance(self, account, worker, timestamp, base_asset, quote_asset):
        return self.execute(self._get_balance, account, worker, timestamp, base_asset, quote_asset)

    def _get_balance(self, account, worker, timestamp, base_asset, quote_asset, token):
        """ Get first item that has bigger time as given timestamp and matches account and worker name
        """
        result = self.session.query(Balances).filter(
            Balances.account == account,
            Balances.worker == worker,
            Balances.base_symbol == base_asset,
            Balances.quote_symbol == quote_asset,
            Balances.timestamp > timestamp
        ).first()

        self._set_result(token, result)

    def get_recent_balance_entry(self, account, worker, base_asset, quote_asset):
        return self.execute(self._get_recent_balance_entry, account, worker, base_asset, quote_asset)

    def _get_recent_balance_entry(self, account, worker, base_asset, quote_asset, token):
        """ Get most recent balance history item that matches account and worker name
        """
        result = self.session.query(Balances).filter(
            Balances.account == account,
            Balances.worker == worker,
            Balances.base_symbol == base_asset,
            Balances.quote_symbol == quote_asset,
        ).order_by(Balances.id.desc()).first()

        self._set_result(token, result)


# Derive sqlite file directory
data_dir = user_data_dir(APP_NAME, AUTHOR)
sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

# Create directory for sqlite file
helper.mkdir(data_dir)

db_worker = DatabaseWorker()
