#!/usr/bin/env python3
import logging
import os
import os.path
import signal
import sys

from dexbot.config import Config, DEFAULT_CONFIG_FILE
from dexbot.helper import initialize_orders_log
from dexbot.ui import (
    verbose,
    chain,
    unlock,
    configfile
)
from .worker import WorkerInfrastructure
from .cli_conf import configure_dexbot, dexbot_service_running
from . import errors
from . import helper

# We need to do this before importing click
if "LANG" not in os.environ:
    os.environ['LANG'] = 'C.UTF-8'
import click


log = logging.getLogger(__name__)

# Initial logging before proper setup.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Configure orders logging
initialize_orders_log()


@click.group()
@click.option(
    "--configfile",
    default=DEFAULT_CONFIG_FILE,
)
@click.option(
    '--verbose',
    '-v',
    type=int,
    default=3,
    help='Verbosity (0-15)')
@click.option(
    '--systemd/--no-systemd',
    '-d',
    default=False,
    help='Run as a daemon from systemd')
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
        worker = WorkerInfrastructure(ctx.config)
        # Set up signalling. do it here as of no relevance to GUI
        kill_workers = worker_job(worker, lambda: worker.stop(pause=True))
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
        if ctx.obj['systemd']:
            try:
                import sdnotify  # A soft dependency on sdnotify -- don't crash on non-systemd systems
                n = sdnotify.SystemdNotifier()
                n.notify("READY=1")
            except BaseException:
                log.debug("sdnotify not available")
        worker.run()
    except errors.NoWorkersAvailable:
        worker.shutdown()
        sys.exit(70)  # 70= "Software error" in /usr/include/sysexts.h
    finally:
        if ctx.obj['pidfile']:
            helper.remove(ctx.obj['pidfile'])


@main.command()
@click.pass_context
@configfile
@chain
@unlock
def configure(ctx):
    """ Interactively configure dexbot
    """
    # Make sure the dexbot service isn't running while we do the config edits
    if dexbot_service_running():
        click.echo("Stopping dexbot daemon")
        os.system('systemctl --user stop dexbot')

    config = Config(path=ctx.obj['configfile'])
    configure_dexbot(config, ctx)
    config.save_config()

    click.echo("New configuration saved")
    if config.get('systemd_status', 'disabled') == 'enabled':
        click.echo("Starting dexbot daemon")
        os.system("systemctl --user start dexbot")


def shell():
    """ Run dexbot as a shell
    """
    if len(sys.argv) > 2 and sys.argv[1] == '-c':
        # let users who Know What They Are Doing get to the shell of their choice
        os.execl(sys.argv[2], sys.argv[2])
    cfg_file = config_file
    assert os.path.exists(cfg_file), "no config file"
    with open(cfg_file) as fd:
        config = yaml.safe_load(fd)
    while True:
        configure_dexbot(config, True)
        with open(cfg_file, "w") as fd:
            yaml.dump(config, fd, default_flow_style=False)
        if config['systemd_status'] == 'installed':
            # we are already installed
            os.system("systemctl --user restart dexbot")
        if config['systemd_status'] == 'install':
            os.system("systemctl --user enable dexbot")
            os.system("systemctl --user start dexbot")
            config['systemd_status'] = 'installed'


def worker_job(worker, job):
    return lambda x, y: worker.do_next_tick(job)


if __name__ == '__main__':
    main()
