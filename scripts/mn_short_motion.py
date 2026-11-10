#!/usr/bin/env python3
"""Create ten-language news motion-graphics props and synchronized TTS clips.

Modes:
  demo — an explicitly labelled demonstration, without Gemini credentials;
  live — use the SAME latest editorial JSON as MN Short's RSS/Gemini flow.

All photos must come with a supported Wikimedia Commons license AND an exact
subject-name match in Commons metadata. Failure uses a named text card instead
of a photo of an unrelated person. Discovery is not visual identity verification.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MOTION = ROOT / "mn-short-motion"
PUBLIC = MOTION / "public"
PROPS = MOTION / "props"
OUTPUT = ROOT / "mn-short-output-motion"
FPS = 30
USER_AGENT = "MNShortEditorial/0.3 (Wikimedia Commons credited photo research; https://github.com/ledeghar/MoneyPrinterTurbo)"


def tokens(value):
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", normalized)


def named(text, name):
    needle, words = tokens(name), tokens(text)
    return len(needle) >= 2 and any(words[i:i + len(needle)] == needle for i in range(len(words) - len(needle) + 1))


def clean_html(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value or "")).split())[:200]


def demo_editorial():
    source = {
        "title": "Cómo se construye un vídeo informativo verificable",
        "description": "Demostración de producción: identidades, fuentes y licencias; no es una noticia de actualidad.",
        "url": "https://github.com/ledeghar/MoneyPrinterTurbo",
        "publisher": "Media News · Demostración",
        "published_utc": datetime.now(timezone.utc).isoformat(),
    }
    es = [
        "Así puede verse una noticia explicada con imágenes, cifras y titulares sincronizados.",
        "Por ejemplo, Jensen Huang debe aparecer identificado por su nombre, no con cualquier ejecutivo.",
        "Primero comprobamos la fuente original y distinguimos hechos de informaciones atribuidas.",
        "Tres controles importan: identidad, procedencia y derechos de la fotografía.",
        "Si una imagen no está autorizada, mostramos el nombre sin inventar un retrato.",
        "Las localizaciones necesitan mapas reales; esto es solamente un diagrama de contexto.",
        "Cada frase tiene su propia pantalla y su propia locución.",
        "Esto es MN Short.",
    ]
    en = [
        "This is how we can explain a story using animated images, figures and headlines.",
        "For example, Jensen Huang must be identified by name, not replaced by a random executive.",
        "We start by checking the original source and distinguishing documented facts from attributed claims.",
        "Three checks matter: identity, origin and the right to reuse a photograph.",
        "If a picture is not cleared for use, we show the name, not a fabricated portrait.",
        "Real locations need accurate maps. What you see here is only a context diagram.",
        "Every sentence gets its own screen, perfectly timed to the narration.",
        "This is MN Short.",
    ]
    return {"source": source, "generated": {
        "title_es": "Cómo se produce MN Short: noticia visual",
        "title_en": "How MN Short builds visual news",
        "script_es": " ".join(es), "script_en": " ".join(en),
        "visual_subjects": [{"name": "Jensen Huang", "kind": "person", "context": "Nvidia"}],
        "demo_sentences_es": es, "demo_sentences_en": en,
    }}


def split_sentences(script):
    # Gemini's editorial scripts are prompted to use short full sentences.
    text = " ".join(str(script).strip().split())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ0-9])", text) if s.strip()]


def wiki_json(endpoint, params, timeout=20):
    """Query Wikimedia APIs with a declared identity and conservative timeout."""
    url = endpoint + "?" + urlencode(params)
    request = Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def wikidata_identity_photo(name):
    """Look up Wikidata's curated P18 portrait of the EXACT named person.

    P18 establishes a strongly identified source file. Commons must STILL
    confirm the photo's reuse license, author and original source page.
    """
    try:
        found = wiki_json("https://www.wikidata.org/w/api.php", {
            "action": "wbsearchentities", "format": "json",
            "search": name, "language": "en", "limit": 8, "type": "item",
        })
        for entity in found.get("search") or []:
            aliases = [entity.get("label", "")] + [
                a for a in (entity.get("aliases") or [])
                if isinstance(a, str)
            ]
            if not any(tokens(alias) == tokens(name) for alias in aliases):
                continue
            qid = entity.get("id", "")
            if not re.fullmatch(r"Q[1-9]\d*", qid):
                continue
            record = wiki_json("https://www.wikidata.org/w/api.php", {
                "action": "wbgetentities", "format": "json", "ids": qid,
                "props": "claims", "languages": "en",
            })
            claims = (
                (record.get("entities") or {}).get(qid, {}).get("claims") or {}
            )
            for statement in claims.get("P18") or []:
                filename = (
                    statement.get("mainsnak", {}).get("datavalue", {}).get("value")
                )
                if isinstance(filename, str) and re.search(r"\.(jpe?g|png)$", filename, re.I):
                    print("Identity source: Wikidata", qid, "P18", filename)
                    return "File:" + filename
    except (OSError, ValueError, TypeError) as exc:
        print("Wikidata P18 unavailable:", type(exc).__name__, str(exc)[:140])
    return None


def checked_commons_file(page, person, confirmed_by_wikidata=False):
    """Validate one individual Commons file against whitelist and attribution."""
    title = str(page.get("title") or "").removeprefix("File:")
    if not (confirmed_by_wikidata or named(title, person)):
        return None
    entries = page.get("imageinfo") or []
    if not entries:
        return None
    info = entries[0]
    meta = info.get("extmetadata") or {}
    license_name = clean_html(
        (meta.get("LicenseShortName") or {}).get("value") or ""
    )
    norm = re.sub(r"[\s_-]+", " ", license_name).strip().upper()
    permitted = (
        norm in {"CC0", "CC0 1.0", "PUBLIC DOMAIN", "PD", "PD OLD"}
        or bool(re.fullmatch(r"CC BY (?:2\.0|2\.5|3\.0|4\.0)", norm))
    )
    if not permitted:
        return None
    url = str(info.get("thumburl") or info.get("url") or "")
    uri = urlparse(url)
    if uri.scheme != "https" or (uri.hostname or "") != "upload.wikimedia.org":
        return None
    if not re.search(r"\.(jpe?g|png)(?:\?|$)", uri.path, flags=re.I):
        return None
    credits = clean_html((meta.get("Artist") or {}).get("value") or "")
    if not credits:
        # Do not publish a CC BY image without a credited author.
        if not (norm.startswith("PD") or norm in {"CC0", "CC0 1.0", "PUBLIC DOMAIN"}):
            return None
        credits = "Dominio público / sin autor identificado"
    attribution = clean_html((meta.get("Credit") or {}).get("value") or "")
    width = info.get("thumbwidth") or info.get("width") or 0
    height = info.get("thumbheight") or info.get("height") or 0
    return {
        "url": url, "title": title, "author": credits[:130],
        "license": license_name, "page": info.get("descriptionurl") or "",
        "credit": (credits[:65] + " / " + license_name + " / Wikimedia Commons")[:115],
        "width": width, "height": height,
        "attribution": attribution[:200],
        "identity_method": "Wikidata P18" if confirmed_by_wikidata else "Commons exact-name filename",
    }


def licensed_photo(name):
    """Dynamically find a real, named and reuse-cleared Commons photograph.

    Search order: curated Wikidata P18 image, then title-exact licensed Commons
    files with expanded queries. An unrelated company logo or guessed portrait
    is not an acceptable substitute.
    """
    api = "https://commons.wikimedia.org/w/api.php"
    p18 = wikidata_identity_photo(name)
    if p18:
        try:
            data = wiki_json(api, {
                "action": "query", "format": "json", "titles": p18,
                "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                "iiurlwidth": 1280,
            })
            for page in ((data.get("query") or {}).get("pages") or {}).values():
                image = checked_commons_file(page, name, confirmed_by_wikidata=True)
                if image:
                    return image
        except (ValueError, OSError) as exc:
            print("Commons licensing lookup for P18 unavailable:", type(exc).__name__)

    queries = [
        '"' + name + '"',
        "intitle:" + " intitle:".join(tokens(name)[:4]),
        name + " portrait",
    ]
    options = []
    seen = set()
    for query in queries:
        try:
            data = wiki_json(api, {
                "action": "query", "format": "json", "generator": "search",
                "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": 50,
                "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                "iiurlwidth": 1280,
            })
            pages = (data.get("query") or {}).get("pages") or {}
            for page in pages.values():
                image = checked_commons_file(page, name)
                if image and image["page"] not in seen:
                    seen.add(image["page"])
                    options.append(image)
        except (ValueError, OSError) as exc:
            print("Commons query failed:", query, type(exc).__name__, str(exc)[:130])
        if options:
            break
    options.sort(key=lambda a: (
        # Portrait orientation preferred for shorts, then source resolution.
        int(a["height"] > a["width"]),
        min(int(a["width"]), 1280),
    ), reverse=True)
    if not options:
        print("No license-cleared named photograph found for:", name)
    return options[0] if options else None


def save_commons_photo(name, destination):
    image = licensed_photo(name)
    if not image:
        return None
    request = Request(image["url"], headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            kind = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if kind not in {"image/jpeg", "image/png"}:
                return None
            payload = response.read(8_000_001)
            if len(payload) > 8_000_000 or not payload:
                return None
        suffix = ".jpg" if kind == "image/jpeg" else ".png"
        photo_path = destination.with_suffix(suffix)
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        photo_path.write_bytes(payload)
        image["local"] = "images/" + photo_path.name
        print("Licensed Commons photo candidate:", name, image["license"])
        return image
    except OSError as exc:
        print("Commons photo download unavailable for", name, type(exc).__name__)
        return None


def cue(sentence, index, count, source, subjects, original_nums, demo=False):
    """Choose factual scene type from entities ACTUALLY named in this sentence."""
    result = {"kind": "headline", "subject": sentence}
    if index == count - 1 and re.search(r"(?:MN\s+Short|eme ene short|em en short)", sentence, flags=re.I):
        return {"kind": "outro", "subject": "MN Short"}
    if demo:
        demo_types = ["headline", "person", "source", "metric", "person", "place", "headline", "outro"]
        kind = demo_types[index % len(demo_types)]
        return {
            "kind": kind,
            "subject": (
                "Jensen Huang" if kind == "person" else
                "3 controles editoriales" if kind == "metric" else
                "Contexto visual" if kind == "place" else
                "Fuente original" if kind == "source" else
                sentence
            ),
            **({"metric": "3"} if kind == "metric" else {}),
            **({"person": "Jensen Huang"} if kind == "person" else {}),
        }
    for item in subjects:
        if not isinstance(item, dict):
            continue
        subject = str(item.get("name") or "").strip()
        kind = str(item.get("kind") or "").lower()
        if len(subject) < 4 or not named(sentence, subject):
            continue
        source_text = str(source.get("title") or "") + " " + str(source.get("description") or "")
        if not named(source_text, subject):
            continue
        if kind == "person":
            return {"kind": "person", "subject": subject, "person": subject}
        if kind == "place":
            return {"kind": "place", "subject": subject}
        if kind in {"organization", "event"}:
            return {"kind": "headline", "subject": subject}
    if source.get("publisher") and str(source["publisher"]).lower() in sentence.lower():
        return {"kind": "source", "subject": str(source["publisher"])}
    # Numbers must be present in the original feed; never illustrate invented statistics.
    for match in re.finditer(r"(?<!\w)\d+(?:[.,]\d+)?%?", sentence):
        number = match.group(0)
        if number in original_nums and len(number) <= 7 and not (1900 <= int(re.sub(r"\D", "", number) or 0) <= 2100):
            return {"kind": "metric", "subject": sentence[:105], "metric": number}
    if index == 0:
        return {"kind": "headline", "subject": str(source.get("title") or sentence)[:130]}
    return result


def voice_duration(path):
    info = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True, timeout=20).strip()
    duration = float(info)
    if not 0.1 < duration < 60:
        raise RuntimeError("Unexpected audio duration: " + info)
    return duration


def spoken_text(text, voice):
    """Apply voice-specific brand phonetics without changing the visible script."""
    replacements = {
        "es": "eme ene short", "en": "em en short",
        "fr": "ème enne short", "de": "em en short",
        "it": "emme enne short", "pt": "eme ene short",
        "ru": "эм эн шорт", "zh": "艾姆恩肖特",
        "ja": "エムエヌ ショート", "ar": "إم إن شورت",
    }
    locale = voice.split("-", 1)[0]
    return re.sub(
        r"\bMN\s*Short\b",
        lambda _: replacements.get(locale, "MN Short"), text, flags=re.I,
    )


def boundary_to_timing(part):
    """Edge Neural TTS offsets/durations are 100-nanosecond ticks."""
    if part.get("type") != "WordBoundary":
        return None
    word = str(part.get("text") or "").strip()
    if not word:
        return None
    start = max(0, int(part["offset"])) / 10_000_000
    duration = max(0, int(part["duration"])) / 10_000_000
    return {"text": word, "start": round(start, 4), "end": round(start + duration, 4)}


VOICE_ALTERNATIVES = {
    "es": ["es-ES-ElviraNeural"],
    "en": ["en-GB-SoniaNeural"],
    "fr": ["fr-FR-DeniseNeural"],
    "de": ["de-DE-KatjaNeural"],
    "it": ["it-IT-ElsaNeural"],
    "pt": ["pt-PT-RaquelNeural"],
    "ru": ["ru-RU-SvetlanaNeural"],
    "zh": ["zh-CN-XiaoxiaoNeural"],
    "ja": ["ja-JP-NanamiNeural"],
    "ar": ["ar-SA-ZariyahNeural", "ar-EG-SalmaNeural"],
}


def voices_for_locale(primary):
    locale = primary.split("-", 1)[0]
    return list(dict.fromkeys([primary] + VOICE_ALTERNATIVES.get(locale, [])))


async def synthesize(text, voice, output):
    """Capture actual audio and WordBoundary metadata in the same request.

    A neural voice may stop returning sound even while other locales work.
    Try same-locale alternative voices; never fabricate timing or audio.
    """
    import edge_tts

    rendered = spoken_text(text, voice)
    locale = voice.split("-", 1)[0]
    output.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for candidate_voice in voices_for_locale(voice):
        for attempt in range(3):
            marks = []
            try:
                speech = edge_tts.Communicate(
                    rendered, voice=candidate_voice, rate="-4%", volume="+12%",
                    boundary="WordBoundary",
                )
                with output.open("wb") as handle:
                    async for part in speech.stream():
                        if part["type"] == "audio":
                            handle.write(part["data"])
                        elif part["type"] == "WordBoundary":
                            timed = boundary_to_timing(part)
                            if timed:
                                marks.append(timed)
                if output.stat().st_size <= 500:
                    raise RuntimeError("TTS returned empty audio")
                if not marks:
                    raise RuntimeError("TTS returned no word boundaries")
                if any(marks[i]["start"] > marks[i + 1]["start"] for i in range(len(marks) - 1)):
                    raise RuntimeError("TTS word-boundary timing is not monotonic")
                if candidate_voice != voice:
                    print("Voice fallback used:", locale, candidate_voice)
                # Gentle pacing reduces failures when requesting 80 utterances.
                await asyncio.sleep(0.65)
                return marks
            except Exception as exc:
                last_error = exc
                output.unlink(missing_ok=True)
                print("Voice service unavailable for", candidate_voice,
                      "attempt", attempt + 1, type(exc).__name__)
                await asyncio.sleep(2.5 + attempt * 3.5)
    raise RuntimeError(
        "Word-synchronized TTS failed for " + locale + " using "
        + ", ".join(voices_for_locale(voice)) + "; last error: "
        + type(last_error).__name__
    ) from last_error


VOICES = {
    "es": "es-ES-AlvaroNeural",
    "en": "en-GB-RyanNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-PT-DuarteNeural",
    "ru": "ru-RU-DmitryNeural",
    "zh": "zh-CN-YunxiNeural",
    "ja": "ja-JP-KeitaNeural",
    "ar": "ar-SA-HamedNeural",
}


async def build(editorial, mode, languages="all"):
    generated, source = editorial["generated"], editorial["source"]
    if languages not in {"all", "es"}:
        raise ValueError("Only 'all' or 'es' render profiles are supported")
    selected_languages = list(VOICES) if languages == "all" else ["es"]
    if mode == "demo":
        all_demo = json.loads((MOTION / "demo_translations.json").read_text(encoding="utf-8"))
        translations = {lang: all_demo[lang] for lang in selected_languages}
    elif languages == "es":
        # One real Spanish news story must not trigger translation of nine
        # additional languages or generation of nine unused audio tracks.
        translations = {"es": split_sentences(generated["script_es"])}
    else:
        translations_path = ROOT / "mn_short_motion_translations.json"
        if not translations_path.is_file():
            raise RuntimeError("Missing aligned translations; run mn_short_motion_translate.py first.")
        translations = json.loads(translations_path.read_text(encoding="utf-8"))

    # One semantic and visual storyboard is shared among all languages. Every
    # translation MUST have precisely the same number/order of segments.
    original = translations.get("es") or []
    if not isinstance(original, list) or not (3 <= len(original) <= 18):
        raise RuntimeError("Canonical Spanish story has unexpected scene count")
    if set(translations) != set(selected_languages):
        raise RuntimeError("Missing requested languages: " + repr(set(selected_languages) - set(translations)))
    for lang, segments in translations.items():
        if not isinstance(segments, list) or len(segments) != len(original):
            raise RuntimeError("Screen-to-screen translation mismatch: " + lang)
        if any(not isinstance(s, str) or len(s.strip()) < 2 for s in segments):
            raise RuntimeError("Empty/invalid spoken segment: " + lang)

    shutil.rmtree(PUBLIC / "audio", ignore_errors=True)
    shutil.rmtree(PUBLIC / "images", ignore_errors=True)
    PROPS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    original_nums = set(re.findall(
        r"(?<!\w)\d+(?:[.,]\d+)?%?",
        str(source.get("title") or "") + " " + str(source.get("description") or "")
    ))
    visuals = [
        cue(sentence, i, len(original), source,
            generated.get("visual_subjects") or [], original_nums,
            demo=(mode == "demo"))
        for i, sentence in enumerate(original)
    ]

    photo_cache = {}
    credits = []
    for item in visuals:
        person = item.get("person")
        if person and person not in photo_cache:
            photo_cache[person] = save_commons_photo(
                person, PUBLIC / "images" / ("person_" + str(len(photo_cache) + 1))
            )
            if photo_cache[person]:
                credits.append({"person": person, **photo_cache[person]})
        if person and photo_cache.get(person):
            item["image"] = photo_cache[person]["local"]
            item["credit"] = photo_cache[person]["credit"]
        elif person:
            raise RuntimeError(
                "EDITORIAL PHOTO REQUIRED: no authenticated, reuse-cleared "
                "portrait found for '" + person + "'. Stop this video; "
                "never replace a real person with initials, a logo or stock."
            )

    durations = {}
    for lang in selected_languages:
        voice = VOICES[lang]
        sentences = translations[lang]
        cursor = 0
        scenes = []
        for index, sentence in enumerate(sentences):
            picture = visuals[index].copy()
            # Exact same type, photo, metric, and named subject as all other
            # languages. Translate all non-entity text displayed in graphics.
            if picture["kind"] == "headline":
                picture["subject"] = sentence
            if picture["kind"] == "metric":
                picture["subject"] = sentence
            audio_rel = "audio/" + lang + "_" + str(index).zfill(2) + ".mp3"
            audio_file = PUBLIC / audio_rel
            audio_file.parent.mkdir(parents=True, exist_ok=True)
            word_timings = await synthesize(sentence, voice, audio_file)
            frames = max(45, math.ceil(voice_duration(audio_file) * FPS) + 5)
            scenes.append({
                "text": sentence, "audio": audio_rel, "startFrame": cursor,
                "durationFrames": frames, "wordTimings": word_timings, **picture,
            })
            cursor += frames
        if cursor > 95 * FPS:
            raise RuntimeError(
                lang + " audio exceeds 95 seconds: need shorter editorial narration"
            )
        props = {
            "language": lang,
            "publisher": source.get("publisher") or "Media News",
            "storyTitle": generated.get("title_" + lang) or generated.get("title_es") or "",
            "sourceUrl": source.get("url") or "",
            "totalFrames": cursor,
            "scenes": scenes,
        }
        (PROPS / (lang + ".json")).write_text(
            json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        durations[lang] = round(cursor / FPS, 2)
        print(lang, len(scenes), "scenes", durations[lang], "seconds")

    metadata = {
        "mode": mode, "source": source, "generated": generated,
        "aligned_translations": translations,
        "durations_seconds": durations,
        "photo_candidates_selected": credits,
        "photo_selection_notice": "Commons license and title checks do not prove subject identity; inspect all chosen photos and rights before publication.",
        "languages": selected_languages,
        "autopublish": False,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT / "editorial-y-creditos.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT / "LEEME.txt").write_text(
        "\ufeffMNShort — MOTOR REMOTION\n"
        + "Prueba: " + mode.upper() + "\n"
        + "Fuente: " + str(source.get("url") or "") + "\n"
        + "Idiomas solicitados: " + ", ".join(selected_languages) + "\n"
        + "MP4 para revisión: " + ", ".join("MNShort_MOTION_" + x.upper() + ".mp4" for x in selected_languages) + "\n"
        + "Solo para revisión: NO se publica automáticamente.\n"
        + "Las fotografías de Commons requieren verificar identidad, derechos y atribución.\n"
        + "Los diagramas de contexto NO son mapas geográficos.\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("demo", "live"), default="demo")
    parser.add_argument("--languages", choices=("all", "es"), default="all",
                        help="All ten languages, or a single Spanish review clip")
    args = parser.parse_args()
    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe is required for synchronized audio scenes")
    if args.mode == "demo":
        editorial = demo_editorial()
    else:
        source_json = ROOT / "mn_short_editorial.json"
        if not source_json.is_file():
            raise SystemExit("Missing MN Short RSS/Gemini editorial manifest. Run mn_short_cloud.py prepare first.")
        editorial = json.loads(source_json.read_text(encoding="utf-8"))
    asyncio.run(build(editorial, args.mode, languages=args.languages))


if __name__ == "__main__":
    main()
