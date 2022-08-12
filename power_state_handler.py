import abc
from abc import ABC


class PowerStateHandler(ABC):
    def __init__(self, conf):
        self.host = conf

    @abc.abstractmethod
    async def power_on(self) -> bool:
        pass

    @abc.abstractmethod
    async def power_off(self) -> bool:
        pass

    @abc.abstractmethod
    async def is_powered_on(self) -> bool:
        pass
