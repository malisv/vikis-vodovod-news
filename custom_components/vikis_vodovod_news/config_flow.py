import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_KEYWORDS,
    CONF_LATEST_NEWS_ID,
    CONF_MAX_NEWS_ITEMS,
    CONF_POLL_INTERVAL,
    DEFAULT_MAX_NEWS_ITEMS,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)


class VikisVodovodNewsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data[CONF_LATEST_NEWS_ID] = user_input[CONF_LATEST_NEWS_ID]
            return await self.async_step_poll_interval()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LATEST_NEWS_ID): cv.positive_int,
                }
            ),
        )

    async def async_step_poll_interval(self, user_input=None):
        if user_input is not None:
            self._data[CONF_POLL_INTERVAL] = user_input[CONF_POLL_INTERVAL]
            return await self.async_step_keywords()
        return self.async_show_form(
            step_id="poll_interval",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                    ): cv.positive_int,
                }
            ),
        )

    async def async_step_keywords(self, user_input=None):
        if user_input is not None:
            self._data[CONF_KEYWORDS] = user_input.get(CONF_KEYWORDS, "")
            return await self.async_step_max_news_items()
        return self.async_show_form(
            step_id="keywords",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_KEYWORDS, default=""): str,
                }
            ),
        )

    async def async_step_max_news_items(self, user_input=None):
        if user_input is not None:
            self._data[CONF_MAX_NEWS_ITEMS] = user_input[CONF_MAX_NEWS_ITEMS]
            return self.async_create_entry(
                title="Vikis Vodovod News",
                data=self._data,
            )
        return self.async_show_form(
            step_id="max_news_items",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MAX_NEWS_ITEMS, default=DEFAULT_MAX_NEWS_ITEMS
                    ): cv.positive_int,
                }
            ),
        )


class VikisVodovodNewsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        merged = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LATEST_NEWS_ID, default=merged.get(CONF_LATEST_NEWS_ID)
                    ): cv.positive_int,
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=merged.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_KEYWORDS, default=merged.get(CONF_KEYWORDS, "")
                    ): str,
                    vol.Required(
                        CONF_MAX_NEWS_ITEMS,
                        default=merged.get(CONF_MAX_NEWS_ITEMS, DEFAULT_MAX_NEWS_ITEMS),
                    ): cv.positive_int,
                }
            ),
        )