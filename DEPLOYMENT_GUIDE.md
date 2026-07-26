# splanly Deployment & Setup Guide

## Part 1: Deploy to Render

### Prerequisites
- GitHub account with the `pm-tool` repository
- Render account (free at [render.com](https://render.com))
- Neon PostgreSQL database

---

### Step 1: Push Latest Changes to GitHub

```bash
cd pm-tool
git add .
git commit -m "your commit message"
git push origin main
```

---

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New** → **Web Service**
3. Connect your GitHub account
4. Select the `pm-tool` repository

---

### Step 3: Configure the Web Service

| Setting | Value |
|---------|-------|
| **Name** | `staffplan` |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free or paid for production |

---

### Step 4: Add Environment Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql://...` | Neon PostgreSQL connection string |
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` | Must be unique |
| `ENV` | `production` | |
| `LICENSE_SIGNING_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` | For license validation |

**Optional:**

| Variable | Value | Notes |
|----------|-------|-------|
| `MS365_TENANT_ID` | Azure AD tenant ID | For OAuth |
| `MS365_CLIENT_ID` | Azure AD app client ID | For OAuth |
| `MS365_CLIENT_SECRET` | Azure AD app secret | For OAuth |
| `MS365_REDIRECT_URI` | `https://your-app.onrender.com/auth/callback` | OAuth callback |
| `SMTP_HOST` | `smtp.zoho.com` | For emails |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | Your SMTP username | |
| `SMTP_PASSWORD` | Your SMTP password | |
| `SMTP_FROM_EMAIL` | `noreply@yourdomain.com` | |

---

### Step 5: Deploy

1. Click **Create Web Service**
2. Wait for build to complete (2-5 minutes)
3. Check logs for errors
4. Access your app at the Render URL

---

### Step 6: Create Admin User

After deployment, create a super admin via Render Shell:

```bash
python -c "
from app.database import SessionLocal
from app.models.super_admin import SuperAdmin
from app.services.auth_service import hash_password
db = SessionLocal()
sa = SuperAdmin(email='admin@yourcompany.com', display_name='Admin', password_hash=hash_password('your-secure-password'), is_active=True)
db.add(sa)
db.commit()
print('Super admin created!')
"
```

---

## Part 2: Authentication Methods

### Password + OTP (Default)
1. User registers with email
2. Domain matched to firm
3. OTP sent to email for verification
4. User sets password
5. Login: password → OTP verification

### 2FA (TOTP) — Optional per firm
- Enable in Admin Settings → Auth Method
- User scans QR code with authenticator app
- Login: password → 6-digit TOTP code

### MS365 OAuth — Optional
- Configure Azure AD app credentials in env vars
- Users click "Sign in with Microsoft"
- Auto-creates user and links to firm by domain

---

## Part 3: License Management

### License Tiers
| Tier | Users | Team Members | Features |
|------|-------|--------------|----------|
| Standard | 50 | 599 | Core features |
| Enterprise | 100 | 5000 | All features |

### Activate License
1. Go to `/license/activate`
2. Enter license key
3. Key is validated and firm is activated

### Trial Mode
New firms get a trial period. After expiry, access is blocked until license is activated.

---

## Troubleshooting

**"Invalid CSRF token" on forms:**
- Clear browser cookies
- Try incognito mode

**License middleware blocking access:**
- Check `/license/status` for license state
- Activate license if expired

**Email not sending:**
- Check SMTP config in env vars
- Check `/admin/outbox` for failed emails
- Email worker only starts if SMTP_HOST is configured

**Tests wiping production data:**
- Ensure `TESTING=false` in `.env`
- Safety guards prevent cleanup unless `TESTING=true`
