from mux_handler import MuxHandler


class MuxHandlerDummy(MuxHandler):
    def __init__(self, system_key, conf):
        super().__init__(system_key, conf)
        self.input_key = None

    async def select_input(self, input_key: str):
        self.log.info(f'Switching to {input_key}')
        self.input_key = input_key

    async def get_current_input(self) -> str:
        self.log.debug(f'Query Result: {self.input_key}')
        return self.input_key
