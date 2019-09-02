import os
import os.path
import sys
import logging
import logging.config
from functools import update_wrapper

import click
from ruamel import yaml
from appdirs import user_data_dir

from bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance
from bitshares.exceptions import WrongMasterPasswordException

from dexbot import VERSION, APP_NAME, AUTHOR
from dexbot.config import Config

log = logging.getLogger(__name__)


def verbose(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        verbosity = [
            "critical", "error", "warn", "info", "debug"
        ][int(min(ctx.obj.get("verbose", 0), 4))]
        if ctx.obj.get("systemd", False):
            # Don't print the timestamps: systemd will log it for us
            formatter1 = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            formatter2 = logging.Formatter(
                '%(worker_name)s using account %(account)s on %(market)s - %(levelname)s - %(message)s')
        elif verbosity == "debug":
            # When debugging: log where the log call came from
            formatter1 = logging.Formatter('%(asctime)s (%(module)s:%(lineno)d) - %(levelname)s - %(message)s')
            formatter2 = logging.Formatter(
                '%(asctime)s (%(module)s:%(lineno)d) - %(worker_name)s - %(levelname)s - %(message)s')
        else:
            formatter1 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            formatter2 = logging.Formatter(
                '%(asctime)s - %(worker_name)s using account %(account)s on %(market)s - %(levelname)s - %(message)s')

        # Use special format for special workers logger
        logger = logging.getLogger("dexbot.per_worker")
        logger.setLevel(getattr(logging, verbosity.upper()))
        ch = logging.StreamHandler()
        ch.setFormatter(formatter2)
        logger.addHandler(ch)

        # Logging to a file
        filename = ctx.obj.get('logfile')
        if not filename:
            # By default, log to a user data dir
            data_dir = user_data_dir(APP_NAME, AUTHOR)
            filename = os.path.join(data_dir, 'dexbot.log')
        # Print logfile using main logger
        logging.getLogger("dexbot").info('Dexbot version {}, logfile: {}'.format(VERSION, filename))

        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter2)
        logger.addHandler(fh)

        logger.propagate = False  # Don't double up with root logger
        # Set the root logger with basic format
        ch = logging.StreamHandler()
        ch.setFormatter(formatter1)
        logging.getLogger("dexbot").addHandler(ch)
        logging.getLogger("").handlers = []

        # GrapheneAPI logging
        if ctx.obj["verbose"] > 4:
            verbosity = [
                "critical", "error", "warn", "info", "debug"
            ][int(min(ctx.obj.get("verbose", 4) - 4, 4))]
            logger = logging.getLogger("grapheneapi")
            logger.setLevel(getattr(logging, verbosity.upper()))
            logger.addHandler(ch)

        if ctx.obj["verbose"] > 8:
            verbosity = [
                "critical", "error", "warn", "info", "debug"
            ][int(min(ctx.obj.get("verbose", 8) - 8, 4))]
            logger = logging.getLogger("graphenebase")
            logger.setLevel(getattr(logging, verbosity.upper()))
            logger.addHandler(ch)

        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def chain(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        ctx.bitshares = BitShares(
            ctx.config["node"],
            num_retries=-1,
            expiration=60,
            **ctx.obj
        )
        set_shared_bitshares_instance(ctx.bitshares)
        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def unlock(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if not ctx.obj.get("unsigned", False):
            systemd = ctx.obj.get('systemd', False)
            if ctx.bitshares.wallet.created():
                if "UNLOCK" in os.environ:
                    pwd = os.environ["UNLOCK"]
                    if pwd[:12] == "/run/secrets":
                        pwd = open(pwd).read()
                else:
                    if systemd:
                        # No user available to interact with
                        log.critical("Uptick Passphrase not available, exiting")
                        sys.exit(78)  # 'configuration error' in sysexits.h
                    pwd = click.prompt(
                        "Current Uptick Wallet Passphrase", hide_input=True)
                try:
                    ctx.bitshares.wallet.unlock(pwd)
                except WrongMasterPasswordException:
                    log.critical("Password error, exiting")
                    sys.exit(78)
            else:
                if systemd:
                    # No user available to interact with
                    log.critical("Uptick Wallet not installed, cannot run")
                    sys.exit(78)
                click.echo("No Uptick wallet installed yet. \n" +
                           "This is a password for encrypting " +
                           "the file that contains your private keys.  Creating ...")
                pwd = click.prompt(
                    "Uptick Wallet Encryption Passphrase",
                    hide_input=True,
                    confirmation_prompt=True)
                ctx.bitshares.wallet.create(pwd)
        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def configfile(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if not os.path.isfile(ctx.obj["configfile"]):
            Config(path=ctx.obj['configfile'])
        ctx.config = yaml.safe_load(open(ctx.obj["configfile"]))
        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def priceChange(new, old):
    if float(old) == 0.0:
        return -1
    else:
        percent = ((float(new) - float(old))) / float(old) * 100
        if percent >= 0:
            return click.style("%.2f" % percent, fg="green")
        else:
            return click.style("%.2f" % percent, fg="red")


def formatPrice(f):
    return click.style("%.10f" % f, fg="yellow")


def formatStd(f):
    return click.style("%.2f" % f, bold=True)


def warning(msg):
    click.echo(
        "[" +
        click.style("Warning", fg="yellow") +
        "] " + msg
    )


def confirmwarning(msg):
    return click.confirm(
        "[" +
        click.style("Warning", fg="yellow") +
        "] " + msg
    )


def alert(msg):
    click.echo(
        "[" +
        click.style("Alert", fg="red") +
        "] " + msg
    )


def confirmalert(msg):
    return click.confirm(
        "[" +
        click.style("Alert", fg="red") +
        "] " + msg
    )

# error message "translation"
# here we convert some of the cryptic Graphene API error messages into a longer sentence
# particularly whe the problem is something the user themselves can fix (such as not enough
# money in account)
# it's here because both GUI and CLI might use it


TRANSLATIONS = {'amount_to_sell.amount > 0': "You need to have sufficient buy and sell amounts in your account",
                'now <= trx.expiration': "Your node has difficulty syncing to the blockchain, consider changing nodes"}


def translate_error(err):
    for k, v in TRANSLATIONS.items():
        if k in err:
            return v
    return None
