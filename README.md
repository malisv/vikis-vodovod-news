# Vikis Vodovod News — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant custom integration that scrapes water utility notifications from
[vikis.info](https://vikis.info) and exposes them as sensor data for your dashboards.

## What it does

During summer months, water outages and restrictions are common in many regions.
The water utility posts service notifications on vikis.info, each with an
auto-incrementing ID. This integration:

- Periodically checks for new notifications by scanning forward from the last known ID
- Parses date, title, and description from each notification
- Flags notifications containing your keywords as **priority**
- Exposes all collected news as sensor attributes for use in dashboards or automations

## Installation

### HACS (recommended)

1. Add this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) in HACS
2. Search for "Vikis Vodovod News" and install
3. Restart Home Assistant

### Manual

Copy the `custom_components/vikis_vodovod_news/` folder to your Home Assistant
`custom_components/` directory and restart.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration** > search "Vikis Vodovod News"
2. Enter the latest known news ID (e.g., `606`) — you can find this by browsing
   `https://vikis.info/sr/event/show/606` and incrementing until you get a 500 error
3. Set polling interval (default: 2 hours)
4. Optionally enter comma-separated keywords for priority flagging (e.g., `Dabrobosanska, Zlatište`)
5. Set max stored news items (default: 20)

## Sensor attributes

The integration creates one sensor entity: `sensor.vikis_vodovod_news`

| Attribute | Type | Description |
|-----------|------|-------------|
| `news` | list | List of news items, newest first |
| `last_id` | int | Highest scanned ID |
| `last_scan` | string | ISO timestamp of last scan |

Each news item in the `news` list:
```json
{
  "id": 606,
  "date": "15.06.2026.",
  "title": "Obavještenje za potrošače...",
  "description": "Obavještavamo potrošače...",
  "priority": true
}
```

## Services

- **`vikis_vodovod_news.scan_now`** — trigger an immediate scan for new notifications

## License

MIT