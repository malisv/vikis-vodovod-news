class SensorEntity:
    _attr_name = None
    _attr_unique_id = None
    _attr_icon = None
    _attr_native_value = None
    _attr_extra_state_attributes = None
    _attr_should_poll = False
    _attr_assumed_state = False
    _attr_available = True

    def __init__(self):
        self.hass = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def icon(self):
        return self._attr_icon

    @property
    def name(self):
        return self._attr_name

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        return {}