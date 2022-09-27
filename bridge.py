#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
from typing import Optional

import coloredlogs
import toml as toml
from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType

from dummy_input import dummy_input_handler
from output import Output

coloredlogs.install(
    fmt='%(asctime)s %(levelname)5s %(name)s %(message)s',
    level=os.getenv('LOGGING', logging.INFO),
    milliseconds=True)
log = logging.getLogger("bridge")

logging.getLogger("xknx").setLevel(os.getenv('XKNX_LOGGING', logging.WARNING))

config_files = ['/etc/knx-medientechnik-bridge.toml', os.getcwd() + '/config.toml']
if os.getenv('CONFIG_FILE') is not None:
    config_files = [os.getenv('CONFIG_FILE')]

conf = None
for config_file in config_files:
    log.debug(f'trying {config_file}')
    try:
        with open(config_file, 'r') as f:
            log.info(f'reading {config_file}')
            conf = toml.load(f)
    except OSError:
        pass

if conf is None:
    log.error('could not read any of the specified config-files.')
    log.info(f'tried {config_files}')
    log.info('use CONFIG_FILE env-variable to explicitly specify a location')
    sys.exit(1)

xknx_binding: Optional[XKNX] = None
outputs = dict()


async def connect():
    global xknx_binding
    log.info('connect')
    connection_config = ConnectionConfig()
    connection_config.connection_type = ConnectionType.TUNNELING_TCP
    connection_config.gateway_ip = conf['knx']['gateway']
    xknx_binding = XKNX(connection_config=connection_config)

    log.info('start')
    await xknx_binding.start()


async def setup():
    global outputs
    log.info('setup')
    for output_key, output_conf in conf['output'].items():
        outputs[output_key] = Output(xknx_binding, output_key, output_conf)

    log.info('starting outputs')
    await asyncio.gather(*[
        output.start()
        for output in outputs.values()
    ])


async def teardown():
    log.info("teardown")
    await asyncio.gather(*[
        output.stop()
        for output in outputs.values()
    ], xknx_binding.stop())

    dummy_input_handler().stop()


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.run_until_complete(connect())
loop.run_until_complete(setup())

log.info('operational')
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(teardown())
    log.info("teardown")
