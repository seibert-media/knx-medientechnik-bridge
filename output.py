import asyncio
import logging

from handlers import POWER_HANDLERS, MUX_HANDLERS
from knxbinding import DualAddressKnxBinding
from mux_handler import MuxHandler
from power_handler import PowerHandler


class Output(object):
    def __init__(self, xknx_binding, output_key, output_conf):
        self.output_key = output_key
        self.output_conf = output_conf
        self.should_auto_power_on = output_conf.get('auto_power_on', True)

        self.log = logging.getLogger(f'bridge.output["{output_key}"]')
        self.log.info('setup')

        if 'power' in output_conf:
            power_handler_class = POWER_HANDLERS[output_conf['power']['protocol']]
            self.power_handler: PowerHandler = power_handler_class(
                output_key, output_conf['power'], self.on_device_power_changed)

            self.power_button_binding = DualAddressKnxBinding(
                xknx_binding,
                output_conf['power']['group_address'],
                output_conf['power']['group_address_sta'],
                f'{output_key} Power',
                self.on_power_button_pressed)
        else:
            self.power_handler = None
            self.power_button_binding = None

        if 'mux' in output_conf:
            mux_handler_class = MUX_HANDLERS[output_conf['mux']['protocol']]
            self.mux_handler: MuxHandler = mux_handler_class(
                output_key, output_conf['mux'], self.on_mux_input_changed)

            self.input_button_bindings = dict()
            for input_key, input_conf in output_conf['mux']['input'].items():
                self.input_button_bindings[input_key] = DualAddressKnxBinding(
                    xknx_binding,
                    input_conf['group_address'],
                    input_conf['group_address_sta'],
                    f'{output_key} Input {input_key}',
                    lambda new_state, bound_input_key=input_key:
                    self.on_input_button_pressed(bound_input_key, new_state))
        else:
            self.mux_handler = None
            self.input_button_bindings = None

        self.log.info('setup done')

    async def start(self):
        self.log.debug('updating knx state from devices')
        if self.mux_handler is not None:
            current_input = await self.mux_handler.get_current_input()
            await self.set_input_buttons_to(current_input)

        if self.power_button_binding is not None:
            await self.power_button_binding.set_state(await self.power_handler.is_powered_on()),

    async def stop(self):
        self.log.debug('stopping')
        if self.power_handler is not None:
            await self.power_handler.stop()

        if self.mux_handler is not None:
            await self.mux_handler.stop()

    async def on_power_button_pressed(self, new_state):
        self.log.debug(f'power button pressed, setting device state to {new_state}')
        if self.power_handler is not None:
            await self.power_handler.set_power(new_state)

    async def on_device_power_changed(self, new_state):
        self.log.debug(f'device power changes, setting button state {new_state}')
        if self.power_button_binding is not None:
            await self.power_button_binding.set_state(new_state)

    async def on_input_button_pressed(self, input_key, new_state):
        if not new_state:
            return

        self.log.debug(f'input button {input_key} set to on')
        if self.mux_handler is not None:
            await self.mux_handler.select_input(input_key)

        if self.power_handler is not None and self.should_auto_power_on:
            await self.power_handler.power_on()

    async def on_mux_input_changed(self, new_input_key):
        self.log.debug(f'mux input changed to {new_input_key}')
        await self.set_input_buttons_to(new_input_key)

    async def set_input_buttons_to(self, input_to_set_on):
        if self.input_button_bindings is None:
            return

        self.log.debug(f'setting input buttons to {input_to_set_on}')
        await asyncio.gather(*[
            binding.set_state(input_key == input_to_set_on)
            for input_key, binding in self.input_button_bindings.items()
        ])
