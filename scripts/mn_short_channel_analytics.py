#!/usr/bin/env python3
"""Read-only 90-day YouTube channel/revenue dashboard for MN Short.

Requires a separate OAuth refresh token explicitly granted:
  youtube.readonly
  yt-analytics.readonly
  yt-analytics-monetary.readonly
Never fabricates revenue: unavailable != zero, and YPP membership cannot be
inferred reliably from public counts or an estimated revenue API response.
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path

import requests

GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
YT_CHANNELS = "https://www.googleapis.com/youtube/v3/channels"
YT_REPORTS = "https://youtubeanalytics.googleapis.com/v2/reports"
OUT = Path("mn-short-analytics")


def require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(f"Falta GitHub Actions secret: {name}")
    return val


def oauth_access_token(session: requests.Session) -> str:
    response = session.post(
        GOOGLE_TOKEN,
        data={
            "client_id": require_env("YOUTUBE_CLIENT_ID"),
            "client_secret": require_env("YOUTUBE_CLIENT_SECRET"),
            "refresh_token": require_env("YOUTUBE_ANALYTICS_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        timeout=25,
    )
    if not response.ok:
        raise RuntimeError(
            f"No se pudo autorizar YouTube Analytics (HTTP {response.status_code}). "
            "Revisar permisos OAuth; no compartir credenciales en logs."
        )
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("No hubo access_token de Analytics")
    return str(token)


def query_channel(session: requests.Session) -> dict:
    resp = session.get(
        YT_CHANNELS,
        params={"part": "snippet,statistics", "mine": "true"},
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Error al consultar canal (HTTP {resp.status_code})")
    items = resp.json().get("items") or []
    if len(items) != 1:
        raise RuntimeError("OAuth no seleccionó exactamente un canal de YouTube")
    item = items[0]
    return {
        "id": item.get("id"),
        "title": (item.get("snippet") or {}).get("title"),
        "statistics": item.get("statistics") or {},
    }


def query_stats(session: requests.Session, start: date, end: date, metrics: str) -> dict:
    params = {
        "ids": "channel==MINE",
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "metrics": metrics,
        "dimensions": "day",
        "sort": "day",
    }
    if "estimatedRevenue" in metrics:
        params["currency"] = "EUR"
    response = session.get(YT_REPORTS, params=params, timeout=35)
    if not response.ok:
        raise RuntimeError(f"Informe de YouTube Analytics no disponible (HTTP {response.status_code})")
    return response.json()


def tabular_rows(report: dict) -> list[dict]:
    columns = [x["name"] for x in report.get("columnHeaders", [])]
    return [dict(zip(columns, row)) for row in report.get("rows", [])]


def summarize_daily(rows: list[dict], field: str, days: int, end: date):
    start = end - timedelta(days=days - 1)
    vals = [
        row[field] for row in rows
        if field in row and start.isoformat() <= str(row.get("day", "")) <= end.isoformat()
    ]
    return sum(vals) if vals else None


def write_report(report: dict, metrics_rows: list[dict], revenue_rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "canal_90_dias.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    full_rows: dict[str, dict] = {}
    for data in metrics_rows + revenue_rows:
        day = data.get("day")
        if day:
            full_rows.setdefault(day, {}).update(data)
    columns = ["day", "views", "subscribersGained", "subscribersLost",
               "estimatedMinutesWatched", "estimatedRevenue"]
    with (OUT / "tendencia_diaria.csv").open("w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([full_rows[day] for day in sorted(full_rows)])
    summary = report["summary"]
    revenue = summary.get("estimated_revenue_28d_eur")
    revenue_text = (
        f"{revenue:.2f} EUR (estimación de YouTube, no pago confirmado)"
        if revenue is not None else
        "NO DISPONIBLE; no equivale a 0 EUR"
    )
    lines = [
        "MN SHORT — SEGUIMIENTO DE RENDIMIENTO DEL CANAL",
        f"Canal: {report['channel'].get('title')}",
        f"Fecha de consulta UTC: {report['checked_at_utc']}",
        f"Periodo: {report['start_date']} a {report['end_date']}",
        "",
        "Suscriptores actuales (API): " +
        str(report["channel"]["statistics"].get("subscriberCount", "No disponible")),
        "Visualizaciones últimos 28 días: " + str(summary["views_28d"]),
        "Visualizaciones últimos 90 días: " + str(summary["views_90d"]),
        "Nuevos suscriptores últimos 28 días: " + str(summary["subscribers_gained_28d"]),
        "Ingresos estimados últimos 28 días: " + revenue_text,
        "",
        "Estado de aceptación al Programa de Partners: NO COMPROBADO.",
        "Una respuesta vacía de Analytics no demuestra ausencia de ingresos.",
        "El informe cubre el CANAL completo, no solo los Shorts de MN Short.",
        "Para participar en reparto de anuncios de Shorts se exige la admisión a YPP;",
        "los umbrales generales son 1000 suscriptores y 10 millones de",
        "visualizaciones públicas válidas de Shorts en 90 días (o la vía de",
        "4000 horas públicas de contenido largo).",
        "",
        "Errores de API, si los hubo:",
    ]
    lines.extend(report.get("errors") or ["Ninguno"])
    (OUT / "INGRESOS_Y_VISUALIZACIONES.txt").write_text(
        "\ufeff" + "\n".join(lines), encoding="utf-8"
    )


def run():
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    start = yesterday - timedelta(days=89)
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "start_date": start.isoformat(),
        "end_date": yesterday.isoformat(),
        "channel": {},
        "summary": {},
        "estimated_revenue_currency": "EUR",
        "status_ypp": "UNKNOWN",
        "errors": [],
    }
    with requests.Session() as session:
        token = oauth_access_token(session)
        session.headers.update({"Authorization": f"Bearer {token}"})
        report["channel"] = query_channel(session)
        activity_rows = []
        revenue_rows = []
        try:
            activity = query_stats(
                session, start, yesterday,
                "views,subscribersGained,subscribersLost,estimatedMinutesWatched",
            )
            activity_rows = tabular_rows(activity)
        except (ValueError, RuntimeError) as exc:
            report["errors"].append(str(exc))
        try:
            revenue = query_stats(session, start, yesterday, "estimatedRevenue")
            revenue_rows = tabular_rows(revenue)
        except (ValueError, RuntimeError) as exc:
            report["errors"].append(str(exc) + " (permisos monetarios o canal no elegible)")
    report["summary"] = {
        "views_28d": summarize_daily(activity_rows, "views", 28, yesterday),
        "views_90d": summarize_daily(activity_rows, "views", 90, yesterday),
        "subscribers_gained_28d": summarize_daily(
            activity_rows, "subscribersGained", 28, yesterday
        ),
        "estimated_revenue_28d_eur": summarize_daily(
            revenue_rows, "estimatedRevenue", 28, yesterday
        ),
        "estimated_revenue_90d_eur": summarize_daily(
            revenue_rows, "estimatedRevenue", 90, yesterday
        ),
    }
    write_report(report, activity_rows, revenue_rows)
    print("MN Short analytics report prepared for:", report["channel"].get("title"))
    print("Est. revenue EUR (28 days):", report["summary"]["estimated_revenue_28d_eur"])


if __name__ == "__main__":
    run()
