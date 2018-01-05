import logging
log = logging.getLogger(__name__)


def InsufficientFundsError(amount):
    log.error(
        "[InsufficientFunds] Need {}".format(str(amount))
    )
