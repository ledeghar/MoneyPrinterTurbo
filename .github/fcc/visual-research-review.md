# DISI / Media News: review the EXISTING dynamic visual search

You are a coding-review agent reporting to the DISI technical coordinator.
Read files in this checked-out MoneyPrinterTurbo repository. Do NOT edit files,
run commands, initiate uploads, publish videos, or fetch external web pages.

Read these files (and any locally linked code needed to understand them):
- `scripts/mn_short_image_search.py`
- `scripts/mn_short_cloud.py`
- `.github/workflows/mn-short-image-search.yml`
- `.github/workflows/mn-short-cloud.yml`

Task: propose the smallest reliable improvements to make video images accurately
represent the **specific person, organization, site or event mentioned in each
new article**. A story about Jensen Huang should obtain a verified image of
Jensen Huang where one is needed, not treat an NVIDIA logo as his portrait.
Do not hardcode Jensen Huang or any other named subject in the production logic.

Review editorial subject extraction, query generation, candidate source evidence,
licensing/provenance, accidental misidentification, network SSRF protections,
fallback behavior, testability, and the integration boundary with video rendering.
A search hit or exact name match is not proof of image identity or usage rights.
Clearly distinguish proposed changes from features that already exist.

Return a Spanish Markdown report with:
1. Current pipeline (cite paths and relevant functions).
2. Three specific defects or limitations, with evidence in the files.
3. Minimal patch plan and precise files/functions to change.
4. Automated tests using mocked network results (no paid APIs).
5. Risks and evidence still needed before automatically using images.
6. A one-task implementation brief suitable for a follow-up pull request.

No repo modifications or GitHub writes. Do not claim you ran tests.
