import asyncio
import logging

import xknx.devices

from power_state_handler import PowerStateHandler
from power_state_handlers import POWER_STATE_HANDLERS
from zeevee_mux import ZeeVeeMux


def create_knx_binding(xknx_binding, group_address, binding_name, updated_cb):
    return xknx.devices.Switch(
        xknx_binding,
        name=binding_name,
        group_address=group_address,
        # we *are* the switch, so we behave like a true knx device and respond to reads
        # while not trying to read the state from another device on the bus
        respond_to_read=True, sync_state=False,
        device_updated_cb=updated_cb
    )


class Room(object):
    def __init__(self, xknx_binding, room_name, room_conf):
        self.log = logging.getLogger(f'bridge.room["{room_name}"]')
        self.log.info('setup')

        self.log.debug('setup power_state_handler')
        power_state_handler_class = POWER_STATE_HANDLERS[room_conf['power_state']['protocol']]
        self.power_state_handler: PowerStateHandler = power_state_handler_class(room_conf['power_state'])
        self.log.debug('setup power_state handler done')

        self.log.debug('setup zeevee_mux')
        self.zeevee_mux = ZeeVeeMux(room_conf['zeevee']['output'])
        self.log.debug('setup zeevee mux done')

        self.log.debug('setup power_state_binding')
        self.power_state_binding = create_knx_binding(
            xknx_binding, room_conf['power_state']['group_address'],
            f'{room_name} Power State',
            self.on_power_state_changed)
        self.log.debug('setup power_state_binding done')

        self.input_bindings = dict()
        for input_name, input_conf in room_conf['zeevee']['input'].items():
            self.log.debug(f'setup input_binding for "{input_name}"')
            self.input_bindings[input_name] = create_knx_binding(
                xknx_binding, input_conf['group_address'],
                f'{room_name} Input {input_name}',
                lambda switch, bound_input_name=input_name: self.on_input_changed(switch, bound_input_name))
            self.log.debug(f'setup input_binding for "{input_name}" done')

        self.log.info('setup done')

    async def on_power_state_changed(self, switch: xknx.devices.Switch):
        self.log.debug(f'power_state switch changed to {switch.state}')
        if switch.state:
            await self.power_on()
        else:
            await self.power_off()

    async def on_input_changed(self, switch: xknx.devices.Switch, input_name):
        if switch.state:
            self.log.info(f'input switch activated: {input_name}')
            await asyncio.gather(
                self.power_on(),
                self.zeevee_mux.select_input(input_name),
                self.set_input_selection_switches_to_off(except_input=input_name)
            )

    async def set_input_selection_switches_to_off(self, except_input=None):
        self.log.info(f'setting input-switches to off (excluding {except_input})')
        await asyncio.gather(*[
            binding.switch.set(input_name == except_input)
            for input_name, binding in self.input_bindings.items()
        ])
        self.log.info(f'setting input-switches to off (excluding {except_input}) done')

    async def power_on(self):
        self.log.info('power on')
        await asyncio.gather(
            self.power_state_binding.set_on(),
            self.power_state_handler.power_on(),
            self.set_input_selection_switches_to_current_input()
        )
        self.log.info('power on done')

    async def power_off(self):
        self.log.info('power off')
        await asyncio.gather(
            self.power_state_binding.set_off(),
            self.power_state_handler.power_off(),
            self.set_input_selection_switches_to_off()
        )
        self.log.info('power off done')

    async def set_input_selection_switches_to_current_input(self):
        current_input = await self.zeevee_mux.get_current_input()
        await self.set_input_selection_switches_to_off(current_input)
