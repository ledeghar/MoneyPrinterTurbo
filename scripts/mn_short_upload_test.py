#!/usr/bin/env python3
"""Manual, unlisted MN Short upload test using the existing Upload-Post connection.

Does not authorize a new YouTube account and never uploads two videos together.
The caller must explicitly choose upload_unlisted=true at workflow_dispatch.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from app.services.upload_post import UploadPostService


def main():
    key = os.environ.get("UPLOAD_POST_API_KEY", "").strip()
    if not key:
        raise SystemExit("UPLOAD_POST_API_KEY secret is absent; refusing to upload")
    profile = os.environ.get("UPLOAD_POST_PROFILE", "Medianews").strip()
    if not profile:
        raise SystemExit("Upload-Post profile is empty")
    videos = list(Path("mn-short-output").glob("*_ES_*.mp4"))
    if len(videos) != 1:
        raise SystemExit(f"Expected one Spanish video for the test, found {len(videos)}")
    editorial = json.loads(Path("mn-short-output/editorial.json").read_text(encoding="utf-8"))
    generated = editorial["generated"]
    source = editorial["source"]
    title = generated["title_es"][:90].strip()
    if not title:
        raise SystemExit("Missing Spanish title; refusing to upload")

    # Do not automatically mark a video as public. This uses the user's existing
    # Upload-Post profile that is already connected to their MN Short channel.
    desc = (
        "MN Short — Tecnología detrás del titular.\n\n"
        f"Fuente informativa: {source['publisher']}\n{source['url']}\n"
        "Imágenes de archivo ilustrativas. #MNShort #Tecnologia #Shorts"
    )
    service = UploadPostService({
        "upload_post_enabled": True,
        "upload_post_api_key": key,
        "upload_post_username": profile,
    })
    result = service.upload_video(
        video_path=str(videos[0]),
        title=title,
        platforms=["youtube"],
        youtube_extra={
            "youtube_title": title,
            "youtube_description": desc,
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False,
        },
    )
    # Do not log tokens, headers or account data. GitHub Actions will
    # preserve the success/failure details in its job logs.
    if not result.get("success"):
        error = result.get("error") or result.get("message") or "unknown error"
        print("Upload-Post unlisted YouTube test failed:", error)
        if "request_id" in result:
            print("Request ID (inspect in Upload-Post before retry):", result["request_id"])
        raise SystemExit(1)
    print("Upload-Post confirmed unlisted YouTube upload:", result.get("request_id", "success"))
    for p, entry in (result.get("results") or {}).items():
        if p == "youtube" and isinstance(entry, dict):
            print("YouTube URL:", entry.get("url", "(available in Upload-Post dashboard)"))


if __name__ == "__main__":
    main()
