# DISI / MNShort — Single-Spanish review workflow

This controlled test follows the successful 10-language Remotion demo.
It keeps the established MNShort wordmark and 'Media News by DISI' footer.
Instead of producing ten MP4s, it renders **one Spanish** 1080x1920 video,
either a demo or a live sourced story (RSS/Gemini).

## User action

Actions -> `MNShort - One Spanish Remotion preview (review only)` ->
Run workflow -> main -> `live` -> Run workflow.

- `live` requests a new RSS-backed story and the Spanish narration using
  the existing `GEMINI_API_KEY` repository secret.
- `demo` costs no Gemini request and checks branding/format only.
- No other-language translation or ten-video render occurs in either mode.
- The result is an MP4 plus editorial source, audio timing and credit manifest
  stored as an Actions artifact for seven days.
- This workflow cannot publish and only has `contents: read` permissions.

## Editorial acceptance

Verify the original source and date, every named person and location, rights
and correct attribution for imagery, scene/narration synchrony and branding.
A Wikimedia search match is not, by itself, identity verification or a
grant of reproduction rights. Review actual video before any public release.

No automatic or paid distribution is enabled by this workflow.
