class ZeeVeeMux(object):
    def __init__(self, output):
        self.output = output

    async def select_input(self, input: str) -> bool:
        pass

    async def get_current_input(self) -> str:
        pass
