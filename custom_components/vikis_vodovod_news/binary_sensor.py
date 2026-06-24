from datetime import date, datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_ACTIVE_WARNINGS, ATTR_NEWS, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VikisVodovodNewsWarning(coordinator)])


def parse_news_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    raw = date_str.rstrip(".")
    parts = raw.split(".")
    if len(parts) != 3:
        return None
    try:
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (ValueError, IndexError):
        return None


class VikisVodovodNewsWarning(CoordinatorEntity, BinarySensorEntity):
    _attr_name = "Vikis Vodovod News Warning"
    _attr_unique_id = "vikis_vodovod_news_warning"
    _attr_device_class = "safety"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if data is None:
            return False
        today = datetime.now().date()
        news = data.get(ATTR_NEWS, [])
        for item in news:
            item_date = parse_news_date(item.get("date"))
            if item_date is not None and item_date >= today:
                return True
        return False

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        today = datetime.now().date()
        news = data.get(ATTR_NEWS, [])
        active = []
        for item in news:
            item_date = parse_news_date(item.get("date"))
            if item_date is not None and item_date >= today:
                active.append(item)
        return {
            ATTR_ACTIVE_WARNINGS: active,
            "total_news": len(news),
        }