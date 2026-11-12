#!/usr/bin/env python3
"""DISI Book Marketing: free editorial campaign planner and static landing site.

Produces local artefacts only. NEVER publishes on social media, deploys a site,
contacts viewers, fabricates sales metrics, or uses paid external APIs.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog.json"
CHANNELS = {
    "linkedin": {"format": "text", "time": "10:00", "tags": "#Lectura #Periodismo #Libros"},
    "facebook": {"format": "text", "time": "12:30", "tags": "#MediaNews #Libros"},
    "youtube": {"format": "video", "time": "12:00", "tags": "#Shorts #Libros"},
    "tiktok": {"format": "video", "time": "18:00", "tags": "#BookTok #Libros"},
    "instagram": {"format": "video", "time": "19:00", "tags": "#Libros #MediaNews"},
    "x": {"format": "text", "time": "12:00", "tags": "#Libros"},
    "pinterest": {"format": "graphic", "time": "17:00", "tags": "#Libros #Lectura"},
}
WEEK_PATTERN = {
    0: ("linkedin", "facebook"),
    2: ("youtube", "instagram", "tiktok"),
    4: ("x", "pinterest"),
}
STORE_HOSTS = {"www.amazon.es", "amazon.es", "www.lulu.com", "lulu.com"}
CSS = """
:root{color-scheme:dark;--navy:#051522;--blue:#123b5b;--red:#e83551;--muted:#b7cbdc;--white:#f4f8fc}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:var(--navy);color:var(--white);line-height:1.6}
a{color:inherit}a:focus-visible{outline:3px solid #8ce1ff;outline-offset:4px}
.container{max-width:1140px;margin:auto;padding:0 28px}
header{border-bottom:1px solid #31526e;background:#071b2e}
nav{min-height:82px;display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap}
.brand{font-weight:950;letter-spacing:2px;font-size:25px}.brand b{color:var(--red)}
.byline{font-size:13px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase}
.hero{padding:96px 0 72px;background:radial-gradient(circle at 85% 18%,#194563,transparent 50%),var(--navy)}
.eyebrow{color:#f48b9c;font-weight:800;text-transform:uppercase;letter-spacing:3px;font-size:13px}
h1{font-family:Georgia,serif;font-size:clamp(48px,7vw,90px);line-height:1.06;max-width:880px;letter-spacing:-1.7px;margin:14px 0 28px}
h2{font-family:Georgia,serif;font-weight:800;font-size:clamp(30px,4vw,52px);line-height:1.16;margin:0 0 20px}
.lead{max-width:770px;color:var(--muted);font-size:clamp(17px,2vw,21px)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px;margin:26px 0 90px}
.book{background:linear-gradient(135deg,#12334e,#071c30);border:1px solid #33536d;border-radius:20px;overflow:hidden;box-shadow:0 16px 45px #0004}
.cover{min-height:290px;padding:32px;display:flex;flex-direction:column;justify-content:space-between;background:radial-gradient(circle at 70% 60%,#2a4961,transparent 62%),linear-gradient(125deg,#122e44,#07121e);border-bottom:4px solid var(--red)}
.cover .mark{font-weight:800;font-size:13px;letter-spacing:3px;color:#acd4e8}
.cover .booktitle{font-family:Georgia,serif;font-size:clamp(56px,7vw,78px);font-weight:800;line-height:1}
.cover .subtitle{font-size:20px;line-height:1.35;max-width:340px}
.cover small{color:#dbe6ee}.details{padding:32px}
.details p{color:#c9d9e4;max-width:520px}.meta{font-size:13px;color:#aac0d2}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}
.action{display:inline-flex;align-items:center;min-height:50px;padding:12px 20px;border-radius:9px;text-decoration:none;font-weight:800;background:var(--red);color:white}
.action.secondary{background:#1e4c6d}.action:hover{filter:brightness(1.12)}
.notice{font-size:13px;color:#a8c0d0}.about{border-top:1px solid #31516a;padding:54px 0 80px}.about p{max-width:780px;color:var(--muted)}
footer{background:#020d16;padding:25px 0;border-top:1px solid #233d52;color:#acbdca;font-size:13px}
@media(max-width:760px){.grid{grid-template-columns:1fr}.hero{padding:60px 0}.cover{min-height:260px}nav{padding:18px 0}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def load_catalog(path: Path = CATALOG) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    books = data.get("books")
    if not isinstance(books, list) or {b.get("slug") for b in books} != {"alepo", "jartum"}:
        raise ValueError("Expected exactly ALEPO and JARTUM")
    for book in books:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", book["slug"]):
            raise ValueError("Unsafe book slug")
        if len(book.get("themes", [])) < 3:
            raise ValueError("Book requires at least 3 factual promotional themes")
        for edition in book["edition_ids"]:
            if not re.fullmatch(r"\d{13}", edition["isbn13"]):
                raise ValueError("Invalid ISBN format")
        for link in book["purchase_links"]:
            parsed = urlparse(link["url"])
            if parsed.scheme != "https" or parsed.hostname not in STORE_HOSTS or parsed.username or parsed.password:
                raise ValueError("Only known HTTPS book stores are allowed")
            if link["link_check"] not in ("PUBLIC_PAGE_CONFIRMED", "PENDING_LIVE_CHECK"):
                raise ValueError("Explicit sale link verification state required")
    return data


def start_monday(today: date) -> date:
    return today + timedelta(days=(-today.weekday()) % 7)


def campaign_url(destination: str, channel: str, book: str, slot: str) -> str:
    parsed = urlparse(destination)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Campaign URL must be HTTPS")
    old = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
           if not k.startswith("utm_")]
    query = old + [("utm_source", channel), ("utm_medium", "social"),
                   ("utm_campaign", "disi_books_2026"), ("utm_content", book + "_" + slot)]
    return urlunparse(parsed._replace(query=urlencode(query)))


def copy_for(channel: str, book: dict, theme: dict, url: str) -> str:
    title = book["title"] + ": " + book["subtitle"]
    text = theme["hook"] + ". " + theme["angle"]
    if channel == "x":
        # Never truncate or shorten the link: only the prose can be shortened.
        suffix = "\n" + url + " #Libros"
        limit = 280 - len(suffix)
        if limit < 25:
            raise ValueError("Sales URL too long for X copy")
        return text[:limit].rstrip(" .,") + suffix
    return (text + "\n\n" + title + " — Juan Manuel Ledesma."
            + "\n" + url + "\n" + CHANNELS[channel]["tags"])


def plan_campaigns(data: dict, start: date, landing_url: str = "") -> list[dict]:
    if start.weekday() != 0:
        raise ValueError("start must be a Monday")
    if landing_url:
        p = urlparse(landing_url)
        if p.scheme != "https" or not p.hostname or p.username or p.password:
            raise ValueError("Landing URL must be an absolute HTTPS URL")
    books = data["books"]
    entries = []
    for week in range(4):
        for day_no, platforms in WEEK_PATTERN.items():
            day = start + timedelta(days=week * 7 + day_no)
            slot = f"w{week + 1}-{day_no}"
            # Rotate both books and topics; no daily repeated blast.
            book = books[(week * 3 + day_no // 2) % len(books)]
            theme = book["themes"][(week + day_no // 2) % len(book["themes"])]
            preferred = book["purchase_links"][0]
            for channel in platforms:
                fmt = CHANNELS[channel]["format"]
                if landing_url:
                    target = campaign_url(landing_url, channel, book["slug"], slot)
                    link_status = "LANDING_URL_SUPPLIED_NOT_DEPLOYMENT_VERIFIED"
                else:
                    target = preferred["url"]
                    link_status = preferred["link_check"]
                entries.append({
                    "id": f"{day.isoformat()}-{book['slug']}-{channel}",
                    "date_local": day.isoformat(), "time_local": CHANNELS[channel]["time"],
                    "timezone": "Europe/Madrid", "book": book["slug"],
                    "platform": channel, "format": fmt,
                    "title": book["title"] + ": " + book["subtitle"],
                    "hook": theme["hook"], "copy_es": copy_for(channel, book, theme, target),
                    "destination_url": target, "link_status": link_status,
                    "media_requirement": (
                        "DISIV9Approved: original Canva logos + V6 outro; 10 real voice tracks, "
                        "10 synced subtitles, exact 10-language master, editor-approved"
                        if fmt == "video" else
                        "Original rights-cleared graphic required" if fmt == "graphic" else "None"
                    ),
                    "publication_enabled": False, "editorial_approved": False,
                    "status": "DRAFT_REVIEW_ONLY",
                    "views": None, "clicks": None, "sales": None, "revenue_eur": None,
                })
    return entries


def site(data: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    blocks = []
    for book in data["books"]:
        name = escape(book["title"])
        subtitle = escape(book["subtitle"])
        description = escape(book["description"])
        isbn = ", ".join(escape(e["vendor"] + " ISBN " + e["isbn13"]) for e in book["edition_ids"])
        actions = "".join(
            '<a class="action' + (" secondary" if i else "") + '" href="' +
            escape(link["url"], quote=True) + '" target="_blank" rel="noopener noreferrer">' +
            escape(link["label"]) + '</a>'
            for i, link in enumerate(book["purchase_links"])
        )
        blocks.append(
            '<article class="book" id="' + escape(book["slug"]) + '">'
            '<div class="cover" aria-label="Identidad tipográfica del libro, no portada original">'
            '<span class="mark">JUAN MANUEL LEDESMA</span>'
            '<div><div class="booktitle">' + name + '</div><div class="subtitle">' + subtitle +
            '</div></div><small>MEDIA NEWS / LIBROS</small></div>'
            '<div class="details"><h2>' + name + '</h2><p>' + description + '</p>'
            '<p class="meta">Ediciones: ' + isbn + '</p><div class="actions">' + actions +
            '</div></div></article>'
        )
    page = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="description" content="ALEPO y JARTUM, libros de Juan Manuel Ledesma, publicados por el autor.">'
        '<meta name="theme-color" content="#051522">'
        '<title>' + escape(data["site_title"]) + '</title><link rel="stylesheet" href="styles.css">'
        '</head><body><header><div class="container"><nav>'
        '<div class="brand">MEDIA NEWS <b>/ DISI</b></div>'
        '<div class="byline">Libros · Juan Manuel Ledesma</div></nav></div></header>'
        '<main><section class="hero"><div class="container">'
        '<div class="eyebrow">Crónicas y relatos de conflictos reales</div>'
        '<h1>Las historias que quedan detrás de los titulares.</h1>'
        '<p class="lead">Dos libros de Juan Manuel Ledesma sobre las personas atrapadas en la guerra. '
        'ALEPO y JARTUM: literatura y testimonio con una mirada humana.</p>'
        '</div></section><section class="container" aria-label="Catálogo de libros">'
        '<div class="grid">' + "".join(blocks) + '</div></section>'
        '<section class="about"><div class="container"><h2>Sobre el autor</h2>'
        '<p>Juan Manuel Ledesma es periodista y fotógrafo. '
        'Sus obras abordan conflictos y situaciones extremas desde una perspectiva humana.</p>'
        '<p class="notice">Los enlaces conducen a librerías externas. '
        'Los precios y la disponibilidad se consultan directamente con cada librería.</p>'
        '</div></section></main><footer><div class="container">'
        '© 2026 Media News · Proyecto editorial by DISI. Sin seguimiento publicitario ni cookies.'
        '</div></footer></body></html>'
    )
    (directory / "index.html").write_text(page, encoding="utf-8")
    (directory / "styles.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (directory / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="ascii")
    (directory / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  X-Frame-Options: DENY\n  Content-Security-Policy: default-src 'none'; "
        "style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; "
        "frame-ancestors 'none'; upgrade-insecure-requests\n", encoding="utf-8")


def export(entries: list[dict], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "disi-book-marketing/0.1",
        "scope": "DRAFT_ONLY_NO_PUBLISHING", "autopublish": False,
        "total_drafts": len(entries), "sale_metrics": "UNKNOWN_NOT_ZERO",
        "posts": entries,
    }
    (directory / "campaigns.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (directory / "campaign-calendar.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["date_local", "time_local", "timezone", "book", "platform", "format",
                  "status", "link_status", "destination_url", "copy_es", "media_requirement"]
        w = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(entries)
    text = ["DISI BOOK MARKETING — 28 DÍAS DE BORRADORES", "",
            "Estado: SIN PUBLICAR. Requiere control editorial, enlaces y derechos.",
            "Vídeos: DISI V9 original con 10 voces, 10 subtítulos y cierre V6.",
            "Métricas de ventas/ingresos: DESCONOCIDAS, nunca estimadas.", ""]
    for p in entries:
        text.append(p["date_local"] + " " + p["time_local"] + " Madrid | "
                    + p["platform"].upper() + " | " + p["title"])
        text.append(p["copy_es"])
        text.append("Estado: " + p["status"])
        text.append("")
    (directory / "copy-to-review.txt").write_text("\n".join(text), encoding="utf-8")


def run(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=CATALOG)
    p.add_argument("--site-dir", type=Path, default=ROOT / "output" / "site")
    p.add_argument("--campaign-dir", type=Path, default=ROOT / "output" / "campaigns")
    p.add_argument("--start", help="Monday YYYY-MM-DD; defaults to next Monday")
    p.add_argument("--landing-url", default="", help="Real HTTPS site address, only after deploy")
    args = p.parse_args(argv)
    data = load_catalog(args.catalog)
    start = date.fromisoformat(args.start) if args.start else start_monday(date.today())
    entries = plan_campaigns(data, start, args.landing_url)
    site(data, args.site_dir)
    export(entries, args.campaign_dir)
    print(json.dumps({"status": "DRAFT_ONLY", "site": str(args.site_dir),
                      "campaigns": len(entries), "next_start": start.isoformat(),
                      "publish": False}, ensure_ascii=False))


if __name__ == "__main__":
    run()
