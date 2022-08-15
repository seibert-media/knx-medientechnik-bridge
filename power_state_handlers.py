from power_state_handler_dummy import PowerStateHandlerDummy
from power_state_handler_pjlink import PowerStateHandlerPJLink

POWER_STATE_HANDLERS = {
    'dummy': PowerStateHandlerDummy,
    'pjlink': PowerStateHandlerPJLink,
}
