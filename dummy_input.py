import asyncio
import logging
import sys
import threading

inst = None


def dummy_input_handler():
    global inst
    if inst is None:
        inst = DummyInputHandler()

    return inst


# https://stackoverflow.com/a/58493716/1659732
async def ainput():
    loop = asyncio.get_event_loop()
    fut = loop.create_future()

    def _run():
        line = sys.stdin.readline()
        loop.call_soon_threadsafe(fut.set_result, line)

    threading.Thread(target=_run, daemon=True).start()
    return await fut


class DummyInputHandler:
    def __init__(self):
        self.callbacks = dict()
        self.log = logging.getLogger(f'bridge.dummy_input')
        self.log.debug('starting read_stdin task')
        self.task = asyncio.create_task(self.read_stdin())

    def register_dummy_power_callback(self, system_key, cb):
        self.log.info(f'Write "{system_key}:on" or "{system_key}:off" to toggle Power for {system_key}')
        self.callbacks[f'{system_key}:on'] = lambda: cb(True)
        self.callbacks[f'{system_key}:off'] = lambda: cb(False)

    def register_dummy_mux_callback(self, system_key, input_key, cb):
        self.log.info(f'Write "{system_key}:{input_key}" to toggle Mux for {system_key}')
        self.callbacks[f'{system_key}:{input_key}'] = lambda: cb(input_key)

    def stop(self):
        self.log.debug('stopping read_stdin task')
        self.task.cancel()

    async def read_stdin(self):
        while True:
            line = await ainput()
            line = line.rstrip()
            if line in self.callbacks:
                await self.callbacks[line]()
