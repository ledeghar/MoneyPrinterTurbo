# MN Short — automatic cloud video production

## What it does

A GitHub Actions runner (not the owner's Windows laptop) retrieves a recent technology RSS item, uses Gemini to draft two attributed scripts (Spanish + English), and executes MoneyPrinterTurbo CLI to create two 9:16 MP4 videos with Pexels footage, Edge TTS narration, subtitles and random background music. Output MP4 files carry date, language and headline in their filenames. Finished files are attached to the GitHub Actions run as artifacts for editorial review. A separate manual input can send ONE Spanish MP4 to YouTube as unlisted through the user's existing Upload-Post profile.

## Required before first run

In GitHub repository Settings → Secrets and variables → Actions, create repository secrets:
- `GEMINI_API_KEY` — Google AI Studio Gemini API key. Any associated charges/rate limits depend on your Google API plan.
- `PEXELS_API_KEY` — Pexels stock-video API key. This can be the same key already used locally, entered directly in GitHub, never sent over chat.
- `UPLOAD_POST_API_KEY` — existing Upload-Post account API key (no new YouTube OAuth authorization required for this route). Profile name: `Medianews`.

No personal GitHub token or Claude subscription is required for rendering. To run manually choose Actions → MN Short → Run workflow after the workflow is merged to main. The first run should leave `upload_unlisted` unchecked to validate cloud rendering. After inspecting output, a manually approved run with `upload_unlisted=true` uploads only the Spanish MP4 as **unlisted**, consuming one Upload-Post quota slot. By default there is no uploading and no schedule during the pilot.

## Important operational boundaries

- **No public YouTube posting yet.** The workflow can perform an explicitly selected unlisted Spanish-video test using the existing Upload-Post connection. Upload-Post's free plan has a 10 uploads/month limit in the user's current account, and a future direct YouTube OAuth integration requires separate authorization. Do not authorize public unattended publishing before quality checks, metadata/rights review and consent.
- **No daily schedule during pilot.** The workflow is manually triggered only. After the production and upload checks pass, add a scheduled trigger on the default branch; scheduled GitHub Actions can be delayed.
- **News verification** is limited to a single attributed RSS excerpt; no independent corroboration is claimed. The generator is instructed to skip insufficient source material. The resulting script is not independently verified by code and therefore needs editorial review.
- **Video quality** is not guaranteed before running against the real API keys. Initial audio levels are 150% voice / 10% background music and must be checked in an actual render.
- GitHub workflow artifact storage is quota-limited and outputs expire after 3 days; it is not a permanent video archive. A later NAS or object storage connection is necessary for retention.
- Google/GitHub/Pexels service quotas and terms still apply. Avoid publishing the same story repeatedly; stateful deduplication must be added before enabling unattended publication.

## Next technical tasks before true unattended production

1. Test one complete manual Actions run and inspect the two MP4s.
2. Calibrate narration/music balance and add automatic audio QA.
3. Add topic deduplication, multi-source corroboration and durable archiving.
4. Test the already-connected Upload-Post profile with one manually approved unlisted upload. Add duplicate prevention and quota checks; then authorize public automation or migrate to direct YouTube OAuth for higher volumes.
