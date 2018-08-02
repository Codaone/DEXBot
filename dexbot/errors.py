import logging
log = logging.getLogger(__name__)


class DEXBotError(Exception):
    pass


class InsufficientFundsError(DEXBotError):
    pass


class NoWorkersAvailable(DEXBotError):
    pass


class EmptyMarket(DEXBotError):
    pass
