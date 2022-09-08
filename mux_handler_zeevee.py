import asyncio
import re
from telnetlib import Telnet
from typing import Optional

from mux_handler import MuxHandler

MONITOR_POLL_INTERVAL_SECONDS = 1.0
TELNET_PORT = 23


# maps from
# [
#   'encoder.EventSpaceAppleTv.hdmiAudio; EncoderIN, EventSpaceConfidenceScreen',
#   'encoder.EventSpaceAppleTv.video; EncoderIN, EventSpaceConfidenceScreen',
# ]
# to
# {
#   'EncoderIN': 'EventSpaceAppleTv',
#   'EventSpaceConfidenceScreen': 'EventSpaceAppleTv',
# }
def map_connections(connection_info_lines: list[str]) -> dict:
    result_map = dict()

    for line in connection_info_lines:
        match = re.match(r'^encoder\.([^.]+)\.([^;]+); (.*)$', line)
        encoder, link_type, decoders = match.groups()
        if link_type != 'video':
            continue

        for decoder in decoders.split(', '):
            result_map[decoder] = encoder

    return result_map


class MuxHandlerZeeVee(MuxHandler):
    def __init__(self, output_key, conf, on_mux_input_changed):
        super().__init__(output_key, conf, on_mux_input_changed)
        self.host = conf['host']
        self.zeevee_output = conf['zeevee_output']

        self.command_lock = asyncio.Lock()

        self.log.debug(f'connecting to {self.host}:{TELNET_PORT}')
        self.telnet = Telnet(self.host, TELNET_PORT)

        self.state_monitor = asyncio.create_task(self.monitor())
        self.last_linked_input = None

    async def stop(self):
        self.log.debug('stopping')
        self.telnet.close()
        self.state_monitor.cancel()

    async def select_input(self, input_key: str):
        self.log.info(f'Switching to {input_key}')

        src = self.inputs[input_key].get('zeevee_name', None)
        dest = self.conf['zeevee_output']
        if src is None:
            await self.unlink(dest)
        else:
            await self.link(dest, src)

    async def unlink(self, dest):
        command = f'join none {dest} fastSwitched'
        result = await self.try_send_command(command) is True
        await self.update_state()
        return result

    async def link(self, dest, src):
        command = f'join {src} {dest} fastSwitched'
        result = await self.try_send_command(command) is True
        await self.update_state()
        return result

    async def get_current_input(self) -> Optional[str]:
        connection_info_lines = await self.try_send_command("show device connections")
        zeevee_connections = map_connections(connection_info_lines)
        linked_zeevee_input = zeevee_connections.get(self.zeevee_output, None)
        self.log.debug(f'linked zeevee input of {self.zeevee_output} is {linked_zeevee_input}')
        for input_key, input_conf in self.inputs.items():
            if input_conf.get('zeevee_name', None) == linked_zeevee_input:
                self.log.debug(f'mapped to input_key {input_key}')
                return input_key

        self.log.debug(f'not mapped to any input_key')
        return None

    async def try_send_command(self, command):
        try:
            return await self.send_command(command)
        except:
            self.log.warning("send_command failed")

    async def send_command(self, command, success_line='Success'):
        async with self.command_lock:
            self.telnet.read_until(b'Zyper$ ', 10)
            self.log.debug(f'sending command_line {command}')
            self.telnet.write(f'{command}\r\n'.encode('ascii'))

            response = self.telnet.read_until(success_line.encode('ascii'), 10)

            lines = response.decode('ascii').split('\r\n')
            if lines[0] == command:
                lines = lines[1:]
            else:
                self.log.warning(f'expected command as first line, was {lines[0]}')

            if lines[-1] == success_line:
                lines = lines[:-1]
            else:
                self.log.warning(f'expected success_line {success_line} as last line, was {lines[-1]}')
                return False

            if len(lines) > 0:
                self.log.debug(f'received response {lines}')
                return lines
            else:
                self.log.debug(f'received no additional response')
                return True

    async def monitor(self):
        while True:
            await self.update_state()
            await asyncio.sleep(MONITOR_POLL_INTERVAL_SECONDS)

    async def update_state(self):
        new_linked_input = await self.get_current_input()
        if self.last_linked_input is not None and self.last_linked_input != new_linked_input:
            self.log.info(f"input changed to {new_linked_input}")
            await self.on_mux_input_changed(new_linked_input)

        self.last_linked_input = new_linked_input
