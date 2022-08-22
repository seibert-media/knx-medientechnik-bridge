from dummy_input import dummy_input_handler
from power_handler import PowerHandler


class PowerHandlerDummy(PowerHandler):
    def __init__(self, output_key, conf, on_device_power_changed):
        super().__init__(output_key, conf, on_device_power_changed)
        self.power_state = False
        dummy_input_handler().register_dummy_power_callback(output_key, self.externally_set_power)

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        self.power_state = True
        return True

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        self.power_state = False
        return True

    async def is_powered_on(self) -> bool:
        return self.power_state

    async def externally_set_power(self, new_state):
        self.log.info(f'Externally set to {new_state}')
        self.power_state = new_state
        await self.on_device_power_changed(new_state)
