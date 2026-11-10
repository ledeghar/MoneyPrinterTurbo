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


def licensed_photo(name):
    """Use Commons only, require full name in file title and CC0/PD/CC BY.

    CC BY-SA and NC/ND are intentionally excluded for this initial pilot.
    The title+license gate is necessary, not a guarantee of photo identity.
    """
    endpoint = "https://commons.wikimedia.org/w/api.php"
    parameters = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": '"' + name + '"', "gsrnamespace": "6",
        "gsrlimit": "18", "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": "1280",
    }
    url = endpoint + "?" + urlencode(parameters)
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(request, timeout=17) as response:
            data = json.load(response)
        pages = (data.get("query") or {}).get("pages") or {}
    except (ValueError, OSError) as exc:
        print("Commons search unavailable for", name, type(exc).__name__)
        return None
    options = []
    for page in pages.values():
        title = str(page.get("title") or "").removeprefix("File:")
        if not named(title, name):
            continue
        details = (page.get("imageinfo") or [])
        if not details:
            continue
        info = details[0]
        meta = info.get("extmetadata") or {}
        license_name = clean_html((meta.get("LicenseShortName") or {}).get("value") or "")
        lic = license_name.upper().replace("-", " ")
        # Avoid licenses with ShareAlike/NonCommercial/NoDerivatives obligations.
        if not (
            lic in {"CC0", "CC0 1.0", "PUBLIC DOMAIN", "PD", "PD-OLD"}
            or re.fullmatch(r"CC BY (?:2\.0|2\.5|3\.0|4\.0)", lic)
        ):
            continue
        description = clean_html((meta.get("ImageDescription") or {}).get("value") or "")
        if description and not named(description, name) and not named(title, name):
            continue
        uri = str(info.get("thumburl") or "")
        hostname = (urlparse(uri).hostname or "").lower()
        if urlparse(uri).scheme != "https" or hostname != "upload.wikimedia.org":
            continue
        if not re.search(r"\.(jpe?g|png)(?:\?|$)", uri, flags=re.I):
            continue
        credit = clean_html((meta.get("Artist") or {}).get("value") or "") or "Autor no indicado"
        options.append({
            "url": uri, "title": title, "author": credit[:100],
            "license": license_name, "page": info.get("descriptionurl") or "",
            "credit": (credit[:65] + " / " + license_name + " / Wikimedia Commons")[:110],
            "width": info.get("thumbwidth") or info.get("width") or 0,
        })
    options.sort(key=lambda d: (d["width"], len(d["title"]) * -1), reverse=True)
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


async def synthesize(text, voice, output):
    import edge_tts
    # Newsroom brand is sounded out in English and Spanish.
    replacements = {
        "es": "eme ene short",
        "en": "em en short",
        "fr": "ème enne short",
        "de": "em en short",
        "it": "emme enne short",
        "pt": "eme ene short",
        "ru": "эм эн шорт",
        "zh": "艾姆恩肖特",
        "ja": "エムエヌ ショート",
        "ar": "إم إن شورت",
    }
    locale = voice.split("-", 1)[0]
    text = re.sub(
        r"\bMN\s+Short\b", lambda _: replacements.get(locale, "MN Short"),
        text, flags=re.I,
    )
    for attempt in range(3):
        try:
            speech = edge_tts.Communicate(text, voice=voice, rate="-4%", volume="+12%")
            await speech.save(str(output))
            if output.stat().st_size <= 500:
                raise RuntimeError("TTS returned empty audio")
            return
        except Exception as exc:
            output.unlink(missing_ok=True)
            if attempt == 2:
                raise RuntimeError(
                    "Neural TTS failed for " + locale + " after retries: " + type(exc).__name__
                ) from exc
            await asyncio.sleep(2.0 + attempt * 3.0)


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
            await synthesize(sentence, voice, audio_file)
            frames = max(45, math.ceil(voice_duration(audio_file) * FPS) + 5)
            scenes.append({
                "text": sentence, "audio": audio_rel, "startFrame": cursor,
                "durationFrames": frames, **picture,
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
