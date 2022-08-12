import abc
from abc import ABC


class PowerStateHandler(ABC):
    def __init__(self, conf):
        self.host = conf
        self._temp_internal_state = False

    @abc.abstractmethod
    async def power_on(self):
        self._temp_internal_state = True

    @abc.abstractmethod
    async def power_off(self):
        self._temp_internal_state = False

    @abc.abstractmethod
    async def is_powered_on(self) -> bool:
        return self._temp_internal_state
