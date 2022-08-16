from telnetlib import Telnet

from mux_handler import MuxHandler

TELNET_PORT = 23


class MuxHandlerZeeVee(MuxHandler):
    def __init__(self, system_key, conf):
        super().__init__(system_key, conf)
        self.host = conf['host']
        self.temp_current_input = None  # TODO query system

    async def select_input(self, input_key: str):
        self.log.info(f'Switching to {input_key}')

        src = self.inputs[input_key]['zeevee_name']
        dest = self.conf['zeevee_output']

        self.log.debug(f'connecting to {self.host}:{TELNET_PORT}')
        with Telnet(self.host, TELNET_PORT) as tn:
            tn.read_until(b'Zyper$', 10)
            command_line = f'join {src} {dest} fastSwitched'
            self.log.debug(f'sending command_line {command_line}')
            tn.write(f'{command_line}\n'.encode('ascii'))

            ret = tn.expect([
                br'.*\n(Error:.*)',
                br'.*\n(Success)'
            ], 10)

            response_line = ret[1].group(1)
            self.log.debug(f'received response_line {response_line}')

            success = response_line == 'Success'

            if success:
                self.temp_current_input = input_key

            return success

    async def get_current_input(self) -> str:
        # TODO send `show device connections` command
        return self.temp_current_input
