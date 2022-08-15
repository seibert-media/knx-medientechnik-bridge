import logging

from power_state_handler import PowerStateHandler


class PowerStateHandlerDummy(PowerStateHandler):
    def __init__(self, conf):
        super().__init__(conf)
        self.host = conf['host']
        self.log = logging.getLogger(f'bridge.power_state["{self.host}"]')
        self.power_state = False

    async def power_on(self) -> bool:
        self.log.info('Dummy: Turning on')
        self.power_state = True
        return True

    async def power_off(self) -> bool:
        self.log.info('Dummy: Turning off')
        self.power_state = False
        return True

    async def is_powered_on(self) -> bool:
        return self.power_state
