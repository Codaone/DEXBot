#!/usr/bin/python3
import threading
import pytest
import logging
import time
import os
from pprint import pprint
from dexbot.worker import WorkerInfrastructure
from bitshares.bitshares import BitShares
from fixtures import fixture_data
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(funcName)s %(lineno)d  : %(message)s'
)
bot='worker 1'
class Test_Worker:
    def setup_class(self):
        self.TEST_CONFIG=fixture_data()
        # self.bitshares_instance = BitShares(node=TEST_CONFIG['node'], keys=KEYS)
        self.worker = WorkerInfrastructure(config=self.TEST_CONFIG)#,bitshares_instance=self.bitshares_instance)
    # def test_run(self):
    #     def wait_then_stop():
    #         time.sleep(20)
    #         self.worker.do_next_tick(self.worker.stop)
    #     stopper = threading.Thread(target=wait_then_stop)
    #     stopper.start()
    #     self.worker.run()
    #     stopper.join()
    def test_init_workers(self):
        self.worker.init_workers(self.TEST_CONFIG)
        account=self.TEST_CONFIG.get('workers').get(bot).get('account')
        logging.info(account)
        assert account in self.worker.accounts
    def test_update_notify(self):
        from dexbot.errors import NoWorkersAvailable
        # with pytest.raises(NoWorkersAvailable):
        #     self.worker.update_notify()
        self.worker.update_notify()
    def test_on_block(self):
        self.worker.on_block('022a4c4252aa7247e0d8978023c99b9d55af2136')
    def test_on_market(self):
        from bitshares.price import Order
        aorder=Order({'amount_to_sell': {'amount': 299999, 'asset_id': '1.3.1570'},
            'expiration': '2019-04-13T00:37:21',
            'extensions': [],
            'fee': {'amount': 2526, 'asset_id': '1.3.0'},
            'fill_or_kill': False,
            'min_to_receive': {'amount': '2444794742',
                                'asset_id': '1.3.5138'},
            'seller': '1.2.795945'})
        self.worker.on_market(aorder)
    def test_on_account(self):
        account=self.TEST_CONFIG.get('workers').get(bot).get('account')
        assert account in self.worker.accounts
    def test_add_worker(self):
        bot_name='worker 1'
        self.worker.add_worker(bot_name,self.TEST_CONFIG)
        logging.info(self.worker.workers)
        assert bot_name in self.worker.workers
    # def test_stop(self):
    #     time.sleep(2)
    #     self.worker.stop()
    def test_remove_worker(self):
        logging.info(self.worker.workers)
        assert bot  in self.worker.workers
    def test_remove_market(self):
        self.worker.remove_market(bot)
        logging.info(self.worker.markets)
        market=self.worker.markets
        assert market == self.worker.markets
    def test_remove_offline_worker(self):
        from fixtures import bitshares
        self.worker.remove_offline_worker(self.TEST_CONFIG,bot,bitshares)    
        # assert [] in self.worker.get_own_orders
    def test_remove_offline_worker_data(self):
        self.worker.remove_offline_worker_data(bot)
    def test_do_next_tick(self):
        pass
if __name__ == '__main__':
    cur_dir=os.path.dirname(__file__)
    # path='/Users/jacking/Documents/GitHub/env/DEXBot/tests/test_dexbot/'
    pytest.main(['--capture=no',cur_dir+'/test_worker.py'])