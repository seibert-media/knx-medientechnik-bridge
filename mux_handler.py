import abc
import logging
from abc import ABC


class MuxHandler(ABC):
    def __init__(self, system_key, conf, on_mux_input_changed):
        self.system_key = system_key
        self.conf = conf
        self.inputs = conf['input']
        self.on_mux_input_changed_cb = on_mux_input_changed

        self.log = logging.getLogger(f'bridge.system["{system_key}"].mux')

    @abc.abstractmethod
    async def select_input(self, input_key: str) -> bool:
        pass

    @abc.abstractmethod
    async def get_current_input(self) -> str:
        pass

    async def stop(self):
        pass

    async def on_mux_input_changed(self, new_input_key):
        if self.on_mux_input_changed_cb:
            await self.on_mux_input_changed_cb(new_input_key)
