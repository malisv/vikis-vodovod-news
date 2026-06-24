from unittest.mock import AsyncMock


class Store(AsyncMock):
    def __init__(self, hass, version, key):
        super().__init__()
        self.hass = hass
        self.version = version
        self.key = key