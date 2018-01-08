import logging
log = logging.getLogger(__name__)


class InsufficientFundsError(Exception):
    pass
