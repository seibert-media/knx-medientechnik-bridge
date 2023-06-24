import asyncio
import hashlib
import re

from power_handler import PowerHandler

MONITOR_POLL_INTERVAL_SECONDS = 5.0
MAX_LINE_LENGTH = 1000

PJLINK_PORT = 4352


async def read_line(reader):
    bytes_read = await reader.read(MAX_LINE_LENGTH)
    return bytes_read.decode('ascii').rstrip()


class PowerHandlerPJLink(PowerHandler):
    def __init__(self, output_key, conf, on_device_power_changed):
        super().__init__(output_key, conf, on_device_power_changed)
        self.host = conf['host']
        self.password = conf.get('password', None)

        self.command_lock = asyncio.Lock()

        self.state_monitor = asyncio.create_task(self.monitor())
        self.last_state = None

    async def stop(self):
        self.log.debug('stopping')
        self.state_monitor.cancel()

    async def try_send_command(self, command):
        try:
            return await asyncio.wait_for(self.send_command(command), timeout=20.0)
        except TimeoutError:
            self.log.warning("send_command timed out")
        except Exception as e:
            self.log.warning("send_command failed: " + repr(e))

    async def send_command(self, command: str) -> str:
        async with self.command_lock:
            self.log.debug(f'connecting to {self.host}:{PJLINK_PORT}')
            reader, writer = await asyncio.open_connection(self.host, PJLINK_PORT)

            self.log.debug(f'authenticating')
            welcome_line = await read_line(reader)
            self.log.debug(f'received welcome_line {welcome_line}')

            match = re.match('PJLINK 1 (.+)', welcome_line)
            if match:
                # so-called security
                nonce = match.group(1)
                nonced_password = nonce + self.password
                auth_prefix = hashlib.md5(nonced_password.encode('ascii')).hexdigest()

            elif welcome_line == 'PJLINK 0':
                # no security
                auth_prefix = ""

            else:
                self.log.error(f'unexpected Welcome-Line from PJLink Host {self.host}:{PJLINK_PORT} - {welcome_line}')

            command_line = auth_prefix + command
            self.log.debug(f'sending command_line {command_line.rstrip()}')
            writer.write((command_line + "\r").encode('ascii'))
            await writer.drain()

            response_line = await read_line(reader)
            self.log.debug(f'received response_line {response_line}')

            self.log.debug(f'disconnecting')
            writer.close()
            await writer.wait_closed()

            return response_line

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        return await self.try_send_command('%1POWR 1') == '%1POWR=OK'

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        return await self.try_send_command('%1POWR 0') == '%1POWR=OK'

    async def is_powered_on(self) -> bool:
        return await self.try_send_command('%1POWR ?') == '%1POWR=1'

    async def monitor(self):
        while True:
            new_state = await self.is_powered_on()
            if self.last_state is not None and self.last_state != new_state:
                self.log.info(f"state changed to {new_state}")
                await self.on_device_power_changed(new_state)

            self.last_state = new_state
            await asyncio.sleep(MONITOR_POLL_INTERVAL_SECONDS)
