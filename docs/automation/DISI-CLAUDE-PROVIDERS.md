# DISI — zero-budget provider and skills diligence, 12Nov2026

## Findings / safe source links

1. OpenRouter official: `https://openrouter.ai/collections/free-models`; free variants generally 50 requests/day and 20 RPM, 1,000/day after $10 purchased credits. Failed requests can count. `openrouter/free` selects a model but DOES NOT raise the cap.
2. OpenRouter Claude Action official integration: `https://openrouter.ai/docs/guides/coding-agents/claude-code-integration`. Only free `:free` IDs allowed in DISI's no-spend scope.
3. `https://github.com/musistudio/claude-code-router` (MIT): routing across independently authorized providers, not unlimited requests or a provider-account bypass.
4. `https://github.com/haiggoh/free-agents` (MIT): multi-provider local/remote offload. README reports NVIDIA and Gemini live tests; Windows port / other backends need independent verification.
5. `https://docs.api.nvidia.com/nim/docs/product`: NVIDIA developer free prototyping, subject to provider availability/terms.
6. `https://github.com/rtk-ai/rtk` (Apache-2.0): token compression of command output. Does not eliminate daily request limits.
7. `https://github.com/anthropics/skills`: first-party skill exemplars; do not bulk-install unreviewed skills.
8. `https://huggingbay.xyz/es` is inaccessible to our web inspection. Public metadata at `https://huggingbay.xyz/api/mcp` declares artifact lookup and model decision tools and an experimental Bay Run service. Third-party trust services report warning signals; DO NOT install remote MCP in DISI, download binaries, submit HUMINT, or provide API keys until independently audited. It is not proven to supply unlimited safe inference.
9. `https://thehuggingbay.io/` is a different openly licensed torrent/magnet index, not verified as the same operator. It offers few audio and embedding model listings; not a substitute for a coding LLM.

## Priority for DISI
- Phase 1: install this read-only GitHub gateway; validate it with owner-only issue; one limited free provider, zero-sum budget.
- Phase 2: introduce user-approved alternative keys on demand, based on licensing, privacy and real tool-calling smoke tests (do not guess current quotas).
- Phase 3: use a capable local/server Ollama instance to remove inference token billing; hardware resources and electricity are still finite.
- Efficiency: no unnecessary LLM calls for mechanical checks, hard cap retries, local filtering of CI logs, compact evidence-oriented skill files.
- Absolutely no account farming, credential pooling or rate-limit evasion.