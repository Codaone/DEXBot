import pytest


def test_configure(base, config):
    c = base.config
    assert config == c

    base.configure()


def test_configure_details(base):
    config_details = base.configure_details()
    assert config_details == []


def test_pause(base):
    base.pause()


def test_clear_all_worker_data(base):
    base.clear_all_worker_data()


def test_store_profit_estimation_data(base, account_name):
    # todo:'worker_name' is not declared.
    # todo: no136:self.worker_name = name  # add by bitProfessor
    base.store_profit_estimation_data()


@pytest.mark.xfail(reason='bug')
def test_get_profit_estimation_data(base):
    base.get_profit_estimation_data(seconds=60)


def test_calc_profit(base):
    base.calc_profit()


def test_account(base, account_name):
    assert account_name == base.account.name


def test_balances(base):
    balances = base.balances
    assert float(balances[0]) == 10000
    assert float(balances[1]) == 10000
    assert float(balances[2]) == 2000


def test_base_asset(base):
    assert 'MYBASE' == base.base_asset


def test_quote_asset(base):
    assert 'MYQUOTE' == base.quote_asset


def test_market(base):
    assert 'MYBASE' == base.market['base']['symbol']
    assert 'MYQUOTE' == base.market['quote']['symbol']



# @pytest.mark.xfail(reason='sqlalchemy.exc.InterfaceError')
@pytest.mark.skip('Exception in thread Thread-1')
def test_purge_all_local_worker_data(base):
    base.purge_all_local_worker_data(base.worker)


def test_update_gui_slider(base):
    base.update_gui_slider()


@pytest.mark.xfail(reason='view is not declared')
def test_update_gui_profit(base):
    base.update_gui_profit()
