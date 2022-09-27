from power_handler import PowerHandler


class PowerHandlerDummy(PowerHandler):
    def __init__(self, output_key, conf, on_device_power_changed):
        super().__init__(output_key, conf, on_device_power_changed)
        self.power_state = False

    async def power_on(self) -> bool:
        self.log.info('Would be Turning on')
        self.power_state = True
        return True

    async def power_off(self) -> bool:
        self.log.info('Would be Turning off')
        self.power_state = False
        return True

    async def is_powered_on(self) -> bool:
        return self.power_state
