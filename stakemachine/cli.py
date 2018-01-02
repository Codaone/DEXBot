#!/usr/bin/env python3
import yaml
import logging
import click
import os.path

from .ui import (
    verbose,
    chain,
    unlock,
    configfile,
    confirmwarning,
    confirmalert,
    warning,
    alert,
)
from stakemachine.bot import BotInfrastructure
from stakemachine.configure import configure_stakemachine, QuitException

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


@click.group()
@click.option(
    "--configfile",
    default="config.yml",
)
@click.option(
    '--verbose',
    '-v',
    type=int,
    default=3,
    help='Verbosity (0-15)')
@click.pass_context
def main(ctx, **kwargs):
    ctx.obj = {}
    for k, v in kwargs.items():
        ctx.obj[k] = v


@main.command()
@click.pass_context
@configfile
@chain
@unlock
@verbose
def run(ctx):
    """ Continuously run the bot
    """
    bot = BotInfrastructure(ctx.config)
    bot.run()

@main.command()
@click.pass_context
@verbose
def configure(ctx):
    """ Interactively configure stakemachine
    """
    if os.path.exists(ctx.obj['configfile']):
        with open(ctx.obj["configfile"]) as fd:
            config = yaml.load(fd)
    else:
        config = {}
    try:
        configure_stakemachine(config)
        with open(ctx.obj["configfile"],"w") as fd:
            yaml.dump(config,fd,default_flow_style=False)
        print("new configuration saved")
    except QuitException:
        print("configuration exited: nothing changed")
if __name__ == '__main__':
    main()
