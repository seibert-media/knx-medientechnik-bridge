import asyncio

import aiohttp

from power_handler import PowerHandler

MONITOR_POLL_INTERVAL_SECONDS = 1.0


class PowerHandlerTasmota(PowerHandler):
    def __init__(self, output_key, conf, on_device_power_changed):
        super().__init__(output_key, conf, on_device_power_changed)
        self.host = conf['host']
        self.command_lock = asyncio.Lock()

        self.state_monitor = asyncio.create_task(self.monitor())
        self.last_state = None

    async def stop(self):
        self.log.debug('stopping')
        self.state_monitor.cancel()

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        result = await self.try_send_command('Power ON')
        return result['POWER'] == 'ON'

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        result = await self.try_send_command('Power OFF')
        return result['POWER'] == 'OFF'

    async def is_powered_on(self) -> bool:
        result = await self.try_send_command('Power')
        return result['POWER'] == 'ON'

    async def try_send_command(self, command):
        try:
            return await self.send_command(command)
        except:
            self.log.warning("send_command failed")

    async def send_command(self, command):
        async with aiohttp.ClientSession() as session:
            async with session.get('http://' + self.host + '/cm', params={'cmnd': command}) as response:
                return await response.json()

    async def monitor(self):
        while True:
            new_state = await self.is_powered_on()
            if self.last_state is not None and self.last_state != new_state:
                self.log.info(f"state changed to {new_state}")
                await self.on_device_power_changed(new_state)

            self.last_state = new_state
            await asyncio.sleep(MONITOR_POLL_INTERVAL_SECONDS)
