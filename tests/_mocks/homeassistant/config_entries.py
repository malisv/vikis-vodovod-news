from unittest.mock import MagicMock


class ConfigEntry(MagicMock):
    pass


class ConfigFlow:
    VERSION = 1
    domain = None

    def __init_subclass__(cls, *, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.domain = domain

    def __init__(self):
        self._data = {}
        self.hass = MagicMock()

    def async_show_form(self, **kw):
        return {"type": "form", "step_id": kw.get("step_id"), "data_schema": kw.get("data_schema")}

    def async_create_entry(self, **kw):
        return {"type": "create_entry", **kw}


class OptionsFlow:
    def __init__(self, config_entry=None):
        if config_entry is not None:
            self._config_entry = config_entry
        self.hass = MagicMock()

    def async_show_form(self, **kw):
        return {"type": "form", "step_id": kw.get("step_id"), "data_schema": kw.get("data_schema")}

    def async_create_entry(self, **kw):
        return {"type": "create_entry", **kw}