#!/usr/bin/env python3
"""Schedule MN Short on FB/Instagram and optionally TikTok via Upload-Post.

No API calls without explicit repository opt-in AND passing the independent
editorial/visual QA gate. Does not publish to YouTube, which has a separate
native OAuth pipeline. A scheduled job_id means the post is QUEUED, not that
the platform has published it or that it earns revenue.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

OUTPUT = Path("mn-short-output")
ENDPOINT = "https://api.upload-post.com/api/upload"
SUPPORTED = frozenset({"facebook", "instagram", "tiktok"})
SLOTS = frozenset({"08:00", "10:00", "12:00", "16:00", "18:00", "20:00"})


def configured_platforms(raw: str, tiktok_enabled: bool = False) -> list[str]:
    """Only explicitly selected destinations; YouTube must never double-post."""
    platforms = list(dict.fromkeys(x.strip().lower() for x in raw.split(",") if x.strip()))
    if not platforms or any(platform not in SUPPORTED for platform in platforms):
        raise ValueError("Destinos admitidos: facebook,instagram,tiktok (no youtube)")
    if "tiktok" in platforms and not tiktok_enabled:
        raise ValueError("TikTok requiere MNSHORT_TIKTOK_ENABLED=true; puede tener coste")
    return platforms


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def planned_utc(editorial: dict, now: datetime | None = None) -> str:
    grid = editorial.get("grid") or {}
    slot = grid.get("slot")
    local_date = grid.get("release_local_date")
    if slot not in SLOTS or not isinstance(local_date, str):
        raise ValueError("Fecha u horario de publicación ausente")
    try:
        target = datetime.fromisoformat(f"{local_date}T{slot}:00").replace(
            tzinfo=ZoneInfo("Europe/Madrid")
        ).astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ValueError("Fecha de salida inválida") from exc
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("La hora actual debe incluir zona horaria")
    if target <= current + timedelta(minutes=2):
        raise ValueError("Ya no queda margen para programar la publicación")
    return target.isoformat(timespec="seconds").replace("+00:00", "Z")


def verify_release_evidence(folder: Path) -> tuple[dict, Path]:
    """Do not accept a green CI run as permission to distribute the story."""
    gate = json.loads((folder / "CONTROL_PUBLICACION.json").read_text(encoding="utf-8"))
    videos = list(folder.glob("*.mp4"))
    if len(videos) != 1 or gate.get("approved") is not True:
        raise RuntimeError("Producción retenida por el control editorial o MP4 inexistente")
    movie = videos[0]
    if gate.get("video_sha256") != _sha256(movie):
        raise RuntimeError("El MP4 no coincide con el que superó la revisión")
    editorial = json.loads((folder / "editorial.json").read_text(encoding="utf-8"))
    if editorial.get("grid", {}).get("count") != 1:
        raise RuntimeError("Solo se admite un Short por franja")
    return editorial, movie


def upload_scheduled(
    folder: Path,
    profile: str,
    api_key: str,
    platforms: list[str],
    now: datetime | None = None,
    session: requests.Session | None = None,
) -> dict:
    if os.environ.get("MNSHORT_CROSSPOST_ENABLED", "").lower() != "true":
        raise RuntimeError("Distribución externa no habilitada")
    if not profile.strip() or not api_key.strip():
        raise RuntimeError("Falta cuenta Upload-Post o UPLOAD_POST_API_KEY")
    editorial, video = verify_release_evidence(folder)
    when = planned_utc(editorial, now=now)
    source = editorial["source"]
    title = str(editorial["generated"]["title_es"]).strip()
    if not 10 <= len(title) <= 100:
        raise ValueError("Título de Short no válido")
    text = (
        f"{title}\n"
        f"Fuente: {source['publisher']} — {source['url']}\n"
        "MN Short | Contexto periodístico original. #MNShort #Noticias"
    )
    unique = f"{profile}|{','.join(platforms)}|{when}|{_sha256(video)}"
    idempotency = "mnshort-" + hashlib.sha256(unique.encode("utf-8")).hexdigest()
    form = [
        ("user", profile),
        ("title", text[:2200]),
        ("description", text[:2200]),
        ("scheduled_date", when),
        ("timezone", "UTC"),
    ]
    form.extend(("platform[]", platform) for platform in platforms)
    if "tiktok" in platforms:
        form.append(("tiktok_is_ai_generated", "true"))
    if "facebook" in platforms:
        form.append(("facebook_is_ai_generated", "true"))

    owns_session = session is None
    session = session or requests.Session()
    try:
        with video.open("rb") as media:
            response = session.post(
                ENDPOINT,
                data=form,
                files={"video": (video.name, media, "video/mp4")},
                headers={
                    "Authorization": f"Apikey {api_key}",
                    "Idempotency-Key": idempotency,
                },
                timeout=300,
                allow_redirects=False,
            )
    finally:
        if owns_session:
            session.close()

    # Never blindly retry a timed-out/ambiguous call. A successful 202 is only
    # confirmation that Upload-Post accepted the SCHEDULE, not final delivery.
    if response.status_code != 202:
        raise RuntimeError(
            f"No se confirmó una programación de Upload-Post (HTTP {response.status_code}). "
            f"Buscar idempotency {idempotency} en la cuenta antes de reintentar"
        )
    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError("Respuesta de programación no verificable") from exc
    job_id = result.get("job_id")
    if result.get("success") is not True or not isinstance(job_id, str) or not job_id:
        raise RuntimeError("Upload-Post no devolvió job_id; revisar antes de reintentar")

    record = {
        "provider": "Upload-Post",
        "status": "SCHEDULED_NOT_YET_PUBLISHED",
        "job_id": job_id,
        "platforms": platforms,
        "scheduled_date_utc": when,
        "mp4_sha256": _sha256(video),
        "idempotency_key": idempotency,
        "revenue_status": "NOT_VERIFIED",
        "uploaded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (folder / "PROGRAMACION_REDES.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"MN Short: programación externa aceptada para {','.join(platforms)}; job={job_id}")
    return record


def main() -> None:
    selected = configured_platforms(
        os.environ.get("MNSHORT_CROSSPOST_PLATFORMS", "facebook,instagram"),
        tiktok_enabled=os.environ.get("MNSHORT_TIKTOK_ENABLED", "").lower() == "true",
    )
    upload_scheduled(
        OUTPUT,
        os.environ.get("UPLOAD_POST_PROFILE", ""),
        os.environ.get("UPLOAD_POST_API_KEY", ""),
        selected,
    )


if __name__ == "__main__":
    main()
