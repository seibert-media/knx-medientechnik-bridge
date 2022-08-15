import asyncio
from typing import Optional

from power_state_handler import PowerStateHandler

MONITOR_INTERVAL_SECONDS = 30


class PowerStateHandlerPJLink(PowerStateHandler):
    def __init__(self, conf):
        super().__init__(conf)
        self.monitor_task: Optional[asyncio.Task] = None
        self.host = conf['host']
        self.password = conf['password']

    async def send_command(self, command: str) -> str:
        # connect
        # receive token
        # token + password | md5
        # "hash%1POWR ?"
        # read next line
        # disconnect
        pass

    async def power_on(self) -> bool:
        return await self.send_command('%1POWR 1') == '%1POWR=OK'

    async def power_off(self) -> bool:
        return await self.send_command('%1POWR 0') == '%1POWR=OK'

    async def is_powered_on(self) -> bool:
        return await self.send_command('%1POWR ?') == '%1POWR=1'
