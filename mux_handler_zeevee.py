from mux_handler import MuxHandler


class MuxHandlerZeeVee(MuxHandler):
    def __init__(self, system_key, output_name):
        super().__init__(system_key, output_name)

    async def select_input(self, input_key: str):
        self.log.info(f'Switching to {input_key}')
        pass

    async def get_current_input(self) -> str:
        return ""
