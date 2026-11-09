#!/usr/bin/env python3
"""Opt-in public YouTube uploader for ONE produced editorial MN Short.

Scheduled publishing is disabled until BOTH the repository variable
MNSHORT_PUBLICATION_ENABLED and OAuth secrets are configured. Do not retry
an ambiguous YouTube API result: investigate Studio to avoid duplicates.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests

try:
    from .mn_short_youtube_direct import UPLOAD_START_URL, get_access_token, validate_upload_url
except ImportError:  # Direct invocation from GitHub Actions
    from mn_short_youtube_direct import UPLOAD_START_URL, get_access_token, validate_upload_url

CATEGORY_IDS = {
    "news": "25",
    "world": "25",
    "society": "25",
    "cinema": "24",
    "technology": "28",
    "gaming": "20",
}


def upload_one_public(path: Path, editorial: dict) -> str:
    if os.environ.get("MNSHORT_PUBLICATION_ENABLED", "").lower() != "true":
        raise RuntimeError("Public upload not enabled; refusing publication")
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError("MP4 missing or empty")
    if editorial["grid"].get("count") != 1 or editorial["grid"].get("language") != "es":
        raise RuntimeError("Unexpected editorial manifest: only one Spanish Short is allowed")
    source = editorial["source"]
    topic = editorial["grid"]["topic"]
    title = str(editorial["generated"]["title_es"]).strip()
    if not 1 <= len(title) <= 100:
        raise RuntimeError("Invalid YouTube title")
    description = (
        "MN Short — información de actualidad.\n\n"
        f"Fuente: {source['publisher']}.\n"
        f"Artículo original: {source['title']}\n"
        f"{source['url']}\n\n"
        "Locución generada con IA. Los planos de stock son ilustrativos y no "
        "representan necesariamente a las personas o instalaciones citadas.\n"
        "#MNShort #Shorts"
    )
    with requests.Session() as session:
        token = get_access_token(session)
        size = path.stat().st_size
        init = session.post(
            UPLOAD_START_URL,
            params={"uploadType": "resumable", "part": "snippet,status"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(size),
            },
            json={
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": CATEGORY_IDS[topic],
                    "defaultLanguage": "es",
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                    "containsSyntheticMedia": True,
                },
            },
            timeout=45,
            allow_redirects=False,
        )
        if init.status_code != 200:
            raise RuntimeError(f"YouTube declined upload initiation (HTTP {init.status_code})")
        upload_url = validate_upload_url(init.headers.get("Location", ""))
        with path.open("rb") as video:
            response = session.put(
                upload_url, data=video,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "video/mp4",
                    "Content-Length": str(size),
                },
                timeout=600,
                allow_redirects=False,
            )
        if response.status_code not in {200, 201}:
            raise RuntimeError(
                f"Upload result not confirmed (HTTP {response.status_code}). "
                "Check YouTube Studio before any manual retry."
            )
        data = response.json()
        video_id = data.get("id")
        if not video_id:
            raise RuntimeError("YouTube gave no video ID. Check Studio; do not retry blindly.")
        privacy = (data.get("status") or {}).get("privacyStatus", "unknown")
        OUTPUT = Path("mn-short-output")
        (OUTPUT / "YOUTUBE_PUBLICATION.json").write_text(
            json.dumps({
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "requested_privacy": "public",
                "reported_privacy": privacy,
                "slot": editorial["grid"]["slot"],
                "title": title,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"YouTube upload confirmed: video_id={video_id}, privacy={privacy}")
        return video_id


def main() -> None:
    folder = Path("mn-short-output")
    videos = list(folder.glob("*.mp4"))
    if len(videos) != 1:
        raise SystemExit(f"Exactly ONE MP4 per slot is required; found {len(videos)}")
    editorial = json.loads((folder / "editorial.json").read_text(encoding="utf-8"))
    upload_one_public(videos[0], editorial)


if __name__ == "__main__":
    main()
