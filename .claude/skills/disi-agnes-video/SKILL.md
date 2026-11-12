---
name: disi-agnes-video
description: Generate optional, explicitly requested Agnes AI video clips for DISI using the repository's safe bridge. Use for Agnes model setup, a single AI scene, or video-generation diagnostics. Do not use this skill to publish.
---

# DISI Agnes Video — Claude Code instructions

This is a DISI-specific adapter informed by the MIT-licensed Agnes Video Generator and its agent skill:
- https://github.com/lcy362/agnes-video-generator
- https://github.com/lcy362/agnes-video-generator-skills
- Agnes API docs: https://agnes-ai.com/en/docs/overview

Read `disi-agnes/README.md` before operating. Use `disi-agnes/agnes_video.py` rather than automatically installing unreviewed third-party code. This integration calls Agnes's HTTPS video API directly.

## Routine

1. Obtain an editorially cleared prompt. **Never** transfer private HUMINT, private-source identifiers, phone evidence, confidential client material or uncleared copyrighted footage to a cloud model.
2. Classify all new visual material as **AI-generated reconstruction**. Do not imply AI depictions are authentic news footage or eyewitness images.
3. Ensure the prompt is between 12 and 2000 characters and relates to the required scenes. Use English prompts for the video model if useful, while preserving the source's claims.
4. Set `VIDEO_PROMPT` in the shell environment without committing it. Run `python disi-agnes/agnes_video.py --dry-run --seconds 5`; this uses no credits, network or credentials.
5. For an explicitly approved actual generation, provide `AGNES_API_KEY` only via a local environment variable or GitHub Actions secret and run `python disi-agnes/agnes_video.py --execute --seconds 5`. The bridge only permits `agnes-video-2.5-flash`, the currently advertised free model; pricing or availability can change.
6. Inspect the resulting MP4, JSON manifest and FFprobe metadata. If output is not portrait, reject it rather than passing as production-ready.
7. Import the reviewed clip **as an optional source asset** into the existing `mn-short-motion` V9 + FFmpeg pipeline. It is not a full DISI short and must not overwrite the master.
8. The final short needs original Media News → DISI outro (~3.5 s), synchronized subtitles, voice below 59 seconds total, 9:16 and ten audio tracks (es,en,fr,de,it,pt,ru,zh,ja,ar), with truthful license/provenance notes.
9. No automatic uploading, publishing, bulk contact or changes to DISIM. Publication still requires separate editorial approval.

## GitHub Actions

`.github/workflows/disi-agnes-video.yml` is manually triggered only. Default **execute=false** is an offline dry-run and is safe even without an Agnes account. For real generation, the owner must first configure repository secret `AGNES_API_KEY` and select **execute=true**. Do not request the token in chat or write it to source files.

If 401 / 429 / 503 occurs, report the actual failure class and do not change to a paid model, source or credential automatically. The promotional free queue may be saturated.

Current status must be evidenced by a completed GitHub run or artifact, not by the existence of this skill.
