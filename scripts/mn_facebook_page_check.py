#!/usr/bin/env python3
"""Read-only Facebook Page identity verification for DISI. No publishing."""
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GRAPH_BASE = "https://graph.facebook.com/v26.0"
DESTINATION = "https://www.facebook.com/medianewshq"


def verify_page(token: str, page_id: str, opener=urlopen) -> dict:
    if not token:
        raise ValueError("Missing FACEBOOK_PAGE_ACCESS_TOKEN secret")
    if not re.fullmatch(r"[0-9]{5,30}", page_id):
        raise ValueError("Set numeric FACEBOOK_PAGE_ID repository variable")
    request = Request(
        GRAPH_BASE + "/me?fields=id,name,link",
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
    )
    try:
        with opener(request, timeout=20) as response:
            data = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(
            "Meta returned HTTP %s; check token validity and Page permissions" % exc.code
        ) from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError("Meta API could not be reached") from None
    if not isinstance(data, dict) or "error" in data:
        raise RuntimeError("Meta did not return a valid Page identity")
    if str(data.get("id", "")) != page_id:
        raise RuntimeError("Page ID and Page token do not match; no action performed")
    if not data.get("name"):
        raise RuntimeError("Meta returned a Page ID but no Page name")
    return {
        "id": str(data["id"]),
        "name": str(data["name"]),
        "link": str(data.get("link") or ""),
    }


def main() -> int:
    try:
        page = verify_page(
            os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip(),
            os.getenv("FACEBOOK_PAGE_ID", "").strip(),
        )
    except (ValueError, RuntimeError) as exc:
        print("Facebook Page check FAILED:", exc, file=sys.stderr)
        return 1
    print("Meta Page token/ID verification: OK")
    print("Page name:", page["name"])
    print("Page ID:", page["id"])
    print("Page link:", page["link"])
    print("Expected destination:", DESTINATION)
    print("No video uploaded or published. Content creation rights not yet tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
