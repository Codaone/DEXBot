import os
import json
import threading
import queue
import uuid
import time
import datetime
import re
import logging
from appdirs import user_data_dir

from . import helper
from dexbot import APP_NAME, AUTHOR

import sqlalchemy
from sqlalchemy import create_engine, Table, Column, String, Integer, MetaData, DateTime, Float
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


class Journal(Base):
    __tablename__ = 'journal'
    id = Column(Integer, primary_key=True)
    category = Column(String)
    key = Column(String)
    amount = Column(Float)
    stamp = Column(DateTime, default=datetime.datetime.now)


class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    category = Column(String)
    severity = Column(Integer)
    message = Column(String)
    stamp = Column(DateTime, default=datetime. datetime.now)


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

    def save_journal(self, amounts):
        db_worker.execute_noreturn(db_worker.save_journal, self.category, amounts)

    def query_journal(self, start, end_=None):
        return db_worker.execute(db_worker.query_journal, self.category, start, end_)

    def query_log(self, start, end_=None):
        return db_worker.execute(db_worker.query_log, self.category, start, end_)

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
        self.daemon = True
        self.start()

    def run(self):
        for func, args, token in iter(self.task_queue.get, None):
            if token is not None:
                args = args + (token,)
            func(*args)

    def _get_result(self, token):
        while True:
            with self.lock:
                if token in self.results:
                    return_value = self.results[token]
                    del self.results[token]
                    return return_value
                else:
                    self.event.clear()
            self.event.wait()

    def _set_result(self, token, result):
        with self.lock:
            self.results[token] = result
            self.event.set()

    def execute(self, func, *args):
        token = str(uuid.uuid4)
        self.task_queue.put((func, args, token))
        return self._get_result(token)

    def execute_noreturn(self, func, *args):
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

    def save_journal(self, category, amounts, token=None):
        now_t = datetime.datetime.now()
        for key, amount in amounts:
            e = Journal(key=key, category=category, amount=amount, stamp=now_t)
            self.session.add(e)
        self.session.commit()

    def query_journal(self, category, start, end_, token):
        """Query this bots journal
        start: datetime of start time
        end_: datetime of end (None means up to now)
        """
        r = self.session.query(Journal).filter(Journal.category == category)
        if isinstance(start, str):
            m = re.match("(\\d+)([dw])", start)
            if m:
                n = int(m.group(1))
                start = datetime.datetime.now()
                if m.group(2) == 'w':
                    n *= 7
                start -= datetime.timedelta(days=n)
        if end_:
            r = r.filter(Journal.stamp > start, Journal.stamp < end_)
        else:
            r = r.filter(Journal.stamp > start)
        self.set_result(token, r.all())

    def save_log(self, category, severity, message, created, token=None):
        e = Log(
            category=category,
            severity=severity,
            message=message,
            stamp=created)
        self.session.add(e)
        self.session.commit()

    def query_log(self, category, start, end_, token):
        """Query this bots log
        start: datetime of start time
        end_: datetime of end (None means up to now)
        """
        r = self.session.query(Log).filter(Log.category == category)
        if isinstance(start, str):
            m = re.match("(\\d+)([dw])", start)
            if m:
                n = int(m.group(1))
                start = datetime.datetime.now()
                if m.group(2) == 'w':
                    n *= 7
                start -= datetime.timedelta(days=n)
        if end_:
            r = r.filter(Log.stamp > start, Log.stamp < end_)
        else:
            r = r.filter(Log.stamp > start)
        r = r.order_by(Log.stamp)
        self.set_result(token, r.all())

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


MAP_LEVELS = {
    logging.DEBUG: 0,
    logging.INFO: 1,
    logging.ERROR: 2,
    logging.WARN: 2,
    logging.CRITICAL: 3,
    logging.FATAL: 3}


class SQLiteHandler(logging.Handler):
    """
    Logging handler for SQLite.
    Based on Vinay Sajip's DBHandler class (http://www.red-dove.com/python_logging.html)
    """
    # used by email Reporter (but has to be here so it can access db_worker)

    def emit(self, record):
        # Use default formatting:
        self.format(record)
        level = MAP_LEVELS.get(record.levelno, 0)
        notes = record.msg
        if record.exc_info:
            notes += " " + \
                logging._defaultFormatter.formatException(record.exc_info)
        # Insert log record:
        db_worker.execute_noreturn(
            db_worker.save_log,
            record.botname,
            level,
            notes,
            datetime.datetime.fromtimestamp(
                record.created))


# Derive sqlite file directory
data_dir = user_data_dir(APP_NAME, AUTHOR)
sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

# Create directory for sqlite file
helper.mkdir(data_dir)

db_worker = DatabaseWorker()
