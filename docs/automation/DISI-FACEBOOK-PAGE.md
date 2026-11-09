# DISI: Facebook Reels for Media News HQ

Page: https://www.facebook.com/medianewshq

This initial integration is a read-only Meta Graph API preflight.
It does not publish, schedule or upload videos. No credentials are configured
by this change.

## Official Meta API (for the separately authorized upload phase)

Meta's Reels Publishing API for Facebook Pages:
1. POST /{page-id}/video_reels with upload_phase=start.
2. Send MP4 to returned rupload.facebook.com upload_url.
3. POST /{page-id}/video_reels with upload_phase=finish and
   video_state=PUBLISHED only after separate owner authorization.
4. Confirm status before reporting success. Do not blindly retry uploads.

Official Meta Facebook API Postman documentation:
https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api

## To connect the page

1. Create/select a Meta Developers app and request pages_show_list,
   pages_read_engagement and pages_manage_posts for a Page administrator
   authorized to create content. App mode, roles and Meta review can affect access.
2. Obtain a valid Page Access Token for Media News HQ via Meta's
   /me/accounts endpoint and the numeric Page ID.
3. Add GitHub Actions repository secret FACEBOOK_PAGE_ACCESS_TOKEN in
   https://github.com/ledeghar/MoneyPrinterTurbo/settings/secrets/actions.
4. Add Actions repository variable FACEBOOK_PAGE_ID (numeric Page ID).
5. Manually execute workflow 'DISI - Check Facebook Page connection (no uploads)'.
   Compare the returned Page name/link/ID to Media News HQ.

Tokens must not be added to commits, tickets, artifacts or chat.
This check requires a Page token; the public page URL alone is insufficient.
A green check verifies token and matching Page ID, NOT actual posting rights.

Future implementation requires explicit manual approval, video validation,
duplicate protection, retries/status handling, scheduled publishing and
rights/attribution checks. Do not silently enable public publishing.
