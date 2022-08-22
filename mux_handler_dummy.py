from dummy_input import dummy_input_handler
from mux_handler import MuxHandler


class MuxHandlerDummy(MuxHandler):
    def __init__(self, system_key, conf, on_mux_input_changed):
        super().__init__(system_key, conf, on_mux_input_changed)
        self.input_key = None
        for input_key in self.inputs.keys():
            dummy_input_handler().register_dummy_mux_callback(system_key, input_key, self.externally_set_input)

    async def select_input(self, input_key: str) -> bool:
        self.log.info(f'Switching to {input_key}')
        self.input_key = input_key
        return True

    async def get_current_input(self) -> str:
        return self.input_key

    async def externally_set_input(self, new_input_key):
        self.log.info(f'Externally set to {new_input_key}')
        self.input_key = new_input_key
        await self.on_mux_input_changed(new_input_key)
