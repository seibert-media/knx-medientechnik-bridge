from power_state_handler import PowerStateHandler


class PowerStateHandlerPJLink(PowerStateHandler):
    def __init__(self, conf):
        super().__init__(conf)
        self.__temp_state = False

    async def power_on(self) -> bool:
        self.__temp_state = True
        return True

    async def power_off(self) -> bool:
        self.__temp_state = False
        return True

    async def is_powered_on(self) -> bool:
        return self.__temp_state
