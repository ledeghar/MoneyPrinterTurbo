"""Ensure the automatic publisher remains fail-closed until verifiable QA exists."""
from datetime import date, timedelta
import hashlib
import json

from scripts import mn_short_release_gate as gate
from scripts.mn_short_channel_analytics import summarize_daily


def _fixture(tmp_path, monkeypatch):
    mp4 = tmp_path / "one_short.mp4"
    mp4.write_bytes(b"media" * 60000)
    payload = {
        "source": {
            "title": "A well attributed news story",
            "url": "https://example.com/news/article",
            "publisher": "Test Publisher",
        },
        "generated": {
            "title_es": "Una noticia concreta sobre la investigación",
            "script_es": " ".join(["La historia contiene contexto y detalles originales."] * 12),
            "visual_subjects": [
                {"name": "Jane Reporter", "kind": "person", "context": "investigation"}
            ],
        },
        "grid": {"slot": "10:00", "count": 1, "language": "es"}
    }
    (tmp_path / "editorial.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(gate, "_media_probe", lambda p: {
        "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920},
            {"codec_type": "audio", "sample_rate": "48000"},
        ],
        "format": {"duration": "34.1"},
    })
    return mp4, payload


def test_without_independent_sources_and_licensed_visuals_never_publish(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    outcome = gate.assess(tmp_path)
    assert outcome["approved"] is False
    assert any("VERIFICACION_FUENTES" in reason for reason in outcome["reasons"])
    assert any("ESCENAS_VERIFICADAS" in reason for reason in outcome["reasons"])


def test_verified_source_and_exact_final_movie_can_release(tmp_path, monkeypatch):
    movie, editorial = _fixture(tmp_path, monkeypatch)
    verification = {
        "claims_verified": True,
        "original_contribution_verified": True,
        "unresolved_claims": [],
        "source_article_url": editorial["source"]["url"],
        "independent_sources": [
            "https://independent-news.example.org/related-article"
        ],
    }
    scenes = {
        "rendered_mp4_sha256": hashlib.sha256(movie.read_bytes()).hexdigest(),
        "timecoded_alignment_verified": True,
        "scenes": [
            {
                "license_cleared": True,
                "source_page": "https://photo.example.org/jane-reporter",
                "named_subject": "Jane Reporter",
                "subject_identity_verified": True,
            },
            {
                "license_cleared": True,
                "source_page": "https://photo.example.org/licensed-building",
                "named_subject": "",
                "subject_identity_verified": True,
            },
        ],
    }
    (tmp_path / "VERIFICACION_FUENTES.json").write_text(json.dumps(verification), encoding="utf-8")
    (tmp_path / "ESCENAS_VERIFICADAS.json").write_text(json.dumps(scenes), encoding="utf-8")
    assert gate.assess(tmp_path)["approved"] is True
    scenes["rendered_mp4_sha256"] = "0" * 64
    (tmp_path / "ESCENAS_VERIFICADAS.json").write_text(json.dumps(scenes), encoding="utf-8")
    assert gate.assess(tmp_path)["approved"] is False


def test_cannot_replace_person_with_generic_place(tmp_path, monkeypatch):
    movie, editorial = _fixture(tmp_path, monkeypatch)
    (tmp_path / "VERIFICACION_FUENTES.json").write_text(json.dumps({
        "claims_verified": True,
        "original_contribution_verified": True,
        "unresolved_claims": [],
        "source_article_url": editorial["source"]["url"],
        "independent_sources": ["https://another.example.org/report"],
    }), encoding="utf-8")
    (tmp_path / "ESCENAS_VERIFICADAS.json").write_text(json.dumps({
        "rendered_mp4_sha256": hashlib.sha256(movie.read_bytes()).hexdigest(),
        "timecoded_alignment_verified": True,
        "scenes": [
            {"license_cleared": True, "source_page": "https://img.example.org/office",
             "named_subject": "Jane Reporter", "subject_identity_verified": False},
            {"license_cleared": True, "source_page": "https://img.example.org/office2",
             "named_subject": "", "subject_identity_verified": True},
        ],
    }), encoding="utf-8")
    outcome = gate.assess(tmp_path)
    assert outcome["approved"] is False
    assert any("protagonistas" in reason for reason in outcome["reasons"])


def test_revenue_unavailable_must_not_be_zero():
    end = date(2026, 11, 9)
    rows = [{"day": end.isoformat(), "views": 40, "estimatedRevenue": 1.25},
            {"day": (end - timedelta(days=1)).isoformat(), "views": 60,
             "estimatedRevenue": 0.75}]
    assert summarize_daily(rows, "views", 28, end) == 100
    assert summarize_daily(rows, "estimatedRevenue", 28, end) == 2.0
    assert summarize_daily([], "estimatedRevenue", 28, end) is None
