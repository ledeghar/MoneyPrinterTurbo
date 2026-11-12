#!/usr/bin/env python3
"""Owner-authored same-repository PR task validation for DISI Claude Gateway.

Static validation only: no network, shell execution, credentials or GitHub writes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
OWNER = "ledeghar"
REPO = "ledeghar/MoneyPrinterTurbo"
PREFIX = "[DISI-CLAUDE]"
MAX_CHARS = 2500
SUSPICIOUS = ("sk-or-", "ghp_", "github_pat_", "-----begin private key",
              "anthropic_api_key=", "anthropic_auth_token=",
              "openrouter_api_key=", "password=")

def validate_request(event: dict, payload: dict) -> dict:
    if event.get("action") not in ("opened", "synchronize", "reopened"):
        raise ValueError("Only opening or updating an authorized PR is permitted")
    pr = event.get("pull_request") or {}
    if (pr.get("user") or {}).get("login") != OWNER:
        raise ValueError("PR owner is not authorized")
    if not str(pr.get("title", "")).startswith(PREFIX):
        raise ValueError("Required DISI task PR title prefix missing")
    head = pr.get("head") or {}
    if (head.get("repo") or {}).get("full_name") != REPO:
        raise ValueError("Fork PRs must never receive provider credentials")
    if payload.get("schema") != "disi-claude-task/1":
        raise ValueError("Invalid schema")
    if payload.get("approved_by") != OWNER or payload.get("mode") != "READ_ONLY":
        raise ValueError("Only explicitly owner-approved read-only tasks are permitted")
    task = payload.get("task")
    if not isinstance(task, str) or len(task.strip()) < 15 or len(task) > MAX_CHARS:
        raise ValueError("Task must be between 15 and 2500 characters")
    if any(s in task.lower() for s in SUSPICIOUS):
        raise ValueError("Possible secret detected in public task")
    if payload.get("publish") is not False or payload.get("spend") is not False:
        raise ValueError("No publication or paid inference is authorized")
    if not isinstance(payload.get("request_id"),str) or len(payload["request_id"]) < 8:
        raise ValueError("Missing request id")
    return {"number":int(pr["number"]), "request_id":payload["request_id"],
            "task_length":len(task), "mode":"READ_ONLY"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--event",type=Path,required=True)
    p.add_argument("--request",type=Path,required=True)
    a=p.parse_args()
    outcome=validate_request(json.loads(a.event.read_text(encoding="utf-8")),json.loads(a.request.read_text(encoding="utf-8")))
    print("DISI PR #{} / task {} / length {} / {}".format(
        outcome["number"],outcome["request_id"],outcome["task_length"],outcome["mode"]))
if __name__=="__main__":main()
