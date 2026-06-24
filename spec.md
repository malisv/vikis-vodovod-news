# vikis_vodovod_news — Implementation Spec

Home Assistant custom integration for HACS. Scrapes water utility news from
`https://vikis.info/sr/event/show/{id}` and exposes them as sensors.

## Source of truth

`requirement.txt` (repo root) is the single authoritative requirements document.

## Directory structure (under `code/`)

```
custom_components/
  vikis_vodovod_news/
    manifest.json       — version, domain, HA requirements, I/O dependency
    const.py            — DOMAIN, defaults, attribute names
    __init__.py         — async_setup_entry, register services
    config_flow.py      — UI config flow (4-step form)
    coordinator.py      — DataUpdateCoordinator, scan logic, Store persistence
    sensor.py           — single SensorEntity, reads coordinator data
    services.yaml       — scan_now service declaration
```

## Config flow (4 steps)

| Step | Field | Type | Required | Default |
|------|-------|------|----------|---------|
| 1 | `latest_news_id` | int | yes | — |
| 2 | `poll_interval` | int (minutes) | yes | 120 |
| 3 | `keywords` | string (comma-separated) | no | `""` |
| 4 | `max_news_items` | int | yes | 20 |

An OptionsFlow must allow editing all fields after setup. When keywords change,
re-compute `priority` on all stored items.

## HTML parsing (200 OK responses)

| Field | CSS selector | Fallback |
|-------|-------------|----------|
| Date | `.modal-status span.date` | `None` |
| Title | `.modal-status span.title` | `None` |
| Description | `.modal-description p` (all `<p>`, get_text, join with `\n`) | `""` |
| Priority | `True` if any keyword (lowercased) is a substring of (title + description, lowercased) | `False` |

Use `beautifulsoup4` (bundled with HA). HTTP requests via `httpx` (bundled).

## Scanning logic (in `coordinator.py`)

```
FOR id = stored_last_id + 1 UP TO stored_last_id + 500:
    GET https://vikis.info/sr/event/show/{id}
    IF 200 OK:
        parse HTML -> {id, date, title, description, priority}
        append to discovered list
        stored_last_id = id
    ELSE (500 or any non-200):
        BREAK (stop scanning this cycle)
```

- Multiple new IDs in one cycle: yes — if 607 and 608 are both new, both are collected.
- Max 500 attempts per cycle to prevent infinite loops.
- Connection errors (timeout, DNS, 404): log warning, BREAK. Do NOT advance last_id past the gap.

## Persistence

Use `homeassistant.helpers.storage.Store` with key `"vikis_vodovod_news"`.

Stored data:
```json
{
  "last_id": 606,
  "news": [
    {"id": 606, "date": "15.06.2026.", "title": "...", "description": "...", "priority": false},
    {"id": 605, "date": "15.04.2026.", "title": "...", "description": "...", "priority": true}
  ]
}
```

On startup: load from Store. On each scan: prepend new items, truncate to `max_news_items`, save back to Store.

## Sensor entity (`sensor.py`)

- **Platform**: `sensor`
- **Unique ID**: `"vikis_vodovod_news"`
- **State**: `len(news)` (integer)
- **Attributes**:
  - `news`: `list[dict]` of `{id, date, title, description, priority}` sorted newest-first
  - `last_id`: highest scanned ID
  - `last_scan`: ISO 8601 timestamp of last scan

Entity class uses `SensorEntity` from HA. Read from coordinator data.
Use `RestoreEntity` mixin so state survives coordinator init delay.

## Coordinator (`coordinator.py`)

- Extends `DataUpdateCoordinator` with `update_interval` from config.
- `_async_update_data()`: runs scan logic, merges results, persists to Store.
- Returns the entire news list as data (sensor reads it via `self.coordinator.data`).

## Service (`scan_now`)

- Defined in `services.yaml`.
- Registered in `__init__.py` `async_setup_entry`.
- Calls `coordinator.async_request_refresh()`.

## manifest.json

```json
{
  "domain": "vikis_vodovod_news",
  "name": "Vikis Vodovod News",
  "version": "0.1.0",
  "iot_class": "cloud_polling",
  "requirements": ["beautifulsoup4"],
  "dependencies": [],
  "codeowners": ["@your_github_handle"],
  "config_flow": true
}
```

## Edge cases

- **ID gaps**: if 607->500 but 608->200, scan stops at 607. Next cycle tries 608. No extra logic needed.
- **Empty/malformed HTML**: set missing fields to `None`, still record the item.
- **No keywords configured**: all items get `priority: False`.
- **Duplicate IDs** (re-scanning same range after restart before Store loads): deduplicate by ID.
- **Rate limiting**: no known limits. Requests are sequential with implicit delay from HA's coordinator scheduling.