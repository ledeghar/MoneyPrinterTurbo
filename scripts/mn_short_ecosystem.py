#!/usr/bin/env python3
"""MN Short editorial scheduler and single-Short cloud-production bridge.

This orchestrates the existing, proven components:
  RSS -> Gemini scripts -> source-specific image research -> MoneyPrinterTurbo
  -> one Spanish MP4 -> YouTube OAuth (separate opt-in step).
No laptop, permanent server, or copied third-party repos are required.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

try:
    from .mn_short_cloud import generate_scripts, prepare_narration, request_bytes, strip_tags
except ImportError:  # Direct invocation: python scripts/mn_short_ecosystem.py
    from mn_short_cloud import generate_scripts, prepare_narration, request_bytes, strip_tags

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "mn_short_grid.json"
HISTORY_PATH = Path("mnshort-history.json")
EDITORIAL_PATH = Path("mn_short_editorial.json")
TASKS_PATH = Path("mn_short_tasks.json")
OUTPUT_PATH = Path("mn-short-output")
MAX_STORY_AGE_HOURS = 36
HISTORY_DAYS = 30

SCHEDULE_CRONS = {
    "0 8 * * *": "08:00",
    "0 10 * * *": "10:00",
    "0 12 * * *": "12:00",
    "0 16 * * *": "16:00",
    "0 18 * * *": "18:00",
    "0 20 * * *": "20:00",
}


def config() -> dict:
    result = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert result["timezone"] == "Europe/Madrid"
    assert result["language"] == "es" and result["video_count_per_slot"] == 1
    return result


def resolved_slot(raw_slot: str = "", scheduled_cron: str = "") -> str:
    slots = [item["time"] for item in config()["windows"]]
    if scheduled_cron:
        if scheduled_cron not in SCHEDULE_CRONS:
            raise ValueError("Unrecognized scheduled cron; refusing to produce a mislabeled Short")
        return SCHEDULE_CRONS[scheduled_cron]
    if raw_slot in slots:
        return raw_slot
    raise ValueError("A valid 08:00/10:00/12:00/16:00/18:00/20:00 slot is required")


def resolved_topic(slot: str, local_date=None) -> str:
    lookup = {item["time"]: item["topic"] for item in config()["windows"]}
    topic = lookup[slot]
    if topic == "technology_or_gaming":
        today = local_date or datetime.now(ZoneInfo("Europe/Madrid")).date()
        return "gaming" if today.toordinal() % 2 else "technology"
    return topic


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                       parts.path.rstrip("/"), "", ""))


def story_identifier(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()


def title_signature(title: str) -> str:
    """Simple cross-publisher overlap guard, ignoring punctuation/case."""
    title = re.sub(r"[^a-z0-9 ]", " ", title.casefold())
    words = [word for word in title.split() if len(word) > 3]
    return " ".join(words[:9])


def read_history() -> dict:
    if not HISTORY_PATH.exists():
        # Fail closed: absent state risks duplicate uploads after restart.
        raise RuntimeError("Missing persistent editorial history: restore the mnshort-history branch")
    ledger = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict) or not isinstance(ledger.get("items"), list):
        raise ValueError("Invalid history ledger")
    return ledger


def existing_keys(ledger: dict) -> tuple[set[str], set[str]]:
    ids = set()
    signatures = set()
    threshold = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    for item in ledger["items"]:
        try:
            stamp = datetime.fromisoformat(item["created_at"])
            if stamp.tzinfo is None or stamp < threshold:
                continue
            ids.add(item["source_id"])
            signatures.add(item["title_signature"])
        except (KeyError, TypeError, ValueError):
            continue
    return ids, signatures


def entry_text(entry, tags: tuple[str, ...]) -> str:
    for tag in tags:
        node = entry.find(tag)
        if node is not None:
            if tag.endswith("link"):
                return node.get("href") or (node.text or "")
            return "".join(node.itertext()) if tag == "description" else node.text or ""
    return ""


def parse_feed(xml_bytes: bytes, publisher: str, category: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    records = root.findall(".//item")
    if not records:
        records = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    current = datetime.now(timezone.utc)
    result = []
    for item in records[:35]:
        title = strip_tags(entry_text(item, ("title", "{http://www.w3.org/2005/Atom}title")))
        description = strip_tags(entry_text(item, (
            "description", "{http://www.w3.org/2005/Atom}summary",
            "{http://www.w3.org/2005/Atom}content",
            "{http://purl.org/rss/1.0/modules/content/}encoded",
        )))
        url = entry_text(item, ("link", "{http://www.w3.org/2005/Atom}link")).strip()
        date_str = entry_text(item, (
            "pubDate", "{http://www.w3.org/2005/Atom}published",
            "{http://www.w3.org/2005/Atom}updated",
            "{http://purl.org/dc/elements/1.1/}date",
        )).strip()
        try:
            published = parsedate_to_datetime(date_str)
        except (TypeError, ValueError, IndexError):
            try:
                published = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age = current - published.astimezone(timezone.utc)
        if not timedelta(0) <= age <= timedelta(hours=MAX_STORY_AGE_HOURS):
            continue
        if not (len(title) >= 18 and len(description) >= 70 and url.startswith("https://")):
            continue
        if re.search(r"\b(opinion|reviews?|best deals?|sponsored|newsletter)\b", title, re.I):
            continue
        result.append({
            "title": title, "description": description, "url": normalize_url(url),
            "publisher": publisher, "published_utc": published.isoformat(),
            "category": category,
        })
    return result


def choose_story(topic: str, ledger: dict) -> dict:
    feeds = config()["feeds"][topic]
    seen_ids, seen_titles = existing_keys(ledger)
    candidates = []
    problems = []
    for feed in feeds:
        try:
            records = parse_feed(request_bytes(feed["url"]), feed["publisher"], topic)
            for story in records:
                if story_identifier(story["url"]) not in seen_ids and title_signature(story["title"]) not in seen_titles:
                    candidates.append(story)
        except (OSError, ET.ParseError, UnicodeError, ValueError) as exc:
            problems.append(f"{feed['publisher']}: {type(exc).__name__}")
    if not candidates:
        raise RuntimeError(
            f"No fresh, distinct and adequately described {topic!r} article available; "
            f"refusing generic/mislabeled output. Unavailable feeds: {problems}"
        )
    # Prefer fresh substantiated material, not simply first response from an RSS URL.
    candidates.sort(
        key=lambda x: (datetime.fromisoformat(x["published_utc"]), len(x["description"])),
        reverse=True,
    )
    return candidates[0]


def prepare(slot: str, topic: str) -> None:
    ledger = read_history()
    source = choose_story(topic, ledger)
    scripts = generate_scripts(source)
    # Reuse the same narration + cloud renderer as the successful ES/EN pilot.
    one_task = {
        "video_subject": scripts["title_es"],
        "video_script": prepare_narration(scripts["script_es"], "es"),
        "video_terms": scripts["terms_es"][:8],
        "video_language": "es-ES",
        "video_aspect": "9:16",
        "video_source": "pexels",
        "match_materials_to_script": True,
        "video_clip_duration": 3,
        "video_count": 1,
        "voice_name": "es-ES-AlvaroNeural",
        "voice_volume": 1.25,
        "voice_rate": 0.96,
        "bgm_type": "random",
        "bgm_volume": 0.27,
        "subtitle_enabled": True,
        "subtitle_display_mode": "word_by_word",
        "subtitle_position": "two_thirds_bottom",
        "font_name": "MicrosoftYaHeiBold.ttc",
        "font_size": 72,
        "stroke_width": 2,
        "n_threads": 2,
    }
    TASKS_PATH.write_text(json.dumps([one_task], ensure_ascii=False, indent=2), encoding="utf-8")
    editorial = {
        "source": source,
        "generated": scripts,
        "grid": {
            "slot": slot, "topic": topic, "timezone": "Europe/Madrid",
            "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
            "language": "es",
            "count": 1,
        },
    }
    EDITORIAL_PATH.write_text(json.dumps(editorial, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MN SHORT [{slot}] [{topic}]: {source['publisher']} — {source['title']}")
    print("Exactly ONE Spanish video task prepared; publication remains independently gated.")


def slug(text: str, limit: int = 65) -> str:
    import unicodedata
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", ascii_text).strip("_")[:limit] or "noticia"


def package() -> None:
    editorial = json.loads(EDITORIAL_PATH.read_text(encoding="utf-8"))
    files = sorted(Path("storage/tasks").glob("*/final-1.mp4"))
    if len(files) != 1:
        raise RuntimeError(f"Expected exactly one completed MP4, got {len(files)}")
    if not files[0].stat().st_size:
        raise RuntimeError("Rendered MP4 is empty")
    source, grid, generated = (editorial[k] for k in ("source", "grid", "generated"))
    OUT = OUTPUT_PATH
    OUT.mkdir(exist_ok=True)
    today = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
    filename = f"{today}_{grid['slot'].replace(':','')}_{grid['topic']}_{slug(generated['title_es'])}.mp4"
    shutil.move(str(files[0]), str(OUT / filename))
    (OUT / "TITULO_Y_FUENTE.txt").write_text(
        "\ufeff" + "\n".join([
            f"MN SHORT | {today} | {grid['slot']} (Madrid)",
            f"Tema: {grid['topic']}",
            f"Título: {generated['title_es']}",
            f"Archivo: {filename}",
            f"Fuente: {source['publisher']}",
            f"Artículo: {source['title']}",
            f"URL: {source['url']}",
            "",
            generated["script_es"],
            "",
            "Las fotografías investigadas todavía NO están aprobadas automáticamente para montaje.",
        ]), encoding="utf-8",
    )
    (OUT / "editorial.json").write_text(json.dumps(editorial, ensure_ascii=False, indent=2), encoding="utf-8")
    research = Path("image-search-results")
    if research.is_dir():
        shutil.copytree(research, OUT / "BUSQUEDA_VISUAL", dirs_exist_ok=True)
    ledger = read_history()
    now = datetime.now(timezone.utc)
    record = {
        "source_id": story_identifier(source["url"]),
        "title_signature": title_signature(source["title"]),
        "created_at": now.isoformat(),
        "slot": grid["slot"], "topic": grid["topic"],
        "title": source["title"],
        "status": "produced",
    }
    ledger["items"] = [
        item for item in ledger["items"]
        if isinstance(item, dict) and item.get("created_at", "") >=
        (now - timedelta(days=HISTORY_DAYS)).isoformat()
    ]
    ledger["items"].append(record)
    HISTORY_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as out:
            out.write(f"artifact_name=MNShort_{today}_{grid['slot'].replace(':','')}_{slug(generated['title_es'],45)}\n")
    print(f"Packaged one Short: {OUT / filename}")
    print("Recorded production in persistent history; not uploaded to any social platform.")


def main():
    parser = argparse.ArgumentParser(description="MN Short scheduled editorial cloud system")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--slot", default="")
    prep.add_argument("--cron", default="")
    sub.add_parser("package")
    args = parser.parse_args()
    if args.command == "prepare":
        slot = resolved_slot(args.slot, args.cron)
        prepare(slot, resolved_topic(slot))
    elif args.command == "package":
        package()


if __name__ == "__main__":
    main()
