class UpdateFailed(Exception):
    pass


class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval=None):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = {}
        self.last_update_success = True

    async def async_config_entry_first_refresh(self):
        pass

    async def async_request_refresh(self):
        pass


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.hass = coordinator.hass if hasattr(coordinator, 'hass') else None