# MN Short — automatic cloud video production

## What it does

A GitHub Actions runner (not the owner's Windows laptop) retrieves a recent technology RSS item, uses Gemini to draft two attributed scripts (Spanish + English), and executes MoneyPrinterTurbo CLI to create two 9:16 MP4 videos with Pexels footage, Edge TTS narration, subtitles and random background music. Output MP4 files carry date, language and headline in their filenames. Finished files are attached to the GitHub Actions run as artifacts for editorial review. A separate manual input can send ONE Spanish MP4 directly to YouTube as unlisted via the official YouTube Data API (OAuth), without using Upload-Post.

## Required before first run

In GitHub repository Settings → Secrets and variables → Actions, create repository secrets:
- `GEMINI_API_KEY` — Google AI Studio Gemini API key. Any associated charges/rate limits depend on your Google API plan.
- `PEXELS_API_KEY` — Pexels stock-video API key. This can be the same key already used locally, entered directly in GitHub, never sent over chat.
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` — direct Google OAuth authorization with `youtube.upload` scope. These are used only in the explicitly activated upload step. The Upload-Post API key is **not** required for the direct upload.

No personal GitHub token or Claude subscription is required for rendering. To run manually choose Actions → MN Short → Run workflow after the workflow is merged to main. The first run should leave `upload_unlisted` unchecked to validate cloud rendering. After inspecting output, a manually approved run with `upload_youtube_unlisted=true` uploads only the Spanish MP4 as **unlisted**, using the official YouTube Data API rather than Upload-Post. By default there is no uploading and no schedule during the pilot.

## Important operational boundaries

- **No public YouTube posting yet.** The workflow can perform one explicitly approved Spanish-video test as UNLISTED via the official YouTube API. Verify that the OAuth Google account selected the intended **MN Short channel**. Do not authorize unattended public posting before quality checks, metadata/rights review and consent.
- **OAuth Testing expires:** Google external OAuth apps in Testing issue refresh tokens that may expire after 7 days; move to an eligible production configuration before scheduling unattended uploads. YouTube scopes may require Google verification depending on the app and audience. Keep the app single-user until properly configured.
- **No daily schedule during pilot.** The workflow is manually triggered only. After the production and upload checks pass, add a scheduled trigger on the default branch; scheduled GitHub Actions can be delayed.
- **News verification** is limited to a single attributed RSS excerpt; no independent corroboration is claimed. The generator is instructed to skip insufficient source material. The resulting script is not independently verified by code and therefore needs editorial review.
- **Video quality** is not guaranteed before running against the real API keys. Initial audio levels are 150% voice / 10% background music and must be checked in an actual render.
- GitHub workflow artifact storage is quota-limited and outputs expire after 3 days; it is not a permanent video archive. A later NAS or object storage connection is necessary for retention.
- Google/GitHub/Pexels service quotas and terms still apply. Avoid publishing the same story repeatedly; stateful deduplication must be added before enabling unattended publication.

## Next technical tasks before true unattended production

1. Test one complete manual Actions run and inspect the two MP4s.
2. Calibrate narration/music balance and add automatic audio QA.
3. Add topic deduplication, multi-source corroboration and durable archiving.
4. Test one manually approved unlisted upload through direct YouTube OAuth. Verify destination channel, resolve OAuth Testing expiry, implement duplicate prevention and quota checks before authorizing public automatic publishing.
