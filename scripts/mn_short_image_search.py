#!/usr/bin/env python3
"""Editorial image *discovery* from exact named subjects (review-only).

Requires the open-source 'ddgs' package. No API keys.
A search-result caption is not proof of the photo's identity or license.
Never silently substitute generic photos for a named subject.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse


def words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", normalized.lower())


def exact_subject_match(title: str, subject: str) -> bool:
    """Require full contiguous subject name, not only company/industry proximity."""
    needle, haystack = words(subject), words(title)
    return bool(needle and len(haystack) >= len(needle) and any(
        haystack[i:i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    ))


def valid_public_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not (
            parsed.hostname in {"localhost", "127.0.0.1"}
            or parsed.hostname.startswith("127.")
        )
    except ValueError:
        return False


def find_candidates(subject: str, context: str, limit: int = 12) -> list[dict]:
    from ddgs import DDGS

    # Filter by subject in the actual search result title. The image URL alone
    # is often generic; a company logo does not count as a person's portrait.
    query = f'"{subject}" {context} editorial portrait photo'
    with DDGS(timeout=15) as search:
        results = search.images(
            query=query, max_results=35, safesearch="moderate",
            backend="auto", type_image="photo",
        )
    selected, seen = [], set()
    for entry in results:
        title = str(entry.get("title") or "").strip()
        image = str(entry.get("image") or "")
        page = str(entry.get("url") or "")
        if not exact_subject_match(title, subject):
            continue
        if not (valid_public_url(image) and valid_public_url(page)):
            continue
        key = image.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append({
            "subject": subject,
            "title": title[:400],
            "image_url": image,
            "source_page": page,
            "source_search_engine": str(entry.get("source") or "unknown"),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "license": "UNVERIFIED",
            "identity": "CANDIDATE_NEEDS_SOURCE_VERIFICATION",
            "approved_for_publication": False,
        })
        if len(selected) >= limit:
            break
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True, help="Full person name, e.g. Jensen Huang")
    ap.add_argument("--context", default="", help="Company or event, e.g. Nvidia")
    ap.add_argument("--output", default="image-search-results")
    args = ap.parse_args()
    if len(args.subject.strip()) < 4 or len(args.subject) > 120:
        ap.error("Provide a full person name, maximum 120 characters")
    if len(args.context) > 160:
        ap.error("Context is too long")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    try:
        candidates = find_candidates(args.subject.strip(), args.context.strip())
        error = None
    except Exception as exc:
        candidates, error = [], f"{type(exc).__name__}: {str(exc)[:400]}"
    manifest = {
        "query_subject": args.subject, "context": args.context,
        "searched_at_utc": datetime.now(timezone.utc).isoformat(),
        "search_service": "DDGS (Bing/DuckDuckGo images)",
        "rights_policy": "Search results are NOT a reuse license. Check original source rights before downloads/publication.",
        "candidates": candidates,
        "error": error,
    }
    (out / "candidates.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"IMAGE RESEARCH: {args.subject} ({args.context})",
        f"Candidates: {len(candidates)}",
        "Candidates are NOT yet cleared for publication or independently identity-verified.",
        "",
    ]
    if error:
        lines += ["Search error: " + error]
    for index, item in enumerate(candidates, start=1):
        lines += [
            f"{index}. {item['title']}",
            f"    Source: {item['source_page']}",
            f"    Image: {item['image_url']}",
            "    Rights: UNVERIFIED — review before use",
            "",
        ]
    (out / "RESULTADOS.txt").write_text("\ufeff" + "\n".join(lines), encoding="utf-8")
    print(f"Search completed: {len(candidates)} exact-name photo candidates.")
    if error:
        raise SystemExit(f"Image search failed; details saved to RESULTS: {error}")


if __name__ == "__main__":
    main()
