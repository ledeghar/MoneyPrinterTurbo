# DISI Remote Gateway v0.2 — ChatGPT ↔ GitHub ↔ Claude Code (12Nov2026)

## Important correction
The initial issue-based trigger could not run: GitHub returned HTTP **410: Issues has been disabled in this repository.** Its trigger is now replaced by an **authorized same-repository pull request carrying a task file**, which the connected ChatGPT GitHub tool can create. No Issues feature is required.

## Architecture
ChatGPT with GitHub connector → creates a dedicated branch from `main` → creates `.disi/claude-task.json` with a non-sensitive, read-only request → opens a same-repository PR titled `[DISI-CLAUDE] ...` → GitHub Actions `pull_request` event launches `DISI Claude Gateway - owner-only PR tasks` → audit in Actions logs and review output.

Only PRs authored by `ledeghar`, from `ledeghar/MoneyPrinterTurbo` to the same repo, with the exact title prefix, enter the agent job. Fork PRs and other contributors are excluded before any secret is loaded. Preflight checks the task schema, mode, owner, length and no-publication/no-spend flags. This is a **public repository**: do not enter HUMINT, keys, private files or sensitive client material in PR/task text.

## How to submit a task with ChatGPT
The connector can create branches, files and PRs; no GitHub CLI or powered-on laptop needed. Request format on the branch:

```json
{
  "schema": "disi-claude-task/1",
  "request_id": "20261112-mnshort-audit-001",
  "approved_by": "ledeghar",
  "mode": "READ_ONLY",
  "task": "Review CLAUDE.md and the DISI book skills; identify three ways to reduce OpenRouter requests. Do not modify files.",
  "publish": false,
  "spend": false
}
```

This is intended for planning, code review, scripts and marketing drafts only. ChatGPT can later read the action logs, check results, create a code-fix PR or modify instructions. The Claude runner cannot edit the repo, execute shell commands or directly publish.

## One-time manual action required
Go to https://github.com/ledeghar/MoneyPrinterTurbo/settings/secrets/actions
Create a repository secret named **OPENROUTER_API_KEY**. Use a separate project-specific key, controlled by spend limits. Never paste credentials in ChatGPT or GitHub task files. Without this secret, the test-run fails clearly before contacting any model.

OpenRouter is rate limited even when free. The action uses `cohere/north-mini-code:free` from the prior Windows smoke test; tool-call compatibility in GitHub Actions remains to be established experimentally. `--max-turns 6`; no automatic reattempt flood.

## Testing
`python3 -m unittest discover -s tests -p test_disi_claude_gateway.py -v`

The task PR's Actions logs will show either: completed model result, an exact provider error, or the missing-secret error. Do not call the connection operational until a real task completes.

## Follow-up
Once read-only Claude actions work with the user's provider key, extend to controlled edit-in-branch proposals only and review each PR. An independent private gateway may later be mirrored into DISIM if authorized, still without uploading HUMINT. GitHub Actions is not unlimited compute and does not access the user's local Windows process.