import logging
from datetime import datetime, timedelta

import aiohttp
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    BASE_URL,
    CONF_KEYWORDS,
    CONF_LATEST_NEWS_ID,
    CONF_MAX_NEWS_ITEMS,
    CONF_POLL_INTERVAL,
    DOMAIN,
    MAX_SCAN_ATTEMPTS,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class VikisVodovodNewsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        config = self._merged_config()
        self._filter_keywords: list[str] = self._parse_keywords(
            config.get(CONF_KEYWORDS, "")
        )
        self._max_news_items: int = config.get(
            CONF_MAX_NEWS_ITEMS, 20
        )
        self._latest_news_id: int | None = config.get(CONF_LATEST_NEWS_ID)
        self.last_scan: datetime | None = None

        poll = config.get(CONF_POLL_INTERVAL, 120)
        update_interval = timedelta(minutes=poll)

        self._store = Store[dict](hass, STORAGE_VERSION, STORAGE_KEY)
        self._stored_data: dict | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    def _merged_config(self) -> dict:
        return {**self._entry.data, **self._entry.options}

    @staticmethod
    def _parse_keywords(raw: str) -> list[str]:
        return [kw.strip() for kw in raw.split(",") if kw.strip()]

    def update_config(self, entry: ConfigEntry) -> None:
        self._entry = entry
        config = self._merged_config()
        self._filter_keywords = self._parse_keywords(
            config.get(CONF_KEYWORDS, "")
        )
        self._max_news_items = config.get(CONF_MAX_NEWS_ITEMS, 20)
        self._latest_news_id = config.get(CONF_LATEST_NEWS_ID)
        poll = config.get(CONF_POLL_INTERVAL, 120)
        self.update_interval = timedelta(minutes=poll)

    async def _async_setup(self):
        self._stored_data = await self._store.async_load() or {}

    async def _async_update_data(self) -> dict:
        stored = self._stored_data or {}
        news: list[dict] = stored.get("news", [])
        last_id: int | None = stored.get("last_id", self._latest_news_id)

        if last_id is None:
            raise UpdateFailed("No latest_news_id configured")

        candidate = last_id + 1
        limit = last_id + 1 + MAX_SCAN_ATTEMPTS
        discovered: list[dict] = []

        while candidate <= limit:
            item = await self._fetch_and_parse(candidate)
            if item is None:
                break
            discovered.append(item)
            last_id = candidate
            candidate += 1

        if discovered:
            all_news = discovered + news
            seen_ids = set()
            deduped = []
            for n in all_news:
                nid = n["id"]
                if nid not in seen_ids:
                    seen_ids.add(nid)
                    deduped.append(n)
            news = deduped[: self._max_news_items]

        if news or discovered:
            await self._store.async_save({"last_id": last_id, "news": news})

        self._stored_data = {"last_id": last_id, "news": news}
        self.last_scan = dt_util.utcnow()

        return {
            "news": news,
            "last_id": last_id,
            "last_scan": self.last_scan,
        }

    async def _fetch_and_parse(self, news_id: int) -> dict | None:
        url = BASE_URL.format(news_id=news_id)
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as exc:
            _LOGGER.warning("Error fetching ID %d: %s", news_id, exc)
            return None

        return await self.hass.async_add_executor_job(
            self._parse_html, html, news_id
        )

    def _parse_html(self, html: str, news_id: int) -> dict | None:
        soup = BeautifulSoup(html, "html.parser")

        date_el = soup.select_one(".modal-status span.date")
        date = date_el.get_text(strip=True) if date_el else None

        title_el = soup.select_one(".modal-status span.title")
        title = title_el.get_text(strip=True) if title_el else None

        desc_els = soup.select(".modal-description p")
        description = (
            "\n".join(
                p.get_text(strip=True) for p in desc_els if p.get_text(strip=True)
            )
            if desc_els
            else ""
        )

        text_to_check = (title or "") + " " + description
        priority = False
        if self._filter_keywords:
            lower_text = text_to_check.lower()
            priority = any(kw.lower() in lower_text for kw in self._filter_keywords)

        return {
            "id": news_id,
            "date": date,
            "title": title,
            "description": description,
            "priority": priority,
        }