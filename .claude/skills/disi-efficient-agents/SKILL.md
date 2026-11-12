---
name: disi-efficient-agents
description: Minimize quota and context use when operating Claude Code/OpenRouter/other authorized free providers in DISI's GitHub repositories.
---
# DISI — operar con bajo consumo de API

Use this skill before tasks that mention "cuota", "tokens", "límite", "gratis", "Claude Code", "OpenRouter", "agents", "GitHub Actions".

## Fixed method
1. Evaluate whether deterministic code (Python, GitHub Actions, FFmpeg, ffprobe, grep, tests) can do the task with ZERO language-model requests. Do not spend inference on parsing JSON, filtering files, arithmetic, static rules or copying source text.
2. Delegate small independent subtasks to specialized agents ONLY when it reduces total inference calls; spawning five agents for a single script normally wastes the quota.
3. For public-data tasks choose existing, permitted no-cost providers. Treat each provider's daily/minute quotas independently. Do not rotate identities or use account farms to evade limits.
4. Batch input into one compact job with explicit deliverable, file paths, maximum words and validation criteria; use targeted Glob/Grep before Read to avoid loading whole repositories. Skip verbose logs or filter their output locally.
5. Prefer `claude --model cohere/north-mini-code:free -p "request"` on the already tested OpenRouter setup for constrained review tasks. Free provider may stop supporting the model; verify a live tool-call smoke test before treating it as production compatible.
6. After a 429, do not retry repeatedly: use exponential backoff only within provider policy and small retry budget. When daily cap is exhausted, switch to another separately authorized provider or local inference; otherwise run deterministic work without an LLM.
7. Preserve clean versions: commit a change only after deterministic unit tests. Avoid re-generating already approved assets, voiceovers, video renders and translations.
8. Never insert secret keys into a repo, Action input, issue, tool log or GitHub PR. Configurations must use local credential storage or GitHub Actions secrets.
9. Do not confuse credits with rate limits: tool-based context compression reduces tokens and may increase useful work per session, but does NOT raise OpenRouter's free requests/day ceiling.
10. Record budget before and after an experiment only from real provider counters. Unknown values remain UNKNOWN.

## Candidate open-source tools, not auto-installed binaries
- musistudio/claude-code-router: MIT, provider router; evaluate on a trusted machine and pin the version after review.
- rtk-ai/rtk: Apache-2.0, compresses shell output. Check for truncation of error details before adopting.
- anthropics/skills: reviewed official skill patterns. Import only a few proven skills; excessive MCPs load unnecessary context.
- haiggoh/free-agents: MIT provider offload; not yet Windows-certified end-to-end. Use isolated tests, do not import entire marketplace unattended.

No configuration in this skill authorizes unrestricted spend, API-limit circumvention, or autonomous publication.