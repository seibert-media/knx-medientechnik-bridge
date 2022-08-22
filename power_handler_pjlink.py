import asyncio
import hashlib
import re

from power_handler import PowerHandler

MAX_LINE_LENGTH = 1000

PJLINK_PORT = 4352


async def read_line(reader):
    bytes_read = await reader.read(MAX_LINE_LENGTH)
    return bytes_read.decode('ascii').rstrip()


class PowerHandlerPJLink(PowerHandler):
    def __init__(self, system_key, conf, on_device_power_changed):
        super().__init__(system_key, conf, on_device_power_changed)
        self.host = conf['host']
        self.password = conf['password']

        self.auth_prefix = None
        self.reader = None
        self.writer = None

        self.state_monitor = asyncio.create_task(self.monitor())
        self.last_state = None

    async def stop(self):
        self.state_monitor.cancel()

    async def send_command(self, command: str) -> str:
        await self.open_or_reopen_socket()
        self.log.debug(f'connecting to {self.host}:{PJLINK_PORT}')

        command_line = self.auth_prefix + command
        self.log.debug(f'sending command_line {command_line.rstrip()}')
        self.writer.write((command_line + "\r\n").encode('ascii'))
        await self.writer.drain()

        response_line = await read_line(self.reader)
        self.log.debug(f'received response_line {response_line}')

        return response_line

    async def open_or_reopen_socket(self):
        if self.reader is None or self.writer is None or self.writer.is_closing():
            self.reader, self.writer = await asyncio.open_connection(self.host, PJLINK_PORT)

            await self.handle_auth()

    async def handle_auth(self):
        welcome_line = await read_line(self.reader)
        self.log.debug(f'received welcome_line {welcome_line}')

        match = re.match('PJLINK 1 (.+)', welcome_line)
        if match:
            # so-called security
            nonce = match.group(1)
            nonced_password = nonce + self.password
            self.auth_prefix = hashlib.md5(nonced_password.encode('ascii')).hexdigest()

        elif welcome_line == 'PJLINK 0':
            # no security
            self.auth_prefix = ""
            pass

        else:
            self.log.error(f'unexpected Welcome-Line from PJLink Host {self.host}:{PJLINK_PORT} - {welcome_line}')

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        return await self.send_command('%1POWR 1') == '%1POWR=OK'

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        return await self.send_command('%1POWR 0') == '%1POWR=OK'

    async def is_powered_on(self) -> bool:
        return await self.send_command('%1POWR ?') == '%1POWR=1'

    async def monitor(self):
        new_state = await self.is_powered_on()
        if self.last_state is not None and self.last_state != new_state:
            await self.on_device_power_changed(new_state)

        self.last_state = new_state
