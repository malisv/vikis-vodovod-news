class BinarySensorEntity:
    _attr_name = None
    _attr_unique_id = None
    _attr_device_class = None
    _attr_should_poll = False
    _attr_is_on = False
    _attr_available = True

    def __init__(self):
        self.hass = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def device_class(self):
        return self._attr_device_class

    @property
    def is_on(self):
        return self._attr_is_on

    @property
    def extra_state_attributes(self):
        return {}