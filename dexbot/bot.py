import traceback
import importlib
import time
import logging
import os.path
from bitshares.notify import Notify
from bitshares.instance import shared_bitshares_instance

log = logging.getLogger(__name__)

log_bots = logging.getLogger('dexbot.per_bot')
# NOTE this is the  special logger for per-bot events
# it  returns LogRecords with extra fields: botname, account, market and is_disabled
# is_disabled is a callable returning True if the bot is currently disabled.
# GUIs can add a handler to this logger to get a stream of events re the running bots.


# FIXME: currently static list of bot strategies: ? how to enumerate bots available and deploy new bot strategies.
STRATEGIES={'Echo':('dexbot.strategies.echo','Echo'),
            'Liquidity Walls':('dexbot.strategies.walls','Walls')}


class BotInfrastructure():

    bots = dict()

    def __init__(
        self,
        config,
        bitshares_instance=None
    ):
        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()

        self.config = config

        # Load all accounts and markets in use to subscribe to them
        accounts = set()
        markets = set()

        
        # set the module search path
        userbotpath = os.path.expanduser("~/bots")
        if os.path.exists(userbotpath):
            sys.path.append(userbotpath)

        
        # Initialize bots:
        for botname, bot in config["bots"].items():
            if "account" not in bot:
                log_bots.critical("Bot has no account",extra={'botname':botname,'account':'unknown','market':'unknown','is_dsabled':(lambda: True)})
                continue
            if "market" not in bot:
                log_bots.critical("Bot has no market",extra={'botname':botname,'account':bot['account'],'market':'unknown','is_disabled':(lambda: True)})
                continue
            try:
                klass = getattr(
                    importlib.import_module(bot["module"]),
                    bot["bot"]
                )
                self.bots[botname] = klass(
                    config=config,
                    name=botname,
                    bitshares_instance=self.bitshares
                )
                markets |= set(self.bots[botname].all_markets())
                accounts.add(bot['account'])
            except:
                log_bots.exception("Bot initialisation",extra={'botname':botname,'account':bot['account'],'market':'unknown','is_disabled':(lambda: True)})

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


    # Events
    def on_block(self, data):
        for botname, bot in self.config["bots"].items():
            if self.bots[botname].disabled:
                continue
            try:
                self.bots[botname].ontick(data)
            except Exception as e:
                self.bots[botname].error_ontick(e)
                self.bots[botname].log.exception("in .tick()")
                self.bots[botname].disabled = True

    def on_market(self, data):
        if data.get("deleted", False):  # no info available on deleted orders
            return
        for botname, bot in self.config["bots"].items():
            if self.bots[botname].disabled:
                continue
            if data.market in self.bots[botname].all_markets():
                try:
                    self.bots[botname].onMarketUpdate(data)
                except Exception as e:
                    self.bots[botname].error_onMarketUpdate(e)
                    self.bots[botname].log.exception(".onMarketUpdate()")

    def on_account(self, accountupdate):
        account = accountupdate.account
        for botname, bot in self.config["bots"].items():
            if self.bots[botname].disabled:
                self.bot[botname].log.info("The bot %s has been disabled" % botname)
                continue
            if bot["account"] == account["name"]:
                try:
                    self.bots[botname].onAccount(accountupdate)
                except Exception as e:
                    self.bots[botname].error_onAccount(e)
                    self.bots[botname].log.exception(".onAccountUpdate()")

    def run(self):
        self.notify.listen()

