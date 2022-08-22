from abc import ABC

import xknx.devices


class KnxBinding(ABC):
    def __init__(self, control_binding: xknx.devices.Switch, status_binding: xknx.devices.Switch):
        self.status_binding = status_binding
        self.control_binding = control_binding

    @property
    def state(self):
        return self.status_binding.state

    async def set_status(self, new_status: bool):
        self.control_binding.switch.value = new_status
        await self.status_binding.switch.set(new_status)

    async def set_status_on(self):
        await self.set_status(True)

    async def set_status_off(self):
        await self.set_status(False)


class DualAddressKnxBinding(KnxBinding):
    def __init__(self, xknx_binding, group_address, group_address_sta, binding_name, updated_cb):
        super().__init__(
            # receive commands here
            xknx.devices.Switch(
                xknx_binding,
                name=binding_name,
                group_address=group_address,
                respond_to_read=False, sync_state=False,
                device_updated_cb=updated_cb
            ),

            # write status here
            xknx.devices.Switch(
                xknx_binding,
                name=binding_name + " Sta",
                group_address=group_address_sta,
                respond_to_read=True, sync_state=False
            )
        )


class SingleAddressKnxBinding(KnxBinding):
    def __init__(self, xknx_binding, group_address, binding_name, updated_cb):
        bidi_binding = xknx.devices.Switch(
            xknx_binding,
            name=binding_name,
            group_address=group_address,
            # we *are* the switch, so we behave like a true knx device and respond to reads
            # while not trying to read the state from another device on the bus
            respond_to_read=True, sync_state=False,
            device_updated_cb=updated_cb
        )
        super().__init__(bidi_binding, bidi_binding)
