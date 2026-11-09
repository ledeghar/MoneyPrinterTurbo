# MN Short — automatic cloud video production

## What it does

A GitHub Actions runner (not the owner's Windows laptop) retrieves a recent technology RSS item, uses Gemini to draft two attributed scripts (Spanish + English), and executes MoneyPrinterTurbo CLI to create two 9:16 MP4 videos with Pexels footage, Edge TTS narration, subtitles and random background music. Output MP4 files carry date, language and headline in their filenames. Finished files are attached to the GitHub Actions run as private-to-the-workflow artifacts for editorial review.

## Required before first run

In GitHub repository Settings → Secrets and variables → Actions, create repository secrets:
- `GEMINI_API_KEY` — Google AI Studio Gemini API key. Any associated charges/rate limits depend on your Google API plan.
- `PEXELS_API_KEY` — Pexels stock-video API key. This can be the same key already used locally, entered directly in GitHub, never sent over chat.

No personal GitHub token or Claude subscription is required for rendering. To run manually choose Actions → MN Short → Run workflow after the workflow is merged to main.

## Important operational boundaries

- **No YouTube posting yet.** The first run is review-only. Upload-Post's free plan has a 10 uploads/month limit in the user's current account, and a future direct YouTube OAuth integration requires separate authorization. Do not publish news before quality checks, metadata/rights review and consent for automatic publication.
- **Daily schedule** uses 08:17 UTC; actual execution may be delayed by GitHub Actions. Schedules activate only on the default branch. Unmerged PR files do not schedule jobs.
- **News verification** is limited to a single attributed RSS excerpt; no independent corroboration is claimed. The generator is instructed to skip insufficient source material. The resulting script is not independently verified by code and therefore needs editorial review.
- **Video quality** is not guaranteed before running against the real API keys. Initial audio levels are 150% voice / 10% background music and must be checked in an actual render.
- GitHub workflow artifact storage is quota-limited and outputs expire after 3 days; it is not a permanent video archive. A later NAS or object storage connection is necessary for retention.
- Google/GitHub/Pexels service quotas and terms still apply. Avoid publishing the same story repeatedly; stateful deduplication must be added before enabling unattended publication.

## Next technical tasks before true unattended production

1. Test one complete Actions run and inspect the two MP4s.
2. Calibrate narration/music balance and add automatic audio QA.
3. Add topic deduplication, multi-source corroboration and durable archiving.
4. Connect YouTube via OAuth upload credentials or a suitable upload service, test unlisted upload, and only then authorize public auto-publication.
