from power_state_handler import PowerStateHandler


class PowerStateHandlerDummy(PowerStateHandler):
    def __init__(self, key, conf):
        super().__init__(key, conf)
        self.power_state = False

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        self.power_state = True
        return True

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        self.power_state = False
        return True

    async def is_powered_on(self) -> bool:
        self.log.debug(f'Query Result: {self.power_state}')
        return self.power_state
