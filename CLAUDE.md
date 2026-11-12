# DISI / Media News — Claude Code project instructions (12Nov2026)

This project builds editorial videos and truthful book marketing for ALEPO and JARTUM. Use the repo's existing Remotion V9 and FFmpeg workflows; do not replace a working media pipeline with an untested one. Code in `.claude/agents/` defines specialist agents; `.claude/skills/disi-books/SKILL.md` is the repeatable orchestrator.

Non-negotiable:
- HUMINT and files from human sources remain primary inputs when provided; keep provenance. Public search is an auxiliary source, never substitute a human-source claim with invented OSINT.
- For book promotions distinguish reconstruction/reenactment from verified footage; do not invent quotes, testimonials, sales, awards, reader reviews or store availability.
- No secret keys, HUMINT documents or phone data in GitHub. No unsolicited bulk contact and no unauthorized publication.
- Shorts <59 s total including the original ~3.5 s Media News → DISI outro; preserve logos, 9:16, synchronized captions and the 10 audio languages (es,en,fr,de,it,pt,ru,zh,ja,ar).
- Keep named exports `<BOOK>_<campaign>_<YYYYMMDD>`, master MP4, references and licensing ledger, and separate legal rights for photos.
- Avoid paid APIs and compute by default. Do not assume connectivity or working credentials. Show a verifiable GitHub Actions result.
- Optimize for **qualified visits to Amazon** and conversion evidence, not vanity impressions.
- On YouTube Shorts, direct URLs in comments and Shorts descriptions are not clickable: use an approved channel profile link or a related long-form video with a link in its description. On LinkedIn/Facebook use a verified direct purchase page.
- `disi-book-marketing/catalog.json` lists provisional KDP ASINs. Do not represent their Amazon pages as verified until live checked in the intended marketplace.

Workflow: fact-check → offer and audience → script alternatives → storyboard and rights → generate technical brief → QA → editorial approval → distribution → measured conversion review.