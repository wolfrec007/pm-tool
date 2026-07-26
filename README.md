# splanly

Staffing & resource planning platform for CA firms.

## Tech Stack
- **Backend:** FastAPI + Jinja2 (server-rendered)
- **Database:** PostgreSQL (Neon)
- **Auth:** Password + OTP + 2FA + MS365 OAuth + JWT
- **Deployment:** Render

## Features
- Multi-tenant with firm/branch support
- Team member, client, engagement, assignment management
- Configurable approval gates for all operations
- 11 role-tiered reports with CSV export
- Licensing system (Standard/Enterprise tiers)
- Invitation system with bulk CSV support
- API v1 (JWT) for Next.js frontend
- Email outbox with async worker

## Quick Start
```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Documentation
- `CONTEXT.md` — Full project context for AI agents
- `DEPLOYMENT_GUIDE.md` — Deploy to Render
- `frontend_new.md` — API v1 reference for Next.js frontend
