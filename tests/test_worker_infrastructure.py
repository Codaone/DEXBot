import threading
import logging
import time
import pytest

from dexbot.worker import WorkerInfrastructure

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


@pytest.fixture(scope='module')
def account(prepare_account):
    account = prepare_account({'MYBASE': 10000, 'MYQUOTE': 2000})
    return account


@pytest.fixture(scope='module')
def config(bitshares, account):
    config = {
        'node': '{}'.format(bitshares.rpc.url),
        'workers': {
            'echo': {'account': '{}'.format(account), 'market': 'MYQUOTE/MYBASE', 'module': 'dexbot.strategies.echo'}
        },
    }
    return config


@pytest.mark.mandatory
def test_worker_infrastructure(bitshares, config):
    """ Test whether dexbot core is able to work
    """
    worker_infrastructure = WorkerInfrastructure(config=config, bitshares_instance=bitshares)

    def wait_then_stop():
        time.sleep(1)
        worker_infrastructure.do_next_tick(worker_infrastructure.stop(pause=True))

    stopper = threading.Thread(target=wait_then_stop)
    stopper.start()
    worker_infrastructure.run()
    stopper.join()
