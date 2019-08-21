import pytest

from dexbot.controllers.main_controller import MainController
from grapheneapi.exceptions import NumRetriesReached


@pytest.fixture
def failing_nodes(unused_port):
    nodes = ['wss://localhost:{}'.format(unused_port()) for _ in range(3)]
    return nodes


@pytest.fixture
def many_failing_one_working(unused_port, bitshares_testnet):
    nodes = ['wss://localhost:{}'.format(unused_port()) for _ in range(3)]
    nodes.append('ws://127.0.0.1:{}'.format(bitshares_testnet.service_port))
    return nodes


@pytest.mark.mandatory
def test_measure_latency_all_failing(failing_nodes):
    """ Expect an error if no nodes could be reached
    """
    with pytest.raises(NumRetriesReached):
        MainController.measure_latency(failing_nodes)


@pytest.mark.mandatory
def test_measure_latency_one_working(many_failing_one_working):
    """ Test connection to 3 nodes where only 3rd is working
    """
    MainController.measure_latency(many_failing_one_working)
