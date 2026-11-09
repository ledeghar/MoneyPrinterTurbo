#!/usr/bin/env python3
"""Upload ONE MN Short to YouTube directly (OAuth 2.0, unlisted, manual-only).

Secrets come from GitHub Actions, never from committed files or command-line flags.
An ambiguous upload result is not retried to avoid accidental duplicate videos.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_START_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing GitHub Actions secret {name}")
    return value


def get_access_token(session: requests.Session) -> str:
    response = session.post(
        TOKEN_URL,
        data={
            "client_id": require_env("YOUTUBE_CLIENT_ID"),
            "client_secret": require_env("YOUTUBE_CLIENT_SECRET"),
            "refresh_token": require_env("YOUTUBE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if response.status_code != 200:
        try:
            error = response.json().get("error", "unknown")
        except ValueError:
            error = "unknown"
        raise RuntimeError(
            f"YouTube OAuth token renewal failed (HTTP {response.status_code}; {error}). "
            "Refresh tokens for external apps in Testing can expire after 7 days."
        )
    token = response.json().get("access_token", "")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Google returned no access token")
    return token


def validate_upload_url(location: str) -> str:
    parsed = urlparse(location)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.googleapis.com"
        or not parsed.path.startswith("/upload/youtube/v3/videos")
    ):
        raise RuntimeError("Google returned an unexpected upload URL")
    return location


def upload_one_unlisted(
    session: requests.Session, path: Path, *, title: str, description: str
) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError("Rendered MP4 was not found or is empty")
    if not title or len(title) > 100:
        raise RuntimeError("YouTube title must be 1–100 characters")
    token = get_access_token(session)
    size = path.stat().st_size
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    start = session.post(
        UPLOAD_START_URL,
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        json=metadata,
        timeout=45,
        allow_redirects=False,
    )
    if start.status_code != 200:
        raise RuntimeError(f"YouTube could not start upload (HTTP {start.status_code})")
    location = validate_upload_url(start.headers.get("Location", ""))
    # No automatic retries on potentially successful remote uploads.
    with path.open("rb") as video:
        finished = session.put(
            location,
            data=video,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "video/mp4",
                "Content-Length": str(size),
            },
            timeout=600,
            allow_redirects=False,
        )
    if finished.status_code not in (200, 201):
        raise RuntimeError(
            f"YouTube upload not confirmed (HTTP {finished.status_code}); "
            "check YouTube Studio before retrying to avoid duplicates"
        )
    video_id = finished.json().get("id")
    if not isinstance(video_id, str) or not video_id:
        raise RuntimeError("YouTube returned no video ID; check Studio before retrying")
    return video_id


def main() -> None:
    if os.environ.get("MNSHORT_UPLOAD_UNLISTED", "").lower() != "true":
        raise SystemExit("Uploading disabled; requires explicit manual permission.")
    output = Path("mn-short-output")
    videos = list(output.glob("*_ES_*.mp4"))
    if len(videos) != 1:
        raise SystemExit(f"Expected exactly one Spanish MP4, found {len(videos)}")
    editorial = json.loads((output / "editorial.json").read_text(encoding="utf-8"))
    title = str(editorial["generated"]["title_es"]).strip()[:100]
    source = editorial["source"]
    description = (
        "MN Short — La tecnología detrás del titular.\n\n"
        f"Fuente: {source['publisher']} — {source['title']}\n{source['url']}\n\n"
        "Imágenes de archivo ilustrativas. Narración generada con IA. "
        "#MNShort #Tecnologia #Shorts"
    )
    with requests.Session() as session:
        video_id = upload_one_unlisted(
            session, videos[0], title=title, description=description
        )
    (output / "youtube-unlisted-test.json").write_text(
        json.dumps(
            {"video_id": video_id, "privacy_status": "unlisted", "source_file": videos[0].name},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"YouTube upload confirmed as UNLISTED: https://www.youtube.com/watch?v={video_id}")
    print("Verify that the destination channel is MN Short in YouTube Studio.")


if __name__ == "__main__":
    main()
