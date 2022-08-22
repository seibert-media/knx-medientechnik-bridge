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

        self.temp_current_input = input_key

        src = self.inputs[input_key].get('zeevee_name', None)
        dest = self.conf['zeevee_output']
        if src is None:
            await self.unlink(dest)
        else:
            await self.link(dest, src)

    async def unlink(self, dest):
        command_line = f'join none {dest} fastSwitched'
        return await self.send_command(command_line)

    async def link(self, dest, src):
        command = f'join {src} {dest} fastSwitched'
        response = await self.send_command(command)
        return response == 'Success'

    async def get_current_input(self) -> str:
        # Zyper$ show device connections
        # encoder.EventSpaceAppleTv.hdmiAudio; EncoderIN, EventSpaceRegieDisplay, EventSpaceConfidenceScreen, EventSpaceBeamer
        # encoder.EventSpaceAppleTv.video; EncoderIN, EventSpaceRegieDisplay, EventSpaceConfidenceScreen, EventSpaceBeamer
        # encoder.hq-infobeamer1.hdmiAudio; KuecheDisplay
        # encoder.hq-infobeamer1.video; KuecheDisplay, EmpfangDisplay1, EmpfangDisplay2

        # command = f'show device connections'
        # response = await self.send_command(command)
        # for line in response.rstrip().split("\b"):
        #    self.log.debug(f'line {line}')  # TODO

        return self.temp_current_input

    async def send_command(self, command):
        self.log.debug(f'connecting to {self.host}:{TELNET_PORT}')
        with Telnet(self.host, TELNET_PORT) as tn:
            tn.read_until(b'Zyper$', 10)
            self.log.debug(f'sending command_line {command}')
            tn.write(f'{command}\n'.encode('ascii'))

            response = tn.read_until(b"\n", 10)
            self.log.debug(f'received response {response}')

            return response.decode('ascii')
