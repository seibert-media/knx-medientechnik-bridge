#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
from typing import Optional

import toml as toml
from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType

from system import System

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("bridge")
log.setLevel(os.getenv('LOGGING', logging.INFO))

logging.getLogger("xknx").setLevel(os.getenv('XKNX_LOGGING', logging.WARNING))

config_files = ['/etc/knx-medientechnik-bridge.toml', os.getcwd() + '/config.toml']
if os.getenv('CONFIG_FILE') is not None:
    config_files = [os.getenv('CONFIG_FILE')]

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
    log.info('tried ', config_files)
    log.info('use CONFIG_FILE env-variable to explicitly specify a location')
    sys.exit(1)

xknx_binding: Optional[XKNX] = None
systems = dict()


async def connect():
    global xknx_binding
    log.info('connect')
    connection_config = ConnectionConfig()
    connection_config.connection_type = ConnectionType.TUNNELING
    connection_config.gateway_ip = conf['knx']['gateway']
    xknx_binding = XKNX(connection_config=connection_config)
    log.info('connect done')

    log.info('start')
    await xknx_binding.start()
    log.info('start done')


async def setup():
    global systems
    log.info('setup')
    for system_name, system_conf in conf['system'].items():
        log.info(f'setup system "{system_name}')
        systems[system_name] = System(xknx_binding, system_name, system_conf)
    log.info('setup done')


async def teardown():
    log.info("teardown")
    await xknx_binding.stop()
    log.info("teardown done")


loop = asyncio.get_event_loop()
loop.run_until_complete(connect())
loop.run_until_complete(setup())

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(teardown())
