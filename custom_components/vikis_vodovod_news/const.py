DOMAIN = "vikis_vodovod_news"
BASE_URL = "https://vikis.info/sr/event/show/{news_id}"

DEFAULT_POLL_INTERVAL = 120
DEFAULT_MAX_NEWS_ITEMS = 20
MAX_SCAN_ATTEMPTS = 500

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

CONF_LATEST_NEWS_ID = "latest_news_id"
CONF_POLL_INTERVAL = "poll_interval"
CONF_KEYWORDS = "keywords"
CONF_MAX_NEWS_ITEMS = "max_news_items"

ATTR_NEWS = "news"
ATTR_LAST_ID = "last_id"
ATTR_LAST_SCAN = "last_scan"