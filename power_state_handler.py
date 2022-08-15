import abc
from abc import ABC


class PowerStateHandler(ABC):
    @abc.abstractmethod
    def __init__(self, conf):
        self.conf = conf

    @abc.abstractmethod
    async def power_on(self):
        pass

    @abc.abstractmethod
    async def power_off(self):
        pass

    @abc.abstractmethod
    async def is_powered_on(self) -> bool:
        pass
