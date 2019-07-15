import asyncio
import threading
import importlib
import logging

import dexbot.plugins
from dexbot.helper import iter_namespace

from bitshares import BitShares

log = logging.getLogger(__name__)

class PluginInfrastructure(threading.Thread):
    """ Run plugins as asyncio tasks

        :param dict config: dexbot config

        PluginInfrastructure class is needed to be able to run asyncio plugins while having synchronous core. After
        switching to asyncio-aware main thread we may continue to use all plugins without refactoring them.
    """

    def __init__(self, config):
        super().__init__()

        self.bitshares = BitShares(node=config['node'], num_retries=-1)
        self.config = config
        self.loop = None
        self.need_stop = False
        self.plugins = []

    def run(self):
        log.debug('Starting PluginInfrastructure thread')
        self.init_plugins()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.run_plugins())
        self.loop.create_task(self.stop_handler())
        self.loop.run_forever()

    def init_plugins(self):
        """ Initialize plugin instances
        """
        plugins = {name: importlib.import_module(name) for finder, name, ispkg in iter_namespace(dexbot.plugins)}

        for name, plugin in plugins.items():
            self.plugins.append(plugin.Plugin(config=self.config, bitshares_instance=self.bitshares))

    async def run_plugins(self):
        """ Run each discovered plugin by calling Plugin.main()
        """
        # Schedule every plugin as asyncio Task; use ensure_future() for python3.6 compatibility
        tasks = [asyncio.ensure_future(plugin.main()) for plugin in self.plugins]
        try:
            # Wait until all plugins are finished, but catch exceptions immediately as they occure
            await asyncio.gather(*tasks, return_exceptions=False)
        except asyncio.CancelledError:
            # Note: task.cancel() will not propagate this exception here, so it will appear only on current task cancel
            log.debug('Stopping run_plugins()')
        except Exception:
            log.exception('Task finished with exception:')

    async def stop_handler(self):
        """ Watch for self.need_stop flag to cancel tasks and stop the thread

            With this solution it's easier to achieve correct tasks stopping. self.loop.call_soon_threadsafe() requires
            additional wrapping to stop tasks or catch exceptions.
        """
        while True:
            if self.need_stop:
                log.debug('Stopping event loop')
                tasks = [task for task in asyncio.Task.all_tasks() if task is not asyncio.tasks.Task.current_task()]
                # Cancel all tasks
                list(map(lambda task: task.cancel(), tasks))
                # Wait for tasks finish
                results = await asyncio.gather(*tasks, return_exceptions=True)
                log.debug('Finished awaiting cancelled tasks, results: {0}'.format(results))
                # Stop the event loop
                self.loop.stop()
                return
            else:
                await asyncio.sleep(1)
