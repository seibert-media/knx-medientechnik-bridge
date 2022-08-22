import abc
import logging
from abc import ABC


class PowerHandler(ABC):
    @abc.abstractmethod
    def __init__(self, system_key, conf):
        self.system_key = system_key
        self.conf = conf

        self.log = logging.getLogger(f'bridge.system["{system_key}"].power')

    @abc.abstractmethod
    async def power_on(self):
        pass

    @abc.abstractmethod
    async def power_off(self):
        pass

    @abc.abstractmethod
    async def is_powered_on(self) -> bool:
        pass
