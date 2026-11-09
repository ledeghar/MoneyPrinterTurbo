#!/usr/bin/env python3
"""Fail-closed release check before MN Short can schedule any public YouTube Short.

Generating a valid MP4 is NOT proof that its claims, depicted subjects or
image rights are reliable. Publication therefore needs evidence files from
future source/scene verification, bound to this exact exported video hash.

The current Pexels-only renderer does not produce that evidence; it will
generate videos for review but will never automatically publish them.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

OUTPUT = Path("mn-short-output")
SLOTS = frozenset({"08:00", "10:00", "12:00", "16:00", "18:00", "20:00"})


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path.name}")
    return value


def _url_host(url: str) -> str:
    try:
        parsed = urlparse(str(url))
        if parsed.scheme != "https":
            return ""
        host = (parsed.hostname or "").lower()
        if not host or host in {"localhost", "127.0.0.1"}:
            return ""
        return host.removeprefix("www.")
    except ValueError:
        return ""


def _media_probe(path: Path) -> dict:
    """Read MP4 shape and audio without trusting a filename or generated text."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=35, check=False,
    )
    if proc.returncode:
        raise RuntimeError("ffprobe could not inspect the exported MP4")
    return json.loads(proc.stdout)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assess(folder: Path = OUTPUT) -> dict:
    """Returns an inspectable decision; never creates or alters evidence."""
    reasons: list[str] = []
    videos = list(folder.glob("*.mp4"))
    video = videos[0] if len(videos) == 1 else None
    if video is None:
        reasons.append("Se requiere exactamente un vídeo MP4 por franja.")
    elif video.stat().st_size < 200_000:
        reasons.append("El MP4 está vacío o demasiado pequeño.")

    editorial = None
    try:
        editorial = _json(folder / "editorial.json")
    except (ValueError, OSError, json.JSONDecodeError):
        reasons.append("Falta el archivo editorial.json válido.")

    expected_subjects: set[str] = set()
    if editorial:
        grid = editorial.get("grid") or {}
        generated = editorial.get("generated") or {}
        source = editorial.get("source") or {}
        if (grid.get("slot") not in SLOTS or grid.get("count") != 1
                or grid.get("language") != "es"):
            reasons.append("Horario, idioma o número de vídeos no coinciden.")
        title = str(generated.get("title_es") or "").strip()
        narration = str(generated.get("script_es") or "").strip()
        if not (10 <= len(title) <= 100 and 40 <= len(narration.split()) <= 150):
            reasons.append("Título o narración están incompletos.")
        if not _url_host(source.get("url", "")):
            reasons.append("La fuente original no tiene una URL HTTPS válida.")
        for entity in generated.get("visual_subjects", []) or []:
            if not isinstance(entity, dict):
                continue
            if entity.get("kind") in {"person", "organization"}:
                name = str(entity.get("name") or "").strip()
                if name:
                    expected_subjects.add(name.casefold())

    hash_value = ""
    if video and video.is_file() and video.stat().st_size >= 200_000:
        hash_value = _sha256(video)
        try:
            probe = _media_probe(video)
            videospecs = [x for x in probe.get("streams", [])
                          if x.get("codec_type") == "video"]
            audio = [x for x in probe.get("streams", [])
                     if x.get("codec_type") == "audio"]
            duration = float((probe.get("format") or {}).get("duration") or 0)
            if not videospecs or not audio:
                reasons.append("El Short no tiene pistas de imagen y audio.")
            else:
                width = int(videospecs[0].get("width", 0))
                height = int(videospecs[0].get("height", 0))
                if height <= width or min(width, height) < 480:
                    reasons.append("El vídeo no es vertical o tiene baja resolución.")
            if not 15 <= duration <= 60:
                reasons.append("Duración fuera del intervalo de 15 a 60 segundos.")
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
            reasons.append("No pudo verificarse el formato real del vídeo.")

    # The source-checking stage does NOT exist yet: this is an explicit,
    # machine-verifiable contract to implement later, not a simulated pass.
    try:
        verification = _json(folder / "VERIFICACION_FUENTES.json")
        independent_sources = {
            _url_host(item) for item in verification.get("independent_sources", [])
            if isinstance(item, str) and _url_host(item)
        }
        original_host = _url_host(
            (editorial or {}).get("source", {}).get("url", "")
        )
        if not (verification.get("claims_verified") is True
                and verification.get("original_contribution_verified") is True
                and verification.get("unresolved_claims") == []
                and len(independent_sources - {original_host}) >= 1
                and verification.get("source_article_url")
                == (editorial or {}).get("source", {}).get("url")):
            reasons.append(
                "Sin comprobación independiente de los hechos y afirmaciones del guion."
            )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        reasons.append(
            "Falta VERIFICACION_FUENTES.json: no existe todavía un validador periodístico independiente."
        )

    # Identity/license evidence must correspond to the EXACT final video and
    # timeline, never simply to found image URLs or a page containing a logo.
    try:
        evidence = _json(folder / "ESCENAS_VERIFICADAS.json")
        scenes = evidence.get("scenes")
        if (not hash_value or evidence.get("rendered_mp4_sha256") != hash_value
                or evidence.get("timecoded_alignment_verified") is not True
                or not isinstance(scenes, list) or len(scenes) < 2):
            reasons.append("Sin correspondencia visual comprobada para el MP4 producido.")
        else:
            covered: set[str] = set()
            for scene in scenes:
                if not isinstance(scene, dict):
                    reasons.append("El manifiesto de escenas contiene entradas inválidas.")
                    break
                if scene.get("license_cleared") is not True:
                    reasons.append("Una escena no tiene autorización de uso comprobada.")
                    break
                if not _url_host(scene.get("source_page", "")):
                    reasons.append("Una escena no tiene fuente documental verificable.")
                    break
                subject = str(scene.get("named_subject") or "").strip().casefold()
                if subject and scene.get("subject_identity_verified") is True:
                    covered.add(subject)
            if not expected_subjects.issubset(covered):
                reasons.append(
                    "No se muestra de forma verificable a los protagonistas nombrados."
                )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        reasons.append(
            "Falta ESCENAS_VERIFICADAS.json: el renderizador actual usa Pexels sin validar protagonistas."
        )

    return {
        "approved": not reasons,
        "decision": "APTO_PARA_PROGRAMAR" if not reasons else "RETENIDO_PARA_REVISION",
        "video_file": video.name if video else None,
        "video_sha256": hash_value,
        "reasons": reasons,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    result = assess()
    (OUTPUT / "CONTROL_PUBLICACION.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "MN SHORT — CONTROL PREVIO A PUBLICACIÓN",
        result["decision"],
        "",
    ]
    for reason in result["reasons"]:
        lines.append("- " + reason)
    if not result["reasons"]:
        lines.append("Archivo verificado: publicación programable si OAuth y permisos lo autorizan.")
    (OUTPUT / "CONTROL_PUBLICACION.txt").write_text(
        "\ufeff" + "\n".join(lines), encoding="utf-8"
    )
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write("approved=" + str(result["approved"]).lower() + "\n")
    print("MN Short release check:", result["decision"])
    for reason in result["reasons"]:
        print(" - " + reason)


if __name__ == "__main__":
    main()
