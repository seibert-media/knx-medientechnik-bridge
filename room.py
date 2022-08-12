import asyncio
import logging

import xknx.devices

from power_state_handler import PowerStateHandler
from power_state_handlers import POWER_STATE_HANDLERS
from zeevee_mux import ZeeVeeMux


class BooleanActor(object):
    def __init__(self, xknx_binding, binding_name, switch_ga, status_ga, switch_toggled_cb):
        self.switch_ga = switch_ga
        self.status_ga = status_ga
        self.switch_toggled_cb = switch_toggled_cb
        self._internal_status = False

        self.switch_binding = xknx.devices.Switch(
            xknx_binding,
            name=binding_name,
            group_address=switch_ga,
            respond_to_read=False, sync_state=False,
            device_updated_cb=self.on_device_updated
        )

        self.status_binding = xknx.devices.Switch(
            xknx_binding,
            name=f'{binding_name} Sta',
            group_address=status_ga,
            respond_to_read=True, sync_state=False
        )

    async def set_status_on(self):
        await self.set_status(True)

    async def set_status_off(self):
        await self.set_status(False)

    async def set_status(self, new_status: bool):
        self._internal_status = new_status
        await self.status_binding.switch.set(new_status)

    async def on_device_updated(self, _switch):
        new_value = self.switch_binding.switch.value
        await self.switch_toggled_cb(new_value)

    def get_status(self) -> bool:
        pass


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
        self.power_state_binding = BooleanActor(
            xknx_binding, f'{room_name} Power State',
            room_conf['power_state']['switch_ga'],
            room_conf['power_state']['status_ga'],
            self.on_power_state_changed)
        self.log.debug('setup power_state_binding done')

        self.input_bindings = dict()
        for input_name, input_conf in room_conf['zeevee']['input'].items():
            self.log.debug(f'setup input_binding for "{input_name}"')
            self.input_bindings[input_name] = BooleanActor(
                xknx_binding, f'{room_name} Input {input_name}',
                input_conf['switch_ga'], input_conf['status_ga'],
                lambda new_value, bound_input_name=input_name: self.on_input_changed(bound_input_name, new_value))
            self.log.debug(f'setup input_binding for "{input_name}" done')

        self.log.info('setup done')

    async def on_power_state_changed(self, new_value):
        self.log.debug(f'power_state switch changed to {new_value}')
        if new_value:
            await self.power_on()
        else:
            await self.power_off()

    async def on_input_changed(self, input_name, new_value):
        if new_value:
            self.log.info(f'input switch activated: {input_name}')
            await asyncio.gather(
                self.power_on(),
                self.zeevee_mux.select_input(input_name),
                self.set_input_selection_switches_to_off(except_input=input_name)
            )

    async def set_input_selection_switches_to_off(self, except_input=None):
        self.log.info(f'setting input-switches to off (excluding {except_input})')
        await asyncio.gather(*[
            binding.set_status(input_name == except_input)
            for input_name, binding in self.input_bindings.items()
        ])
        self.log.info(f'setting input-switches to off (excluding {except_input}) done')

    async def power_on(self):
        self.log.info('power on')
        await asyncio.gather(
            self.power_state_binding.set_status_on(),
            self.power_state_handler.power_on()
        )
        self.log.info('power on done')

    async def power_off(self):
        self.log.info('power off')
        await asyncio.gather(
            self.power_state_binding.set_status_off(),
            self.power_state_handler.power_off(),
            self.set_input_selection_switches_to_off()
        )
        self.log.info('power off done')
