# Changelog

## 0.1.0 — 2026-06-24

Initial release.

- Single sensor `sensor.vikis_vodovod_news` with news list attribute
- Configurable polling interval, keywords, max stored items, starting ID
- Incrementing scan — collects multiple new IDs per cycle
- Keyword priority flagging (case-insensitive substring match)
- Persistent storage via `Store` (survives restarts)
- `scan_now` service for manual refresh
- 40 unit tests