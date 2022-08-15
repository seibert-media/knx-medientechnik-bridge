import asyncio
import logging

import xknx.devices
from xknx.telegram import TelegramDirection

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


class System(object):
    def __init__(self, xknx_binding, system_name, system_conf):
        self.log = logging.getLogger(f'bridge.system["{system_name}"]')
        self.log.info('setup')

        self.log.debug('setup power_state_handler')
        power_state_handler_class = POWER_STATE_HANDLERS[system_conf['power_state']['protocol']]
        self.power_state_handler: PowerStateHandler = power_state_handler_class(system_conf['power_state'])
        self.log.debug('setup power_state handler done')

        self.log.debug('setup zeevee_mux')
        self.zeevee_mux = ZeeVeeMux(system_conf['zeevee']['output'])
        self.log.debug('setup zeevee mux done')

        self.log.debug('setup power_button_binding')
        self.power_button_binding = create_knx_binding(
            xknx_binding, system_conf['power_state']['group_address'],
            f'{system_name} Power State',
            self.on_power_button_toggled)
        self.log.debug('setup power_button_binding done')

        self.input_button_bindings = dict()
        for input_name, input_conf in system_conf['zeevee']['input'].items():
            self.log.debug(f'setup input_button_bindings for "{input_name}"')
            self.input_button_bindings[input_name] = create_knx_binding(
                xknx_binding, input_conf['group_address'],
                f'{system_name} Input {input_name}',
                lambda button, bound_input_name=input_name: self.on_input_button_pressed(button, bound_input_name))
            self.log.debug(f'setup input_button_bindings for "{input_name}" done')

        self.log.info('setup done')

    async def on_power_button_toggled(self, switch: xknx.devices.Switch):
        if switch.switch.telegram.direction == TelegramDirection.OUTGOING:
            return

        self.log.info(f'power_button toggled to {switch.state}')
        if switch.state:
            await asyncio.gather(
                self.power_state_handler.power_on(),
                self.set_input_selection_buttons_to_current_input()
            )
        else:
            await asyncio.gather(
                self.power_state_handler.power_off(),
                self.set_input_selection_buttons_to_off()
            )

    async def on_input_button_pressed(self, switch: xknx.devices.Switch, input_name):
        if switch.switch.telegram.direction == TelegramDirection.OUTGOING:
            return

        if switch.state:
            self.log.info(f'input_button "{input_name}" pressed')
            await asyncio.gather(
                self.set_power_button_to_on(),
                self.power_state_handler.power_on(),
                self.zeevee_mux.select_input(input_name),
                self.set_input_selection_buttons_to_off(except_input=input_name)
            )

    async def set_power_button_to_on(self):
        self.log.debug(f'setting power_button to on')
        await self.power_button_binding.set_on()
        self.log.debug(f'setting power_button to on done')

    async def set_input_selection_buttons_to_off(self, except_input=None):
        self.log.debug(f'setting input_selection_buttons to off (except {except_input})')
        await asyncio.gather(*[
            binding.switch.off()
            for input_name, binding in self.input_button_bindings.items()
            if except_input is None or input_name != except_input
        ])
        self.log.debug(f'setting input_selection_buttons to off (except {except_input}) done')

    async def set_input_selection_buttons_to_current_input(self):
        current_input = await self.zeevee_mux.get_current_input()
        self.log.debug(f'setting input_selection_buttons to "{current_input}"')
        await asyncio.gather(*[
            binding.switch.set(input_name == current_input)
            for input_name, binding in self.input_button_bindings.items()
        ])
        self.log.debug(f'setting input_selection_buttons to "{current_input}" done')
