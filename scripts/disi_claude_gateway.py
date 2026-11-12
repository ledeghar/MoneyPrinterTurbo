#!/usr/bin/env python3
"""Validate owner-only public GitHub issue commands before Claude is launched.

No secrets, third-party libraries, network access, or GitHub mutations.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TITLE_PREFIX = "[DISI-CLAUDE]"
OWNER = "ledeghar"
MAX_CHARS = 2500
DANGEROUS_PATTERNS = (
    "sk-or-", "ghp_", "github_pat_", "-----begin private key",
    "anthropic_api_key=", "anthropic_auth_token=",
)

def validate_event(payload: dict) -> dict:
    if payload.get("action") != "opened":
        raise ValueError("Only newly opened tasks can start a remote execution")
    issue = payload.get("issue") or {}
    user = issue.get("user") or {}
    title = issue.get("title") or ""
    body = issue.get("body") or ""
    if user.get("login") != OWNER:
        raise ValueError("Only the account owner may start an agent")
    if not title.startswith(TITLE_PREFIX):
        raise ValueError("Missing DISI task prefix")
    if not isinstance(body, str) or not (15 <= len(body) <= MAX_CHARS):
        raise ValueError("Task body must contain 15-2500 characters")
    if any(s in body.lower() for s in DANGEROUS_PATTERNS):
        raise ValueError("Possible credential in issue; never use public issues for secrets")
    if issue.get("pull_request"):
        raise ValueError("Only ordinary issues may run")
    return {"issue_number": int(issue["number"]), "task_length": len(body), "mode": "READ_ONLY"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    args = parser.parse_args()
    outcome = validate_event(json.loads(args.event.read_text(encoding="utf-8")))
    print("DISI owner task validated: issue #{} / {} characters / {}".format(
        outcome["issue_number"], outcome["task_length"], outcome["mode"]))

if __name__ == "__main__":
    main()
