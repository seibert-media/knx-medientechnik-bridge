from dummy_input import dummy_input_handler
from power_state_handler import PowerStateHandler


class PowerStateHandlerDummy(PowerStateHandler):
    def __init__(self, system_key, conf):
        super().__init__(system_key, conf)
        self.power_state = False
        dummy_input_handler().register_dummy_power_callback(system_key, self.externally_set_power_state)

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

    def externally_set_power_state(self, new_state):
        self.log.info(f'Externally set to {new_state}')
        self.power_state = new_state
