import abc
import logging
from abc import ABC


class PowerHandler(ABC):
    @abc.abstractmethod
    def __init__(self, system_key, conf, on_device_power_changed):
        self.system_key = system_key
        self.conf = conf
        self.on_device_power_changed_cb = on_device_power_changed

        self.log = logging.getLogger(f'bridge.system["{system_key}"].power')

    async def set_power(self, new_state):
        if new_state:
            await self.power_on()
        else:
            await self.power_off()

    @abc.abstractmethod
    async def power_on(self):
        pass

    @abc.abstractmethod
    async def power_off(self):
        pass

    @abc.abstractmethod
    async def is_powered_on(self) -> bool:
        pass

    async def stop(self):
        pass

    async def on_device_power_changed(self, new_state):
        if self.on_device_power_changed_cb:
            await self.on_device_power_changed_cb(new_state)
