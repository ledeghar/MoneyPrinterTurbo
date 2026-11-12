# DISI — ChatGPT → GitHub → Claude Code (fase 1, 12Nov2026)

The user has requested a remote control path, without reliance on a powered-on laptop. This is **not** a direct ChatGPT-to-local-Windows connection. The first implementation is a **GitHub issue to GitHub Action to Claude Code** pipeline.

## Scope and permissions

- Repository: `ledeghar/MoneyPrinterTurbo` (PUBLIC). Use **public/editorial non-sensitive tasks only**. Never put HUMINT material, protected images or keys in an issue.
- Only newly OPENED issues by `ledeghar` whose title starts with `[DISI-CLAUDE]` trigger execution.
- `scripts/disi_claude_gateway.py` limits request length to 2,500 characters and rejects obvious credential patterns; these checks do not magically sanitize malicious instructions. Trusted owner only; no fork PR events.
- Runner cannot commit files (`contents: read`); Claude is allowed only read/search tools. No shell commands, file edits, production publishing, external MCP servers or paid API fallback.
- Remote result is in the GitHub Actions log / issue if the official action supports comments in this mode. No promise of production until an actual live session succeeds.

## Critical first setup — owner must perform once

Go to:
https://github.com/ledeghar/MoneyPrinterTurbo/settings/secrets/actions

Choose **New repository secret**, name `OPENROUTER_API_KEY`, paste the previously configured OpenRouter credential or preferably a newly minted project-specific restricted key. NEVER paste the key into a chat, issue, PR, workflow, code file or screenshot. Keep its spending ceiling configured with the provider.

Until this secret exists, the workflow will fail explicitly with `DISI Claude Gateway cannot run until ...`. This failure does not mean a Claude model ran; no provider credits have been consumed.

## Running a test

1. Using the account `ledeghar`, open a new ISSUE titled `[DISI-CLAUDE] Auditoría de estructura MNShort`.
2. Body: `Revisa el README y la arquitectura de video de este repositorio. Devuelve tres mejoras concretas para ahorrar llamadas a OpenRouter. No cambies archivos.`
3. The issue event starts `.github/workflows/disi-claude-gateway.yml` automatically. GitHub charges Actions usage according to plan. A free model is still subject to daily provider quotas.
4. Inspect the job, output and any model errors. Some free-model APIs do not fully implement Claude's tool-use semantics, so a model response alone is not enough to validate the gateway.
5. ChatGPT with connected GitHub can create future owner-authored issues and inspect Actions results, compare code and propose fixes, without interacting with local Claude Code.

## Boundaries
GitHub Actions is not unlimited compute, a long-running agent server or cloud browser. The owner key must be configured; no key = no remote inference. `OpenRouter/free` does not bypass the 50/day free cap. External fallback providers require separate approved keys and independent rate-limit compliance.

The model initially configured here is the free `cohere/north-mini-code:free` that ran on Windows. Verify its API availability and tool calling via GitHub Action. Never auto-publish without a separate owner approval workflow.

## Future extension

After a successful read-only trial:
- Permit Claude to work on a short-lived branch and open a PR, never push directly to main.
- Use approval-gated workflows for video generation or network publications.
- Consider a mirrored private gateway in DISIM (still no HUMINT GitHub uploads) for non-public code tasks.