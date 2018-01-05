from dexbot.basestrategy import BaseStrategy
import logging
log = logging.getLogger(__name__)


class ManualOrders(BaseStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: do the strategy
