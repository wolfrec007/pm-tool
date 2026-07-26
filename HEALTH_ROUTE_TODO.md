# Health Route — Status & Notes

## Current State
`GET /health` returns `{"status": "ok"}` (15 bytes, application/json).
- No DB, no session, no auth required
- Exempt from LicenseMiddleware

## Previous Issue (Resolved)
Cron job was hitting `/` (35 KB landing page) instead of `/health`, causing "response too large" errors. Also, `x-render-routing: no-deploy` indicated the app was down when Cloudflare returned its own error page.

**Fix:** Point cron at `https://<domain>/health`, not `/`.

## Test Fixture FK Issue (Fixed)
`tests/conftest.py` `clean_tables` fixture was deleting `User` before `FirmUser`, causing FK violations. Fixed by:
1. Adding `FirmUser` to delete order before `User`
2. Adding `TESTING=true` safety guard to prevent running against production
