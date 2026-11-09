"""Never publish across social networks without release evidence and clear opt-in."""
from datetime import datetime, timezone
import hashlib
import json
from unittest.mock import Mock

import pytest

from scripts import mn_short_crosspost as p


def _fixture(tmp_path, approved=True):
    video = tmp_path / "2026-11-12_1200_news.mp4"
    video.write_bytes(b"realistic-media-file-for-unit-tests" * 10000)
    digest = hashlib.sha256(video.read_bytes()).hexdigest()
    editorial = {
        "grid": {
            "slot": "12:00", "release_local_date": "2026-11-12",
            "count": 1, "language": "es"
        },
        "source": {
            "title": "A story from a legitimate RSS publisher",
            "publisher": "Example Publisher",
            "url": "https://www.example.org/article",
        },
        "generated": {"title_es": "Una noticia de actualidad documentada"},
    }
    (tmp_path / "CONTROL_PUBLICACION.json").write_text(json.dumps({
        "approved": approved,
        "video_sha256": digest
    }), encoding="utf-8")
    (tmp_path / "editorial.json").write_text(json.dumps(editorial), encoding="utf-8")
    return video, editorial


def test_platform_priority_and_tiktok_explicit_authorization():
    assert p.configured_platforms("facebook,instagram") == ["facebook", "instagram"]
    assert p.configured_platforms("facebook,facebook,instagram") == ["facebook", "instagram"]
    with pytest.raises(ValueError):
        p.configured_platforms("facebook,youtube")
    with pytest.raises(ValueError):
        p.configured_platforms("facebook,tiktok")
    assert p.configured_platforms("facebook,tiktok", tiktok_enabled=True) == [
        "facebook", "tiktok"
    ]


def test_schedule_uses_madrid_timezone_and_requires_future_release():
    editorial = {"grid": {"slot": "12:00", "release_local_date": "2026-11-12"}}
    result = p.planned_utc(editorial, now=datetime(2026, 11, 11, tzinfo=timezone.utc))
    assert result == "2026-11-12T11:00:00Z"
    with pytest.raises(ValueError):
        p.planned_utc(editorial, now=datetime(2026, 11, 12, 10, 59, tzinfo=timezone.utc))


def test_rejects_unreviewed_news_even_when_opted_in(monkeypatch, tmp_path):
    _fixture(tmp_path, approved=False)
    monkeypatch.setenv("MNSHORT_CROSSPOST_ENABLED", "true")
    session = Mock()
    with pytest.raises(RuntimeError, match="retenida"):
        p.upload_scheduled(
            tmp_path, "profile", "fake-key", ["facebook"],
            now=datetime(2026, 11, 11, tzinfo=timezone.utc),
            session=session,
        )
    session.post.assert_not_called()


def test_rejects_unapproved_opt_in(monkeypatch, tmp_path):
    _fixture(tmp_path)
    monkeypatch.delenv("MNSHORT_CROSSPOST_ENABLED", raising=False)
    session = Mock()
    with pytest.raises(RuntimeError, match="no habilitada"):
        p.upload_scheduled(
            tmp_path, "profile", "fake-key", ["facebook"],
            now=datetime(2026, 11, 11, tzinfo=timezone.utc),
            session=session,
        )
    session.post.assert_not_called()


def test_schedules_once_with_idempotency_and_no_youtube(monkeypatch, tmp_path):
    _fixture(tmp_path)
    monkeypatch.setenv("MNSHORT_CROSSPOST_ENABLED", "true")
    session = Mock()
    session.post.return_value.status_code = 202
    session.post.return_value.json.return_value = {
        "success": True, "job_id": "scheduled-job-42",
    }
    result = p.upload_scheduled(
        tmp_path, "mn-short", "fake-key", ["facebook", "instagram"],
        now=datetime(2026, 11, 11, tzinfo=timezone.utc),
        session=session,
    )
    assert result["status"] == "SCHEDULED_NOT_YET_PUBLISHED"
    assert result["job_id"] == "scheduled-job-42"
    assert result["scheduled_date_utc"] == "2026-11-12T11:00:00Z"
    kwargs = session.post.call_args.kwargs
    assert kwargs["allow_redirects"] is False
    assert kwargs["headers"]["Idempotency-Key"].startswith("mnshort-")
    assert ("platform[]", "facebook") in kwargs["data"]
    assert ("platform[]", "instagram") in kwargs["data"]
    assert ("platform[]", "youtube") not in kwargs["data"]
    assert (tmp_path / "PROGRAMACION_REDES.json").exists()


def test_no_blind_retries_when_server_response_is_ambiguous(monkeypatch, tmp_path):
    _fixture(tmp_path)
    monkeypatch.setenv("MNSHORT_CROSSPOST_ENABLED", "true")
    session = Mock()
    session.post.return_value.status_code = 504
    with pytest.raises(RuntimeError, match="No se confirmó"):
        p.upload_scheduled(
            tmp_path, "mn-short", "fake-key", ["facebook"],
            now=datetime(2026, 11, 11, tzinfo=timezone.utc),
            session=session,
        )
    session.post.assert_called_once()
