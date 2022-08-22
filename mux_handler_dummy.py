from mux_handler import MuxHandler


class MuxHandlerDummy(MuxHandler):
    def __init__(self, output_key, conf, on_mux_input_changed):
        super().__init__(output_key, conf, on_mux_input_changed)
        self.input_key = None

    async def select_input(self, input_key: str) -> bool:
        self.log.info(f'Switching to {input_key}')
        self.input_key = input_key
        return True

    async def get_current_input(self) -> str:
        return self.input_key
