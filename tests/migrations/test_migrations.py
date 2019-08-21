import pytest

from dexbot.storage import DatabaseWorker


@pytest.mark.mandatory
def test_apply_migrations_fresh(fresh_db):
    """ Test fresh installation
    """
    DatabaseWorker.run_migrations('dexbot/migrations', 'sqlite:///{}'.format(fresh_db))


@pytest.mark.mandatory
def test_apply_migrations_historic(historic_db):
    """ Test transition of old installation before alembic
    """
    DatabaseWorker.run_migrations('dexbot/migrations', 'sqlite:///{}'.format(historic_db))
