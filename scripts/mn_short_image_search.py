#!/usr/bin/env python3
"""Dynamic editorial image discovery for the story selected by MN Short.

Reads the Gemini editorial JSON produced in the *same* GitHub Actions run.
Subjects are extracted from the current article; no fixed names or manual inputs.
Returns source-page and image URLs for review, never a grant of reuse rights.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


def words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", normalized.lower())


def exact_subject_match(title: str, subject: str) -> bool:
    """A full-name reference is required for portraits, not merely the employer."""
    needle, haystack = words(subject), words(title)
    return bool(needle and len(haystack) >= len(needle) and any(
        haystack[i:i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    ))


def valid_public_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and bool(hostname) and not (
            hostname == "localhost"
            or hostname.startswith(("127.", "10.", "192.168.", "169.254.", "172.16."))
        )
    except ValueError:
        return False


def editorial_subjects(editorial: dict) -> list[dict]:
    """Take only subjects grounded in the selected news source AND spoken script."""
    source = editorial.get("source") or {}
    generated = editorial.get("generated") or {}
    source_text = f"{source.get('title', '')} {source.get('description', '')}"
    scripts_text = f"{generated.get('script_es', '')} {generated.get('script_en', '')}"
    people_and_entities = generated.get("visual_subjects") or []
    selected, seen = [], set()
    if not isinstance(people_and_entities, list):
        people_and_entities = []
    for item in people_and_entities[:8]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        kind = str(item.get("kind") or "").strip().lower()
        context = str(item.get("context") or "").strip()
        if not (4 <= len(name) <= 100) or kind not in {"person", "organization", "place", "event"}:
            continue
        if not exact_subject_match(source_text, name):
            continue
        if not exact_subject_match(scripts_text, name):
            continue
        if kind == "place" and not exact_subject_match(source.get("title", ""), name):
            # 'Utah' alone is not evidence of the actual facility reported on.
            continue
        if kind == "person" and len(words(name)) < 2:
            # Single-word names are too ambiguous to select a real person's portrait.
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        selected.append({"name": name, "kind": kind, "context": context[:120]})
        if len(selected) == 5:
            break
    # On an unfamiliar story without a named subject we can still search its
    # exact news headline, but results are unverified and never treated as
    # portraits or approved video material.
    if not selected:
        headline = str(source.get("title") or "").strip()
        if headline:
            selected.append({
                "name": headline[:160],
                "kind": "event",
                "context": str(source.get("publisher") or "")[:120],
                "fallback": "No source-grounded and spoken named subject was found",
            })
    return selected


class ArticleImageParser(HTMLParser):
    """Extract an article's declared lead image, not its arbitrary inline graphics."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        props = {key.lower(): value for key, value in attrs if key and value}
        label = (props.get("property") or props.get("name") or "").lower()
        if label in {"og:image", "og:image:secure_url", "twitter:image"}:
            self.images.append((label, props.get("content", "")))


def article_lead_image(article_url: str) -> dict | None:
    """Check the RSS publisher's original article for its declared main image.

    This is a *candidate*, never automatic proof of what the photo depicts
    nor evidence that the publisher licenses it for reuse.
    """
    parsed = urlparse(article_url)
    host = (parsed.hostname or "").lower()
    trusted_hosts = {
        "techcrunch.com", "www.techcrunch.com",
        "arstechnica.com", "www.arstechnica.com",
        "theverge.com", "www.theverge.com",
    }
    if parsed.scheme != "https" or host not in trusted_hosts:
        return None
    request = Request(
        article_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MNShortEditorialResearch/0.2)",
            "Accept": "text/html",
        }
    )
    try:
        with urlopen(request, timeout=12) as response:
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                return None
            html = response.read(2_000_000).decode("utf-8", errors="replace")
    except (OSError, ValueError):
        return None
    parser = ArticleImageParser()
    parser.feed(html)
    for label, raw_url in parser.images:
        url = urljoin(article_url, raw_url)
        if valid_public_url(url):
            return {
                "kind": "article_image",
                "image_url": url,
                "source_page": article_url,
                "image_meta": label,
                "identity": "UNVERIFIED_SOURCE_ARTICLE_LEAD_IMAGE",
                "license": "UNVERIFIED",
                "approved_for_publication": False,
            }
    return None


def find_candidates(subject: str, context: str, kind: str = "person", limit: int = 6) -> list[dict]:
    from ddgs import DDGS

    # Prioritize the full subject, then try a cleaner query when the detailed
    # one produces no match. Do not accept generic stock as the named subject.
    if kind == "organization":
        queries = [
            f'"{subject}" geothermal power plant photo' if "geothermal" in context.lower() else f'"{subject}" {context} company photo',
            f'"{subject}" official facilities photo',
        ]
    elif kind == "person":
        queries = [f'"{subject}" {context} portrait photo', f'"{subject}" headshot photograph']
    elif kind == "event":
        queries = [f'"{subject}" {context} news photo']
    else:
        queries = [f'"{subject}" {context} photo']

    selected, seen = [], set()
    with DDGS(timeout=15) as search:
        for query in queries:
            # Bing/DuckDuckGo metadata can be noisy: an exact subject in the
            # page title is a minimum prerequisite, never a final identity check.
            results = search.images(
                query=query[:220], max_results=35, safesearch="moderate",
                backend="auto", type_image="photo",
            )
            for entry in results:
                title = str(entry.get("title") or "").strip()
                image = str(entry.get("image") or "")
                page = str(entry.get("url") or "")
                if kind in {"person", "organization", "place"} and not exact_subject_match(title, subject):
                    continue
                if kind == "event":
                    if len(set(words(title)).intersection(set(words(subject)))) < 2:
                        continue
                if not title or not (valid_public_url(image) and valid_public_url(page)):
                    continue
                key = image.lower()
                if key in seen:
                    continue
                seen.add(key)
                selected.append({
                    "subject": subject,
                    "kind": kind,
                    "search_query": query,
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
                    return selected
            if selected:
                break
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--editorial", default="mn_short_editorial.json",
                    help="News and Gemini scripts generated by this Actions run")
    ap.add_argument("--output", default="image-search-results")
    args = ap.parse_args()

    editorial = json.loads(Path(args.editorial).read_text(encoding="utf-8"))
    source = editorial.get("source") or {}
    subjects = editorial_subjects(editorial)
    lead_image = article_lead_image(str(source.get("url") or ""))
    searched = []
    for item in subjects:
        subject, kind, context = item["name"], item["kind"], item["context"]
        try:
            candidates = find_candidates(subject, context, kind)
            error = None
        except Exception as exc:
            candidates, error = [], f"{type(exc).__name__}: {str(exc)[:300]}"
        searched.append({**item, "candidates": candidates, "error": error})
        print(f"Editorial subject: {kind} {subject!r} — {len(candidates)} image candidates")

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_title": source.get("title"),
        "source_url": source.get("url"),
        "source_publisher": source.get("publisher"),
        "original_article_lead_image": lead_image,
        "searched_at_utc": datetime.now(timezone.utc).isoformat(),
        "search_service": "DDGS image search (Bing/DuckDuckGo)",
        "subject_detection": "Gemini from current article + narration; strict source/spoken grounding",
        "publication_policy": "Discovery only: original page, identity and licensing require verification",
        "subjects": searched,
    }
    (out / "visual_research.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "MN SHORT — BÚSQUEDA DINÁMICA DE IMÁGENES",
        "Noticia: " + str(source.get("title") or ""),
        "Fuente: " + str(source.get("url") or ""),
        "Protagonistas detectados automáticamente: " + str(len(subjects)),
        "ATENCIÓN: estas imágenes aún NO están verificadas ni autorizadas para publicación.",
        "Imagen principal declarada por artículo: " + (lead_image["image_url"] if lead_image else "No disponible"),
        "",
    ]
    for item in searched:
        lines += [f"{item['kind'].upper()}: {item['name']} ({item['context']})"]
        if item["error"]:
            lines += ["Error de búsqueda: " + item["error"]]
        for i, candidate in enumerate(item["candidates"], 1):
            lines += [
                f"  {i}. {candidate['title']}",
                f"     Foto: {candidate['image_url']}",
                f"     Página de origen: {candidate['source_page']}",
            ]
        lines += [""]
    (out / "RESULTADOS.txt").write_text("\ufeff" + "\n".join(lines), encoding="utf-8")
    print("Editorial image research saved; no images downloaded or published.")


if __name__ == "__main__":
    main()
