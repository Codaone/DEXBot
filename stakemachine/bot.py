import traceback
import importlib
import time
import logging
import os.path
from bitshares.notify import Notify
from bitshares.instance import shared_bitshares_instance
log = logging.getLogger(__name__)


class BotInfrastructure():

    bots = dict()

    def __init__(
        self,
        config,
        bitshares_instance=None,
    ):
        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()

        self.config = config

        # Load all accounts and markets in use to subscribe to them
        accounts = set()
        markets = set()
        for botname, bot in config["bots"].items():
            if "account" not in bot:
                raise ValueError("Bot %s has no account" % botname)
            if "market" not in bot:
                raise ValueError("Bot %s has no market" % botname)

            accounts.add(bot["account"])
            markets.add(bot["market"])

        # Create notification instance
        # Technically, this will multiplex markets and accounts and
        # we need to demultiplex the events after we have received them
        self.notify = Notify(
            markets=list(markets),
            accounts=list(accounts),
            on_market=self.on_market,
            on_account=self.on_account,
            on_block=self.on_block,
            bitshares_instance=self.bitshares
        )

        # set the module search path
        userbotpath = os.path.expanduser("~/bots")
        if os.path.exists(userbotpath):
            sys.path.append(userbotpath)
        
        # Initialize bots:
        for botname, bot in config["bots"].items():
            klass = getattr(
                importlib.import_module(bot["module"]),
                bot["bot"]
            )
            self.bots[botname] = klass(
                config=config,
                name=botname,
                bitshares_instance=self.bitshares
            )

    # Events
    def on_block(self, data):
        for botname, bot in self.config["bots"].items():
            if self.bots[botname].disabled:
                continue
            try:
                self.bots[botname].ontick(data)
            except Exception as e:
                self.bots[botname].error_ontick(e)
                log.error(
                    "Error while processing {botname}.tick(): {exception}\n{stack}".format(
                        botname=botname,
                        exception=str(e),
                        stack=traceback.format_exc()
                    ))

    def on_market(self, data):
        if data.get("deleted", False):  # no info available on deleted orders
            return
        for botname, bot in self.config["bots"].items():
            if self.bots[botname].disabled:
                log.info("The bot %s has been disabled" % botname)
                continue
            if bot["market"] == data.market:
                try:
                    self.bots[botname].onMarketUpdate(data)
                except Exception as e:
                    self.bots[botname].error_onMarketUpdate(e)
                    log.error(
                        "Error while processing {botname}.onMarketUpdate(): {exception}\n{stack}".format(
                            botname=botname,
                            exception=str(e),
                            stack=traceback.format_exc()
                        ))

    def on_account(self, accountupdate):
        account = accountupdate.account
        for botname, bot in self.config["bots"].items():
            if self.bots[botname].disabled:
                log.info("The bot %s has been disabled" % botname)
                continue
            if bot["account"] == account["name"]:
                try:
                    self.bots[botname].onAccount(accountupdate)
                except Exception as e:
                    self.bots[botname].error_onAccount(e)
                    log.error(
                        "Error while processing {botname}.onAccount(): {exception}\n{stack}".format(
                            botname=botname,
                            exception=str(e),
                            stack=traceback.format_exc()
                        ))

    def run(self):
        self.notify.listen()
