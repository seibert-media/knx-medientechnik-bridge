import abc
import logging
from abc import ABC


class MuxHandler(ABC):
    def __init__(self, system_key, conf):
        self.system_key = system_key
        self.conf = conf
        self.inputs = conf['input']

        self.log = logging.getLogger(f'bridge.system["{system_key}"].mux')

    @abc.abstractmethod
    async def select_input(self, input_key: str) -> bool:
        pass

    @abc.abstractmethod
    async def get_current_input(self) -> str:
        pass
