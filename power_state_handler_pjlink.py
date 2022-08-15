from power_state_handler import PowerStateHandler

MONITOR_INTERVAL_SECONDS = 30


class PowerStateHandlerPJLink(PowerStateHandler):
    def __init__(self, system_key, conf):
        super().__init__(system_key, conf)
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
        self.log.info('Turning on')
        return await self.send_command('%1POWR 1') == '%1POWR=OK'

    async def power_off(self) -> bool:
        self.log.info('Turning off')
        return await self.send_command('%1POWR 0') == '%1POWR=OK'

    async def is_powered_on(self) -> bool:
        result = await self.send_command('%1POWR ?') == '%1POWR=1'
        self.log.debug(f'Query Result: {result}')
        return result
