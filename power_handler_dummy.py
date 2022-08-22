from dummy_input import dummy_input_handler
from power_handler import PowerHandler


class PowerHandlerDummy(PowerHandler):
    def __init__(self, system_key, conf):
        super().__init__(system_key, conf)
        self.power = False
        dummy_input_handler().register_dummy_power_callback(system_key, self.externally_set_power)

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        self.power = True
        return True

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        self.power = False
        return True

    async def is_powered_on(self) -> bool:
        return self.power

    def externally_set_power(self, new_state):
        self.log.info(f'Externally set to {new_state}')
        self.power = new_state
