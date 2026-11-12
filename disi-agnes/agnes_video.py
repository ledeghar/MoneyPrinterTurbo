#!/usr/bin/env python3
"""DISI Agnes bridge: generate one optional AI video clip (never publish)."""
import argparse
import hashlib
import ipaddress
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MODEL = "agnes-video-2.5-flash"  # Free promotional model; never silently use paid models.
BASE_URL = "https://apihub.agnes-ai.com"
RETRY_STATUSES = {408, 429, 500, 502, 503, 504, 520, 522, 524}
MAX_DOWNLOAD = 700 * 1024 * 1024


def public_https(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Video URL must be public HTTPS")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("Refusing private video download")
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            raise ValueError("Refusing private video download")
    except ValueError as exc:
        if "Refusing" in str(exc):
            raise
    return url


def request_json(url, key, payload=None):
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    method = "GET"
    body = None
    if payload is not None:
        method = "POST"
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    for attempt in range(4):
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                result = json.load(response)
                if not isinstance(result, dict):
                    raise RuntimeError("Unexpected Agnes response")
                return result
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUSES or attempt == 3:
                raise RuntimeError("Agnes HTTP error " + str(error.code)) from None
            time.sleep(min(2 ** attempt * 5, 30))
    raise RuntimeError("Agnes request failed")


def extract_video_id(data):
    value = data.get("video_id") or data.get("id") or data.get("task_id")
    if not value and isinstance(data.get("data"), dict):
        value = data["data"].get("video_id") or data["data"].get("id")
    if not isinstance(value, (str, int)) or not str(value).strip():
        raise RuntimeError("Agnes did not return a video_id")
    return str(value)


def result_status(data):
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    nested_meta = nested.get("metadata") if isinstance(nested.get("metadata"), dict) else {}
    status = str(data.get("status") or nested.get("status") or "").lower()
    url = data.get("url") or nested.get("url") or metadata.get("url") or nested_meta.get("url")
    if data.get("error") or nested.get("error") or status in ("failed", "error", "cancelled"):
        raise RuntimeError("Agnes video generation failed (check upstream account or capacity)")
    return status, url


def download_video(url, output):
    public_https(url)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".part")
    try:
        # Do not send the Agnes credential to the media host.
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "DISI-Agnes/1.0"}), timeout=90) as source:
            with tmp.open("wb") as target:
                total = 0
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD:
                        raise RuntimeError("Agnes clip exceeded download size limit")
                    target.write(chunk)
        if tmp.stat().st_size < 1024:
            raise RuntimeError("Agnes returned an empty or invalid clip")
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)


def probe_media(output):
    if not shutil.which("ffprobe"):
        return {"media_probe": "not_installed"}
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-show_entries", "stream=codec_type,width,height", "-of", "json", str(output)],
        text=True, capture_output=True, check=True, timeout=30,
    )
    info = json.loads(result.stdout)
    video_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    if not video_streams:
        raise RuntimeError("Generated file has no video stream")
    stream = video_streams[0]
    return {"width": stream.get("width"), "height": stream.get("height"),
            "duration": info.get("format", {}).get("duration")}


def main():
    parser = argparse.ArgumentParser(description="DISI Agnes: standalone optional AI clip generator")
    parser.add_argument("--dry-run", action="store_true", help="Validate without credentials/network")
    parser.add_argument("--execute", action="store_true", help="Explicitly submit a video job")
    parser.add_argument("--seconds", type=int, default=5, choices=range(4, 13))
    parser.add_argument("--output-dir", default="disi-agnes-output")
    args = parser.parse_args()
    if args.dry_run == args.execute:
        parser.error("Choose exactly one of --dry-run or --execute")
    prompt = os.environ.get("VIDEO_PROMPT", "").strip()
    if not (12 <= len(prompt) <= 2000):
        parser.error("VIDEO_PROMPT must contain 12–2000 characters")
    payload = {"model": MODEL, "mode": "text", "prompt": prompt,
               "seconds": str(args.seconds), "size": "720P", "aspect_ratio": "9:16"}
    safe = {"model": MODEL, "mode": "text", "seconds": args.seconds,
            "aspect_ratio": "9:16", "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt_chars": len(prompt)}
    print(json.dumps({"disi_agnes": "configured", "request": safe, "dry_run": args.dry_run}))
    if args.dry_run:
        return
    key = os.environ.get("AGNES_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing AGNES_API_KEY secret: no generation submitted")
    # No submission for protected HUMINT, personally identifying material or
    # footage not cleared for transmission to a third-party cloud provider.
    result = request_json(BASE_URL + "/v1/videos", key, payload)
    video_id = extract_video_id(result)
    print("Agnes task accepted. Polling id prefix:", video_id[:6])
    query = urllib.parse.urlencode({"video_id": video_id, "model_name": MODEL})
    poll_url = BASE_URL + "/agnesapi?" + query
    deadline = time.monotonic() + 25 * 60
    media_url = None
    while time.monotonic() < deadline:
        status_data = request_json(poll_url, key)
        status, media_url = result_status(status_data)
        if status == "completed" and media_url:
            break
        if status == "completed" and not media_url:
            raise RuntimeError("Agnes completed but did not return a video URL")
        time.sleep(20)
    else:
        raise RuntimeError("Agnes task exceeded 25-minute polling window")
    stamp = time.strftime("%Y%m%d", time.gmtime())
    output = Path(args.output_dir) / ("DISI_Agnes_clip_" + stamp + "_" + video_id[:10] + ".mp4")
    download_video(media_url, output)
    metadata = {**safe, "task_id": video_id, "status": "completed",
                "asset_type": "AI_GENERATED_RECONSTRUCTION", "source": "Agnes AI",
                "file": str(output), "media": probe_media(output),
                "published": False, "ten_audio_tracks": False, "disi_outro": False}
    output.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"created": str(output), "media": metadata["media"], "published": False}))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, urllib.error.URLError, subprocess.CalledProcessError) as error:
        print("DISI Agnes error:", str(error), file=sys.stderr)
        sys.exit(1)
