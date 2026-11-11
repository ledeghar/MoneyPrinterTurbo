#!/usr/bin/env python3
"""Lead acquisition pack for DISI book marketing: public reader channels, not spam.

Creates human-readable, evidence-backed individual outreach drafts and a
review-only acquisition scoreboard. NO network, email, DMs, paid APIs or publishing.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date
import json
from pathlib import Path

DEFAULT_TARGETS = Path(__file__).resolve().parent / "targets.json"
ALLOWED_CONTACTS = {"account_setup","public_form","public_contact_page","public_business_email","public_website"}
ALLOWED_PRIORITIES = {"A","B","C"}
ALLOWED_BOOKS = {"alepo","jartum"}
BOOK_PROOF = {
    "alepo": "ALEPO, obra de Juan Manuel Ledesma sobre la guerra de Siria y las personas atrapadas en el conflicto.",
    "jartum": "JARTUM: Los que quedaron atrás, testimonio de Juan Manuel Ledesma sobre las evacuaciones y los civiles atrapados en Jartum en abril de 2023."
}
VERIFIED_STORE = "https://www.lulu.com/es/shop/juan-manuel-ledesma/jartum-los-que-quedaron-atras/paperback/product-m2rdqz7.html"

def read_targets(path: Path = DEFAULT_TARGETS) -> list[dict]:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("schema") != "disi-buyer-acquisition/0.1":
        raise ValueError("Unsupported target schema")
    targets = bundle.get("targets", [])
    ids = set()
    for t in targets:
        if t["id"] in ids:
            raise ValueError("Duplicate acquisition target")
        ids.add(t["id"])
        if t["priority"] not in ALLOWED_PRIORITIES or t["contact"] not in ALLOWED_CONTACTS:
            raise ValueError("Unknown lead category")
        if not t.get("url", "").startswith("https://") or not t.get("evidence"):
            raise ValueError("Every prospect requires public HTTPS source and provenance")
        if not set(t.get("books", [])).issubset(ALLOWED_BOOKS):
            raise ValueError("Unknown catalog book")
        if t["contact"] == "public_business_email" and "@" not in t.get("email", ""):
            raise ValueError("Missing public business contact")
    return targets

def pitch(t: dict) -> str:
    if t["contact"] == "account_setup":
        return (
            "TAREA DE ALTA EN PLATAFORMA, NO ENVÍO DE MENSAJE\n\n"
            + t["name"] + "\n" + t["url"] + "\n"
            + "Objetivo: " + t["ask"] + "\n"
            + "Limitación: " + t["constraint"] + "\n"
            + "Acción requiere acceso del titular de la cuenta.\n"
        )
    if t["priority"] == "C":
        return (
            "CONTACTO POR IDENTIFICAR ANTES DE PRESENTAR PROPUESTA\n\n"
            + t["name"] + "\n" + t["url"] + "\n"
            + "Motivo editorial: " + t["ask"] + "\n"
            + "No enviar nada hasta encontrar una vía oficial de contacto apropiada.\n"
        )
    subject = "Propuesta editorial: ALEPO y JARTUM — crónicas de guerra y testimonios"
    intro = (
        "Buenos días:\n\n"
        "Soy Juan Manuel Ledesma, periodista, fotógrafo y autor de ALEPO y "
        "JARTUM: Los que quedaron atrás, dos obras centradas en experiencias humanas "
        "en conflictos contemporáneos.\n\n"
    )
    if t["type"] in {"history_podcast", "literature_podcast", "review_or_interview"}:
        proposal = (
            "Me gustaría proponer una conversación o entrevista sobre lo que ocurre "
            "cuando la cobertura informativa termina y los civiles permanecen en peligro. "
            "Puedo aportar contexto de primera mano y material audiovisual propio.\n\n"
        )
    else:
        proposal = (
            "Me gustaría presentar las obras para su consideración editorial o crítica "
            "independiente, sin condicionar el contenido de una eventual reseña.\n\n"
        )
    closer = (
        "La ficha pública confirmada de JARTUM está disponible aquí:\n"
        + VERIFIED_STORE + "\n\n"
        + "Si el enfoque encaja con vuestra audiencia, puedo facilitar sin coste "
          "un dossier y un ejemplar digital de lectura previa aceptación.\n\n"
          "Muchas gracias por vuestro tiempo.\n"
          "Juan Manuel Ledesma\n"
          "Media News / DISI\n"
    )
    return (
        "ASUNTO: " + subject + "\n"
        "DESTINATARIO/PÁGINA: " + t.get("email", t["url"]) + "\n"
        "ESTADO: BORRADOR — NO ENVIADO\n"
        "JUSTIFICACIÓN: " + t["evidence"] + "\n\n"
        + intro + proposal + closer
    )

def build_pack(targets: list[dict], output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for t in targets:
        records.append({
            "id": t["id"], "contact_name": t["name"], "priority": t["priority"],
            "segment": t["type"], "channel": t["contact"],
            "email": t.get("email", ""), "contact_url": t["url"],
            "source": t.get("evidence_url", t["url"]),
            "action": t["ask"], "status": "NOT_CONTACTED",
            "contacted_at": "", "reply_status": "UNKNOWN",
            "clicks": "", "purchases": "", "revenue_eur": "",
            "notes": t["constraint"], "message_file": t["id"] + ".txt"
        })
        (output / (t["id"] + ".txt")).write_text(pitch(t), encoding="utf-8")
    with (output / "qualified-prospects.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]) if records else [])
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "schema": "disi-acquisition-pack/0.1",
        "created_at": date.today().isoformat(),
        "qualified_public_channels": len(records),
        "messages_sent": 0,
        "sales_attributed": None,
        "cost_eur": 0,
        "status": "MANUAL_APPROVAL_REQUIRED",
        "disallowed": ["automated bulk outreach", "paid reviews",
                       "unsolicited attachments", "false marketing claims"],
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return summary

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    p.add_argument("--output", type=Path, default=DEFAULT_TARGETS.parent / "output")
    args = p.parse_args()
    summary = build_pack(read_targets(args.targets), args.output)
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == "__main__":
    main()
