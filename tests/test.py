#!/usr/bin/python3
import threading
import unittest
import logging
import time
import os

from dexbot.worker import WorkerInfrastructure

from bitshares.bitshares import BitShares

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


TEST_CONFIG = {
    'node': 'wss://node.testnet.bitshares.eu',
    'bots': {
        'echo':
        {
            'account': 'aud.bot.test4',
            'market': 'TESTUSD:TEST',
            'module': 'dexbot.strategies.echo'
        }
    }
}

# User needs to put a key in
KEYS = [os.environ['DEXBOT_TEST_WIF']]


class TestDexbot(unittest.TestCase):

    def test_dexbot(self):
        bitshares_instance = BitShares(node=TEST_CONFIG['node'], keys=KEYS)
        worker_infrastructure = WorkerInfrastructure(config=TEST_CONFIG,
                                                     bitshares_instance=bitshares_instance)

        import pdb
        pdb.set_trace()

        def wait_then_stop():
            time.sleep(20)
            worker_infrastructure.do_next_tick(worker_infrastructure.stop)

        stopper = threading.Thread(target=wait_then_stop)
        stopper.start()
        worker_infrastructure.run()
        stopper.join()


if __name__ == '__main__':
    unittest.main()
