#!/usr/bin/env python3
"""Check Google OAuth refresh credentials without uploading any videos."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

names = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
missing = [name for name in names if not os.environ.get(name)]
if missing:
    sys.exit("Missing GitHub Secrets: " + ", ".join(missing))

payload = urlencode({
    "client_id": os.environ["YOUTUBE_CLIENT_ID"],
    "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
    "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
    "grant_type": "refresh_token",
}).encode()
req = Request(
    "https://oauth2.googleapis.com/token", payload,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    with urlopen(req, timeout=20) as response:
        data = json.load(response)
except HTTPError as exc:
    try:
        error = json.load(exc).get("error", "unknown")
    except (ValueError, OSError):
        error = "unknown"
    sys.exit(
        f"Google OAuth refresh failed: HTTP {exc.code} {error}. "
        "Refresh tokens can expire after 7 days while OAuth is in Testing."
    )
except URLError:
    sys.exit("Google OAuth service unavailable; retry after connectivity returns")

if not isinstance(data.get("access_token"), str) or not data["access_token"]:
    sys.exit("Google did not return an access token")
print("SUCCESS: Google OAuth refresh credentials are valid; NO YouTube upload attempted.")
print("Confirm destination channel later with a manually authorized unlisted upload.")
