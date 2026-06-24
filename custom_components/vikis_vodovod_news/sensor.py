from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_LAST_ID, ATTR_LAST_SCAN, ATTR_NEWS, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VikisVodovodNewsSensor(coordinator)])


class VikisVodovodNewsSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Vikis Vodovod News"
    _attr_unique_id = "vikis_vodovod_news"
    _attr_icon = "mdi:water"

    @property
    def native_value(self) -> int:
        data = self.coordinator.data
        if data is None:
            return 0
        return len(data.get(ATTR_NEWS, []))

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        news = data.get(ATTR_NEWS, [])
        last_id = data.get(ATTR_LAST_ID)
        last_scan = data.get(ATTR_LAST_SCAN)
        return {
            ATTR_NEWS: news,
            ATTR_LAST_ID: last_id,
            ATTR_LAST_SCAN: last_scan.isoformat() if last_scan else None,
        }