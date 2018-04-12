#!/usr/bin/env python3
import logging
import os
import signal
import sys

from dexbot import config_file
from dexbot.ui import (
    verbose,
    chain,
    unlock,
    configfile
)
from dexbot.worker import WorkerInfrastructure
import dexbot.errors as errors

import click

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


@click.group()
@click.option(
    "--configfile",
    default=config_file,
)
@click.option(
    '--verbose',
    '-v',
    type=int,
    default=3,
    help='Verbosity (0-15)')
@click.option(
    '--pidfile',
    '-p',
    type=str,
    default='',
    help='File to write PID')
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
    """ Continuously run the worker
    """
    if ctx.obj['pidfile']:
        with open(ctx.obj['pidfile'], 'w') as fd:
            fd.write(str(os.getpid()))
    try:
        try:
            worker = WorkerInfrastructure(ctx.config)
            # Set up signalling. do it here as of no relevance to GUI
            kill_workers = worker_job(worker, worker.stop)
            # These first two UNIX & Windows
            signal.signal(signal.SIGTERM, kill_workers)
            signal.signal(signal.SIGINT, kill_workers)
            try:
                # These signals are UNIX-only territory, will ValueError here on Windows
                signal.signal(signal.SIGHUP, kill_workers)
                # TODO: reload config on SIGUSR1
                # signal.signal(signal.SIGUSR1, lambda x, y: worker.do_next_tick(worker.reread_config))
            except ValueError:
                log.debug("Cannot set all signals -- not available on this platform")
            worker.run()
        finally:
            if ctx.obj['pidfile']:
                os.unlink(ctx.obj['pidfile'])
    except errors.NoWorkersAvailable:
        sys.exit(70)  # 70= "Software error" in /usr/include/sysexts.h


def worker_job(worker, job):
    return lambda x, y: worker.do_next_tick(job)


if __name__ == '__main__':
    main()
