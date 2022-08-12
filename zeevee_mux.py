class ZeeVeeMux(object):
    def __init__(self, output):
        self.output = output
        self._temp_internal_state = None

    async def select_input(self, input: str):
        self._temp_internal_state = input

    async def get_current_input(self) -> str:
        return self._temp_internal_state
