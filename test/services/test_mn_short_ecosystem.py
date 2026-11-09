"""Tests for the one-Short-per-slot news scheduler; network is never used."""
from datetime import datetime, timezone

import pytest

from scripts import mn_short_ecosystem as m


def test_config_is_six_slots_one_video_per_slot():
    data = m.config()
    assert data["timezone"] == "Europe/Madrid"
    assert [w["time"] for w in data["windows"]] == [
        "08:00", "10:00", "12:00", "16:00", "18:00", "20:00"
    ]
    assert data["language"] == "es"
    assert data["video_count_per_slot"] == 1


def test_schedule_cron_maps_to_madrid_local_hour():
    assert m.resolved_slot(scheduled_cron="0 8 * * *") == "08:00"
    assert m.resolved_slot(scheduled_cron="0 20 * * *") == "20:00"
    assert m.resolved_slot(raw_slot="18:00") == "18:00"
    with pytest.raises(ValueError):
        m.resolved_slot(scheduled_cron="0 6 * * *")
    with pytest.raises(ValueError):
        m.resolved_slot(raw_slot="07:00")


def test_alternates_technology_and_gaming_by_day():
    from datetime import date
    a = m.resolved_topic("20:00", date(2026, 11, 9))
    b = m.resolved_topic("20:00", date(2026, 11, 10))
    assert {a, b} == {"technology", "gaming"}


def test_normalize_url_and_dedup():
    original = "https://www.example.com/article?utm_source=rss#news"
    assert m.normalize_url(original) == "https://www.example.com/article"
    assert m.story_identifier(original) == m.story_identifier("https://www.example.com/article")
    recent = datetime.now(timezone.utc).isoformat()
    ledger = {"items": [
        {"source_id": m.story_identifier(original),
         "title_signature": m.title_signature("An article about battery storage deployment"),
         "created_at": recent}
    ]}
    ids, titles = m.existing_keys(ledger)
    assert m.story_identifier(original) in ids
    assert m.title_signature("An article about battery storage deployment") in titles


def test_news_feed_parses_recent_article():
    fresh = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    feed = (
        f'<rss><channel><item><title>Important research advances in modern batteries</title>'
        f'<description>A research team has published new results in energy storage, '
        f'with implications for charging and battery supply chains worldwide.</description>'
        f'<link>https://example.org/a</link><pubDate>{fresh}</pubDate>'
        f'</item></channel></rss>'
    )
    values = m.parse_feed(feed.encode(), "Example RSS", "technology")
    assert len(values) == 1
    assert values[0]["category"] == "technology"
    assert values[0]["url"] == "https://example.org/a"


def test_story_selection_avoids_a_previous_slot(monkeypatch):
    fresh = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    description = ("Researchers released a new energy system after two years of "
                   "engineering validation and several independent laboratory trials.")
    xml = (
        f'<rss><channel><item><title>Important research advances in modern batteries</title>'
        f'<description>{description}</description>'
        f'<link>https://example.org/used</link><pubDate>{fresh}</pubDate></item>'
        f'<item><title>New engineering announcement about sustainable heat</title>'
        f'<description>{description}</description>'
        f'<link>https://example.org/unused</link><pubDate>{fresh}</pubDate></item>'
        f'</channel></rss>'
    ).encode()
    monkeypatch.setattr(m, "config", lambda: {"feeds": {"technology": [
        {"publisher": "Example", "url": "https://example.org/feed"}
    ]}})
    monkeypatch.setattr(m, "request_bytes", lambda url: xml)
    ledger = {"items": [{
        "source_id": m.story_identifier("https://example.org/used"),
        "title_signature": m.title_signature("Important research advances in modern batteries"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }]}
    assert m.choose_story("technology", ledger)["url"] == "https://example.org/unused"


def test_missing_persistent_history_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(m, "HISTORY_PATH", tmp_path / "missing.json")
    with pytest.raises(RuntimeError, match="Missing persistent"):
        m.read_history()
