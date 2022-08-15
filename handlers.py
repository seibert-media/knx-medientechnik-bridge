from mux_handler_dummy import MuxHandlerDummy
from mux_handler_zeevee import MuxHandlerZeeVee
from power_state_handler_dummy import PowerStateHandlerDummy
from power_state_handler_pjlink import PowerStateHandlerPJLink

POWER_STATE_HANDLERS = {
    'dummy': PowerStateHandlerDummy,
    'pjlink': PowerStateHandlerPJLink,
}

MUX_HANDLERS = {
    'dummy': MuxHandlerDummy,
    'zeevee': MuxHandlerZeeVee,
}
