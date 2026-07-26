# splanly Development Session Summary

## Latest Update: July 22, 2026

### Supabase Data Loss Incident
- **Root cause:** Test cleanup fixture (`tests/conftest.py`) ran against production DB with no environment guard
- **Impact:** Wiped assignments, leaves, engagements, clients, team_members (users survived due to FK constraint)
- **Fixes applied:**
  - Added `TESTING` guard to `conftest.py` and `seed_data.py`
  - Added `TESTING: bool = False` to `app/config.py`
  - Fixed delete order (FirmUser before User)
  - Fixed seed script to auto-create Firm if none exists
- **Learnings doc:** `Downloads/supabase_data_loss_learnings.md`

---

## Previous Sessions Summary

### Multi-Tenancy & Approval System (July 2026)
- Added Firm, Branch, FirmUser models for multi-tenancy
- Implemented approval rules and approval requests system
- Added extension requests for allocation extensions
- Firm-scoped all data with firm_id FKs

### Licensing System (July 2026)
- Added SuperAdmin model (platform-level admin)
- License key generation with HMAC signing
- Standard/Enterprise tiers with user/member limits
- LicenseMiddleware blocks access for expired licenses
- Trial/grace/expired states

### API v1 for Next.js Frontend (July 2026)
- JWT authentication (access + refresh tokens)
- Full JSON API mirroring all web routes
- Endpoints: auth, dashboard, team-members, clients, engagements, assignments, leaves, approvals, extensions

### OTP & Invitation System (July 2026)
- 6-digit email OTP for registration and login
- Rate limiting on OTP resend
- Token-based invitations with bulk CSV support
- Role promotion and super admin transfer

### FrankenUI Migration (July 2, 2026)
- Updated all templates to FrankenUI 2.x
- Flash message positioning, searchable dropdowns
- Assign Staff page, engagement detail page
- Deployed to Render

---

## Key URLs
- **Render:** https://pm-tool-5pg6.onrender.com
- **Custom Domain:** https://pkf.skilledca.in
- **Login:** /auth/login
- **Dashboard:** /dashboard

---

## Environment Variables
- `DATABASE_URL` — Neon PostgreSQL connection string
- `SECRET_KEY` — App secret key
- `ENV` — production/development
- `TESTING` — false (must be true to run tests against DB)
- `LICENSE_SIGNING_KEY` — HMAC key for license validation
- SMTP config (Zoho: smtp.zoho.com:587)
- MS365 OAuth config (optional)
