import asyncio
import logging

import xknx.devices
from xknx.telegram import TelegramDirection

from handlers import POWER_HANDLERS, MUX_HANDLERS
from knxbinding import DualAddressKnxBinding, SingleAddressKnxBinding
from mux_handler import MuxHandler
from power_handler import PowerHandler

MONITOR_INTERVAL_SECONDS = 1


class System(object):
    def __init__(self, xknx_binding, system_key, system_conf):
        self.system_key = system_key
        self.system_conf = system_conf

        self.log = logging.getLogger(f'bridge.system["{system_key}"]')
        self.log.info('setup')

        self.log.debug('setup power_handler')
        power_handler_class = POWER_HANDLERS[system_conf['power']['protocol']]
        self.power_handler: PowerHandler = power_handler_class(system_key, system_conf['power'])
        self.log.debug('setup power handler done')

        self.log.debug('setup mux_handler')
        mux_handler_class = MUX_HANDLERS[system_conf['mux']['protocol']]
        self.mux_handler: MuxHandler = mux_handler_class(system_key, system_conf['mux'])
        self.log.debug('setup mux_handler done')

        self.log.debug('setup power_button_binding')
        self.power_button_binding = DualAddressKnxBinding(
            xknx_binding,
            system_conf['power']['group_address'],
            system_conf['power']['group_address_sta'],
            f'{system_key} Power',
            self.on_power_button_toggled)
        self.log.debug('setup power_button_binding done')

        self.input_button_bindings = dict()
        for input_key, input_conf in system_conf['mux']['input'].items():
            self.log.debug(f'setup input_button_bindings for "{input_key}"')
            self.input_button_bindings[input_key] = SingleAddressKnxBinding(
                xknx_binding,
                input_conf['group_address'],
                f'{system_key} Input {input_key}',
                lambda button, bound_input_key=input_key: self.on_input_button_pressed(button, bound_input_key))
            self.log.debug(f'setup input_button_bindings for "{input_key}" done')

        self.log.debug('starting monitor_task task')
        self.monitor_task = asyncio.create_task(self.monitor_device_state())
        self.log.info('setup done')

    def stop(self):
        self.log.debug('stopping monitor_task task')
        self.monitor_task.cancel()

    async def on_power_button_toggled(self, switch: xknx.devices.Switch):
        if switch.switch.telegram.direction == TelegramDirection.OUTGOING:
            return

        self.log.info(f'power_button toggled to {switch.state}')
        if switch.state:
            await asyncio.gather(
                self.power_handler.power_on(),
                self.set_input_selection_buttons_to_current_input()
            )
        else:
            await asyncio.gather(
                self.power_handler.power_off(),
                self.set_input_selection_buttons_to_off()
            )
        self.log.info(f'power_button toggled to {switch.state} done')

    async def on_input_button_pressed(self, switch: xknx.devices.Switch, input_key):
        if switch.switch.telegram.direction == TelegramDirection.OUTGOING:
            return

        if switch.state:
            self.log.info(f'input_button "{input_key}" pressed')
            await asyncio.gather(
                self.set_power_button_to_on(),
                self.power_handler.power_on(),
                self.mux_handler.select_input(input_key),
                self.set_input_selection_buttons_to_off(except_input=input_key)
            )
            self.log.info(f'input_button "{input_key}" pressed done')

    async def set_power_button_to_on(self):
        self.log.debug(f'setting power_button to on')
        await self.power_button_binding.set_status_on()
        self.log.debug(f'setting power_button to on done')

    async def set_input_selection_buttons_to_off(self, except_input=None):
        self.log.debug(f'setting input_selection_buttons to off (except {except_input})')
        await asyncio.gather(*[
            binding.set_status_off()
            for input_key, binding in self.input_button_bindings.items()
            if except_input is None or input_key != except_input
        ])
        self.log.debug(f'setting input_selection_buttons to off (except {except_input}) done')

    async def set_input_selection_buttons_to_current_input(self):
        current_input = await self.mux_handler.get_current_input()
        self.log.debug(f'setting input_selection_buttons to "{current_input}"')
        await asyncio.gather(*[
            binding.set_status(input_key == current_input)
            for input_key, binding in self.input_button_bindings.items()
        ])
        self.log.debug(f'setting input_selection_buttons to "{current_input}" done')

    async def monitor_device_state(self):
        while True:
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)

            self.log.debug(f'checking current device state')
            current_power, current_input = await asyncio.gather(
                self.power_handler.is_powered_on(),
                self.mux_handler.get_current_input(),
            )

            if current_power != bool(self.power_button_binding.state):
                self.log.debug(
                    f'device power changed externally to {current_power}, updating power_button')
                if current_power:
                    await asyncio.gather(
                        self.power_button_binding.set_status_on(),
                        self.set_input_selection_buttons_to_current_input()
                    )
                else:
                    await asyncio.gather(
                        self.power_button_binding.set_status_off(),
                        self.set_input_selection_buttons_to_off()
                    )
                self.log.debug(
                    f'device power changed externally to {current_power}, updating power_button done')

            if current_input in self.input_button_bindings and self.input_button_bindings[current_input].state is False:
                if not current_power:
                    self.log.debug(f'device input changed externally to {current_input} '
                                   f'but device is powered off, not updating buttons')
                else:
                    self.log.debug(f'device input changed externally to {current_input}, updating input_buttons')
                    await self.set_input_selection_buttons_to_current_input()
                    self.log.debug(f'device input changed externally to {current_input}, updating input_buttons done')
