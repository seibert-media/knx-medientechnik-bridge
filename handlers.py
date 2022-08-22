from mux_handler_dummy import MuxHandlerDummy
from mux_handler_zeevee import MuxHandlerZeeVee
from power_handler_dummy import PowerHandlerDummy
from power_handler_pjlink import PowerHandlerPJLink

POWER_HANDLERS = {
    'dummy': PowerHandlerDummy,
    'pjlink': PowerHandlerPJLink,
}

MUX_HANDLERS = {
    'dummy': MuxHandlerDummy,
    'zeevee': MuxHandlerZeeVee,
}
