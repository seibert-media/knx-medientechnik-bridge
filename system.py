import asyncio
import logging

from handlers import POWER_HANDLERS, MUX_HANDLERS
from knxbinding import DualAddressKnxBinding
from mux_handler import MuxHandler
from power_handler import PowerHandler

MONITOR_INTERVAL_SECONDS = 1


class System(object):
    def __init__(self, xknx_binding, system_key, system_conf):
        self.system_key = system_key
        self.system_conf = system_conf

        self.log = logging.getLogger(f'bridge.system["{system_key}"]')
        self.log.info('setup')

        power_handler_class = POWER_HANDLERS[system_conf['power']['protocol']]
        self.power_handler: PowerHandler = power_handler_class(
            system_key, system_conf['power'], self.on_device_power_changed)

        mux_handler_class = MUX_HANDLERS[system_conf['mux']['protocol']]
        self.mux_handler: MuxHandler = mux_handler_class(
            system_key, system_conf['mux'], self.on_mux_input_changed)

        self.power_button_binding = DualAddressKnxBinding(
            xknx_binding,
            system_conf['power']['group_address'],
            system_conf['power']['group_address_sta'],
            f'{system_key} Power',
            self.on_power_button_pressed)

        self.input_button_bindings = dict()
        for input_key, input_conf in system_conf['mux']['input'].items():
            self.input_button_bindings[input_key] = DualAddressKnxBinding(
                xknx_binding,
                input_conf['group_address'],
                input_conf['group_address_sta'],
                f'{system_key} Input {input_key}',
                lambda new_state, bound_input_key=input_key: self.on_input_button_pressed(bound_input_key, new_state))

        self.log.info('setup done')

    async def start(self):
        self.log.debug('updating knx state from devices')
        await asyncio.gather(
            self.power_button_binding.set_state(await self.power_handler.is_powered_on()),
            self.set_input_buttons_to(await self.mux_handler.get_current_input())
        )
        self.log.debug('updating knx state from devices done')

    async def stop(self):
        self.log.debug('stopping')
        await asyncio.gather(
            self.power_handler.stop(),
            self.mux_handler.stop(),
        )
        self.log.debug('stopping done')

    async def on_power_button_pressed(self, new_state):
        self.log.debug(f'power button pressed, setting device state to {new_state}')
        await self.power_handler.set_power(new_state)
        self.log.debug(f'power button pressed, setting device state to {new_state} done')

    async def on_device_power_changed(self, new_state):
        self.log.debug(f'device power changes, setting button state {new_state}')
        await self.power_button_binding.set_state(new_state)
        self.log.debug(f'device power changes, setting button state {new_state} done')

    async def on_input_button_pressed(self, input_key, new_state):
        if not new_state:
            return

        self.log.debug(f'input button {input_key} set to on')
        await asyncio.gather(
            self.mux_handler.select_input(input_key),
            self.power_handler.power_on(),
            self.set_input_buttons_to_off(except_input=input_key),
        )
        self.log.debug(f'input button {input_key} set to on done')

    async def on_mux_input_changed(self, new_input_key):
        self.log.debug(f'mux input changed to {new_input_key}')
        await self.set_input_buttons_to(new_input_key)
        self.log.debug(f'mux input changed to {new_input_key} done')

    async def set_input_buttons_to_off(self, except_input=None):
        self.log.debug(f'setting input buttons to off except {except_input}')
        await asyncio.gather(*[
            binding.set_state_off()
            for input_key, binding in self.input_button_bindings.items()
            if except_input is None or input_key != except_input
        ])
        self.log.debug(f'setting input buttons to off except {except_input} done')

    async def set_input_buttons_to(self, input_to_set_on):
        self.log.debug(f'setting input buttons to {input_to_set_on}')
        await asyncio.gather(*[
            binding.set_state(input_key == input_to_set_on)
            for input_key, binding in self.input_button_bindings.items()
        ])
        self.log.debug(f'setting input buttons to {input_to_set_on} done')
