import json
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from custom_components.vikis_vodovod_news.const import (
    CONF_KEYWORDS,
    CONF_LATEST_NEWS_ID,
    CONF_MAX_NEWS_ITEMS,
    CONF_POLL_INTERVAL,
    DEFAULT_MAX_NEWS_ITEMS,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    MAX_SCAN_ATTEMPTS,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from custom_components.vikis_vodovod_news.coordinator import (
    VikisVodovodNewsCoordinator,
)


# ---------------------------------------------------------------------------
# HTML samples matching real vikis.info responses
# ---------------------------------------------------------------------------

HTML_SINGLE_P = """<div class="modal-service-info">
  <h3>Servisne informacije</h3>
  <div class="modal-status">
    <p>Stanje za <span class="date">15.06.2026.</span></p>
    <p><i class="icon icon-alert"></i> <span class="title">Obavještenje za potrošače</span></p>
  </div>
  <div class="modal-description">
    <p>Dana 15.06.2026. doći će do prekida u vodosnabdijevanju.</p>
  </div>
</div>"""

HTML_MULTI_P = """<div class="modal-service-info">
  <h3>Servisne informacije</h3>
  <div class="modal-status">
    <p>Stanje za <span class="date">15.06.2026.</span></p>
    <p><i class="icon icon-alert"></i> <span class="title">Obavještenje</span></p>
  </div>
  <div class="modal-description">
    <p>Prvi paragraf.</p>
    <p>Drugi paragraf.</p>
    <p>Treći paragraf.</p>
  </div>
</div>"""

HTML_MISSING_FIELDS = """<div class="modal-service-info">
  <div class="modal-status">
    <p><span class="date">15.06.2026.</span></p>
  </div>
</div>"""


# =========================================================================
# Coordinator helper
# =========================================================================


@pytest.fixture
def mock_store():
    store = AsyncMock()
    data = {"last_id": 606, "news": []}

    async def async_load():
        return data

    async def async_save(val):
        data.clear()
        data.update(val)

    store.async_load.side_effect = async_load
    store.async_save.side_effect = async_save
    return store


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.data = {
        CONF_LATEST_NEWS_ID: 606,
        CONF_POLL_INTERVAL: 120,
        CONF_KEYWORDS: "Dabrobosanska, Zlatište",
        CONF_MAX_NEWS_ITEMS: 20,
    }
    entry.options = {}
    return entry


@pytest.fixture
def coordinator(mock_entry, mock_store):
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=lambda fn, html, nid: fn(html, nid)
    )
    with patch(
        "custom_components.vikis_vodovod_news.coordinator.Store",
        return_value=mock_store,
    ):
        with patch(
            "custom_components.vikis_vodovod_news.coordinator.DataUpdateCoordinator.__init__",
            return_value=None,
        ):
            coord = VikisVodovodNewsCoordinator(hass, mock_entry)
            coord._store = mock_store
            coord.hass = hass
            yield coord


# =========================================================================
# _parse_keywords (static)
# =========================================================================


class TestParseKeywords:
    def test_empty(self):
        assert VikisVodovodNewsCoordinator._parse_keywords("") == []

    def test_single(self):
        assert VikisVodovodNewsCoordinator._parse_keywords("Dabrobosanska") == [
            "Dabrobosanska"
        ]

    def test_multiple(self):
        assert VikisVodovodNewsCoordinator._parse_keywords(
            "Dabrobosanska, Zlatište"
        ) == ["Dabrobosanska", "Zlatište"]

    def test_whitespace(self):
        assert VikisVodovodNewsCoordinator._parse_keywords(
            "  foo , bar  "
        ) == ["foo", "bar"]

    def test_only_commas(self):
        assert VikisVodovodNewsCoordinator._parse_keywords("  , , ") == []


# =========================================================================
# _evaluate_priority (static)
# =========================================================================


class TestEvaluatePriority:
    def test_no_keywords(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                "Title", "desc", []
            )
            is False
        )

    def test_match_title(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                "Dabrobosanska ulica", "opis", ["Dabrobosanska"]
            )
            is True
        )

    def test_match_description(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                "Opšte obavještenje",
                "Radovi u Dabrobosanskoj ulici",
                ["Dabrobosanskoj"],
            )
            is True
        )

    def test_case_insensitive(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                "dabrobosanska ulica", "opis", ["Dabrobosanska"]
            )
            is True
        )

    def test_no_match(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                "Neke druge vijesti", "opis", ["Dabrobosanska"]
            )
            is False
        )

    def test_multiple_keywords_one_match(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                "Zlatište rezervoar", "opis", ["Dabrobosanska", "Zlatište"]
            )
            is True
        )

    def test_none_title(self):
        assert (
            VikisVodovodNewsCoordinator._evaluate_priority(
                None, "Dabrobosanska ulica", ["Dabrobosanska"]
            )
            is True
        )


# =========================================================================
# _parse_html
# =========================================================================


class TestParseHtml:
    def test_valid_html(self, coordinator):
        result = coordinator._parse_html(HTML_SINGLE_P, 606)
        assert result["id"] == 606
        assert result["date"] == "15.06.2026."
        assert result["title"] == "Obavještenje za potrošače"
        assert "prekida u vodosnabdijevanju" in result["description"]

    def test_multi_paragraph(self, coordinator):
        result = coordinator._parse_html(HTML_MULTI_P, 607)
        assert result["id"] == 607
        assert "\n" in result["description"]
        parts = result["description"].split("\n")
        assert len(parts) == 3
        assert parts[0] == "Prvi paragraf."
        assert parts[2] == "Treći paragraf."

    def test_missing_title(self, coordinator):
        result = coordinator._parse_html(HTML_MISSING_FIELDS, 608)
        assert result["id"] == 608
        assert result["date"] == "15.06.2026."
        assert result["title"] is None
        assert result["description"] == ""

    def test_priority_default(self, coordinator):
        result = coordinator._parse_html(HTML_SINGLE_P, 606)
        assert result["priority"] is False


# =========================================================================
# _reevaluate_priorities
# =========================================================================


class TestReevaluatePriorities:
    def test_reevaluate_with_keywords(self, coordinator):
        news = [
            {"id": 606, "title": "Dabrobosanska ulica", "description": "", "priority": False},
            {"id": 607, "title": "Druga vijest", "description": "", "priority": True},
        ]
        result = coordinator._reevaluate_priorities(news)
        assert result[0]["priority"] is True  # now matches keyword
        assert result[1]["priority"] is False  # no longer matches

    def test_empty_list(self, coordinator):
        assert coordinator._reevaluate_priorities([]) == []

    def test_no_keywords_stays_false(self, coordinator):
        coordinator._filter_keywords = []
        news = [
            {"id": 606, "title": "Dabrobosanska", "description": "", "priority": False},
        ]
        result = coordinator._reevaluate_priorities(news)
        assert result[0]["priority"] is False


# =========================================================================
# _merged_config
# =========================================================================


class TestMergedConfig:
    def test_data_only(self, coordinator):
        cfg = coordinator._merged_config()
        assert cfg[CONF_LATEST_NEWS_ID] == 606
        assert cfg[CONF_POLL_INTERVAL] == 120
        assert cfg[CONF_KEYWORDS] == "Dabrobosanska, Zlatište"
        assert cfg[CONF_MAX_NEWS_ITEMS] == 20

    def test_options_override_data(self, coordinator):
        coordinator._entry.options = {CONF_POLL_INTERVAL: 60}
        cfg = coordinator._merged_config()
        assert cfg[CONF_POLL_INTERVAL] == 60
        assert cfg[CONF_LATEST_NEWS_ID] == 606  # unchanged

    def test_options_empty(self, coordinator):
        coordinator._entry.options = {}
        cfg = coordinator._merged_config()
        assert cfg[CONF_POLL_INTERVAL] == 120


# =========================================================================
# update_config
# =========================================================================


class TestUpdateConfig:
    def test_updates_keywords_and_reapplies(self, coordinator):
        new_entry = MagicMock()
        new_entry.data = {
            CONF_LATEST_NEWS_ID: 606,
            CONF_POLL_INTERVAL: 120,
            CONF_KEYWORDS: "NoviKljuc",
            CONF_MAX_NEWS_ITEMS: 20,
        }
        new_entry.options = {}
        coordinator._stored_data = {
            "last_id": 610,
            "news": [
                {"id": 610, "title": "NoviKljuc ulica", "description": "", "priority": False},
            ],
        }
        coordinator.update_config(new_entry)
        assert coordinator._filter_keywords == ["NoviKljuc"]
        assert coordinator._latest_news_id == 606


# =========================================================================
# _async_update_data — Store loading on first call
# =========================================================================


@pytest.mark.asyncio
async def test_first_load_from_store(coordinator, mock_store):
    """On first _async_update_data, Store should be loaded."""
    coord = coordinator
    coord._stored_data = None

    # Simulate 607 returns 500 (no new news)
    with patch.object(coord, "_fetch_and_parse", return_value=None):
        result = await coord._async_update_data()

    assert coord._stored_data is not None
    assert result["news"] == []
    assert result["last_id"] == 606


@pytest.mark.asyncio
async def test_discovers_multiple_new_ids(coordinator, mock_store):
    """Scan loop collects 607 and 608 before hitting 500. Newest first."""
    news_607 = {"id": 607, "date": "16.06.", "title": "T1", "description": "D1", "priority": False}
    news_608 = {"id": 608, "date": "17.06.", "title": "T2", "description": "D2", "priority": True}

    calls = iter([news_607, news_608, None])

    async def fake_fetch(nid):
        return next(calls)

    coord = coordinator
    coord._stored_data = {"last_id": 606, "news": []}

    with patch.object(coord, "_fetch_and_parse", side_effect=fake_fetch):
        result = await coord._async_update_data()

    assert len(result["news"]) == 2
    # Newest (highest ID) first
    assert result["news"][0]["id"] == 608
    assert result["news"][1]["id"] == 607
    assert result["last_id"] == 608


@pytest.mark.asyncio
async def test_deduplication(coordinator, mock_store):
    """Same ID discovered and in store — deduplicate (newest first)."""
    news_607 = {"id": 607, "date": "16.06.", "title": "T1", "description": "D1", "priority": False}
    news_608 = {"id": 608, "date": "17.06.", "title": "T2", "description": "D2", "priority": True}
    news_609 = {"id": 609, "date": "18.06.", "title": "T3", "description": "D3", "priority": False}

    coord = coordinator
    # Store already has 607 and 608; last_id=607 means 608 was previously stored
    coord._stored_data = {
        "last_id": 607,
        "news": [news_608, news_607],
    }

    # Discover 608 again (already stored) and 609 (new)
    calls = iter([news_608, news_609, None])

    async def fake_fetch(nid):
        return next(calls)

    with patch.object(coord, "_fetch_and_parse", side_effect=fake_fetch):
        result = await coord._async_update_data()

    # Expect 3 unique items, newest first: 609, 608, 607
    assert len(result["news"]) == 3
    assert result["news"][0]["id"] == 609
    assert result["news"][1]["id"] == 608
    assert result["news"][2]["id"] == 607
    assert result["last_id"] == 609


@pytest.mark.asyncio
async def test_truncation_to_max(coordinator, mock_store):
    """News list capped at max_news_items (newest first)."""
    coord = coordinator
    coord._max_news_items = 2

    news_607 = {"id": 607, "date": "16.06.", "title": "T1", "description": "D1", "priority": False}
    news_608 = {"id": 608, "date": "17.06.", "title": "T2", "description": "D2", "priority": False}
    news_609 = {"id": 609, "date": "18.06.", "title": "T3", "description": "D3", "priority": False}
    news_610 = {"id": 610, "date": "19.06.", "title": "T4", "description": "D4", "priority": False}

    coord._stored_data = {"last_id": 608, "news": [news_608, news_607]}

    calls = iter([news_609, news_610, None])

    async def fake_fetch(nid):
        return next(calls)

    with patch.object(coord, "_fetch_and_parse", side_effect=fake_fetch):
        result = await coord._async_update_data()

    assert len(result["news"]) == 2
    # Newest items kept: 610, 609
    assert result["news"][0]["id"] == 610
    assert result["news"][1]["id"] == 609


@pytest.mark.asyncio
async def test_connection_error_does_not_advance_last_id(coordinator, mock_store):
    """On connection error, break and do not advance last_id."""
    coord = coordinator
    coord._stored_data = {"last_id": 606, "news": []}

    with patch.object(coord, "_fetch_and_parse", return_value=None):
        result = await coord._async_update_data()

    assert result["last_id"] == 606
    assert result["news"] == []


@pytest.mark.asyncio
async def test_raises_on_no_news_id(coordinator, mock_store):
    """UpdateFailed if no latest_news_id configured."""
    coord = coordinator
    coord._latest_news_id = None
    coord._stored_data = {"last_id": None, "news": []}

    from homeassistant.helpers.update_coordinator import UpdateFailed

    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


# =========================================================================
# _fetch_and_parse
# =========================================================================


@pytest.mark.asyncio
async def test_fetch_and_parse_200(coordinator, mock_store, mock_entry):
    """200 response returns parsed dict."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.text = AsyncMock(return_value=HTML_SINGLE_P)

    mock_session = AsyncMock()
    mock_session.get = MagicMock()
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "custom_components.vikis_vodovod_news.coordinator.async_get_clientsession",
        return_value=mock_session,
    ):
        result = await coordinator._fetch_and_parse(606)

    assert result is not None
    assert result["id"] == 606
    assert result["date"] == "15.06.2026."
    assert result["title"] == "Obavještenje za potrošače"


@pytest.mark.asyncio
async def test_fetch_and_parse_500(coordinator, mock_store):
    """500 response returns None."""
    mock_resp = AsyncMock()
    mock_resp.status = 500

    mock_session = AsyncMock()
    mock_session.get = MagicMock()
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "custom_components.vikis_vodovod_news.coordinator.async_get_clientsession",
        return_value=mock_session,
    ):
        result = await coordinator._fetch_and_parse(999)

    assert result is None


# =========================================================================
# Config flow
# =========================================================================


class TestConfigFlow:
    @pytest.mark.asyncio
    async def test_step_order(self):
        from custom_components.vikis_vodovod_news.config_flow import (
            VikisVodovodNewsConfigFlow,
        )

        flow = VikisVodovodNewsConfigFlow()
        flow.hass = MagicMock()

        # Step 1: user
        with patch.object(flow, "async_show_form") as mock_show:
            result = await flow.async_step_user()
            assert result is not None  # async_show_form called
            step_id_passed = mock_show.call_args[1].get("step_id", "")

        # Simulate user input for step 1
        result = await flow.async_step_user({CONF_LATEST_NEWS_ID: 606})
        assert result["type"] == "form"  # type = async_step_poll_interval
        assert result["step_id"] == "poll_interval"

        # Step 2: poll interval
        result = await flow.async_step_poll_interval({CONF_POLL_INTERVAL: 60})
        assert result["step_id"] == "keywords"

        # Step 3: keywords
        result = await flow.async_step_keywords({CONF_KEYWORDS: "Dabrobosanska"})
        assert result["step_id"] == "max_news_items"

        # Step 4: max items → create entry
        result = await flow.async_step_max_news_items({CONF_MAX_NEWS_ITEMS: 10})
        assert result["type"] == "create_entry"
        assert result["title"] == "Vikis Vodovod News"
        assert result["data"][CONF_LATEST_NEWS_ID] == 606
        assert result["data"][CONF_POLL_INTERVAL] == 60
        assert result["data"][CONF_KEYWORDS] == "Dabrobosanska"
        assert result["data"][CONF_MAX_NEWS_ITEMS] == 10

    @pytest.mark.asyncio
    async def test_step_keywords_default_empty(self):
        from custom_components.vikis_vodovod_news.config_flow import (
            VikisVodovodNewsConfigFlow,
        )

        flow = VikisVodovodNewsConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_keywords({})
        # Empty dict should set keywords to ""
        assert flow._data[CONF_KEYWORDS] == ""


class TestOptionsFlow:
    @pytest.mark.asyncio
    async def test_reads_merged_config(self):
        from custom_components.vikis_vodovod_news.config_flow import (
            VikisVodovodNewsOptionsFlow,
        )

        entry = MagicMock()
        entry.data = {
            CONF_LATEST_NEWS_ID: 606,
            CONF_POLL_INTERVAL: 120,
            CONF_KEYWORDS: "Dabrobosanska",
            CONF_MAX_NEWS_ITEMS: 20,
        }
        entry.options = {CONF_POLL_INTERVAL: 60}

        flow = VikisVodovodNewsOptionsFlow(entry)
        flow.hass = MagicMock()

        # Show form — should use merged defaults (60 from options, not 120 from data)
        form = await flow.async_step_init()
        assert form["type"] == "form"

        # Submit with merged value — should save options correctly
        result = await flow.async_step_init({
            CONF_LATEST_NEWS_ID: 606,
            CONF_POLL_INTERVAL: 60,
            CONF_KEYWORDS: "Dabrobosanska",
            CONF_MAX_NEWS_ITEMS: 20,
        })
        assert result["type"] == "create_entry"
        assert result["data"][CONF_POLL_INTERVAL] == 60

    @pytest.mark.asyncio
    async def test_saves_options(self):
        from custom_components.vikis_vodovod_news.config_flow import (
            VikisVodovodNewsOptionsFlow,
        )

        entry = MagicMock()
        entry.data = {CONF_LATEST_NEWS_ID: 606, CONF_POLL_INTERVAL: 120, CONF_KEYWORDS: "", CONF_MAX_NEWS_ITEMS: 20}
        entry.options = {}

        flow = VikisVodovodNewsOptionsFlow(entry)
        flow.hass = MagicMock()

        result = await flow.async_step_init({
            CONF_LATEST_NEWS_ID: 606,
            CONF_POLL_INTERVAL: 30,
            CONF_KEYWORDS: "foo",
            CONF_MAX_NEWS_ITEMS: 10,
        })
        assert result["type"] == "create_entry"
        assert result["data"][CONF_POLL_INTERVAL] == 30


# =========================================================================
# Sensor
# =========================================================================


class TestSensor:
    def test_state_is_news_count(self):
        from custom_components.vikis_vodovod_news.sensor import (
            VikisVodovodNewsSensor,
        )

        coord = MagicMock()
        coord.data = {
            "news": [{"id": 606}, {"id": 607}],
            "last_id": 607,
            "last_scan": None,
        }

        sensor = VikisVodovodNewsSensor(coord)
        assert sensor.native_value == 2

    def test_state_zero_when_no_data(self):
        from custom_components.vikis_vodovod_news.sensor import (
            VikisVodovodNewsSensor,
        )

        coord = MagicMock()
        coord.data = None

        sensor = VikisVodovodNewsSensor(coord)
        assert sensor.native_value == 0

    def test_attributes(self):
        from custom_components.vikis_vodovod_news.sensor import (
            VikisVodovodNewsSensor,
        )

        coord = MagicMock()
        coord.data = {
            "news": [{"id": 606, "date": "15.06.", "title": "T", "description": "D", "priority": False}],
            "last_id": 606,
            "last_scan": None,
        }

        sensor = VikisVodovodNewsSensor(coord)
        attrs = sensor.extra_state_attributes
        assert len(attrs["news"]) == 1
        assert attrs["last_id"] == 606
        assert attrs["last_scan"] is None

    def test_attributes_with_scan(self):
        from custom_components.vikis_vodovod_news.sensor import (
            VikisVodovodNewsSensor,
        )
        from datetime import datetime

        dt = datetime(2026, 6, 24, 12, 0, 0)
        coord = MagicMock()
        coord.data = {
            "news": [],
            "last_id": 606,
            "last_scan": dt,
        }

        sensor = VikisVodovodNewsSensor(coord)
        attrs = sensor.extra_state_attributes
        assert attrs["last_scan"] == "2026-06-24T12:00:00"

    def test_unique_id_and_icon(self):
        from custom_components.vikis_vodovod_news.sensor import (
            VikisVodovodNewsSensor,
        )

        sensor = VikisVodovodNewsSensor(MagicMock())
        assert sensor.unique_id == "vikis_vodovod_news"
        assert sensor.icon == "mdi:water"