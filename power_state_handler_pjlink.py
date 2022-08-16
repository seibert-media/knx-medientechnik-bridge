import asyncio
import hashlib
import re

from power_state_handler import PowerStateHandler

PJLINK_PORT = 4352


class PowerStateHandlerPJLink(PowerStateHandler):
    def __init__(self, system_key, conf):
        super().__init__(system_key, conf)
        self.host = conf['host']
        self.password = conf['password']

    async def send_command(self, command: str) -> str:
        self.log.debug(f'connecting to {self.host}:{PJLINK_PORT}')
        reader, writer = await asyncio.open_connection(self.host, PJLINK_PORT)

        welcome_line = (await reader.readline()).decode('ascii').rstrip()
        self.log.debug(f'received welcome_line {welcome_line}')

        auth_prefix = ""
        match = re.match('PJLINK 1 .+', welcome_line)
        if match:
            # so-called security
            nonce = match.group(1)
            auth_prefix = hashlib.md5(nonce + self.password)
        elif welcome_line == 'PJLINK 0':
            # no security
            pass
        else:
            self.log.warn(f'unexpected Welcome-Line from PJLink Host {self.host}:{PJLINK_PORT} - {welcome_line}')

        command_line = (auth_prefix + command).encode('ascii')
        self.log.debug(f'sending command_line {command_line}')
        writer.write(command_line)
        await writer.drain()

        response_line = (await reader.readline()).decode('ascii').rstrip()
        self.log.debug(f'received response_line {response_line}')

        self.log.debug(f'disconnecting from {self.host}:{PJLINK_PORT}')
        writer.close()
        await writer.wait_closed()

        return response_line

    async def power_on(self) -> bool:
        self.log.info('Turning on')
        return await self.send_command('%1POWR 1') == '%1POWR=OK'

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        return await self.send_command('%1POWR 0') == '%1POWR=OK'

    async def is_powered_on(self) -> bool:
        return await self.send_command('%1POWR ?') == '%1POWR=1'
