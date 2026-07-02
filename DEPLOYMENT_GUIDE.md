# StaffPlan Deployment & 2FA Guide

## Part 1: Deploy to Render

### Prerequisites
- GitHub account with the `pm-tool` repository
- Render account (free at [render.com](https://render.com))
- Supabase database (already set up)

---

### Step 1: Push Latest Changes to GitHub

```bash
cd pm-tool
git add .
git commit -m "fix: CSRF token and template issues"
git push origin main
```

---

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New** → **Web Service**
3. Connect your GitHub account if not already connected
4. Select the `pm-tool` repository

---

### Step 3: Configure the Web Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `staffplan` (or your preferred name) |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` (or paid for production) |

---

### Step 4: Add Environment Variables

Click **Advanced** → **Add Environment Variable** for each:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql://postgres...@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres` | Your Supabase connection string |
| `SECRET_KEY` | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` | **Must be unique and secret!** |
| `ENV` | `production` | |

**Optional (add later):**

| Variable | Value | Notes |
|----------|-------|-------|
| `MS365_TENANT_ID` | Your Azure AD tenant ID | For OAuth |
| `MS365_CLIENT_ID` | Your Azure AD app client ID | For OAuth |
| `MS365_CLIENT_SECRET` | Your Azure AD app secret | For OAuth |
| `MS365_REDIRECT_URI` | `https://your-app.onrender.com/auth/callback` | OAuth callback URL |
| `SMTP_HOST` | `smtp.gmail.com` or your SMTP server | For email notifications |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | Your SMTP username | |
| `SMTP_PASSWORD` | Your SMTP password | |
| `SMTP_FROM_EMAIL` | `noreply@yourdomain.com` | |

---

### Step 5: Deploy

1. Click **Create Web Service**
2. Wait for the build to complete (2-5 minutes)
3. Check the logs for any errors
4. Once deployed, click the URL to access your app

---

### Step 6: Create Admin User

After deployment, you need to create an admin user in the database. You can do this via:

**Option A: Render Shell**
1. Go to your web service in Render
2. Click **Shell** in the left sidebar
3. Run:
```bash
python -c "
from app.database import SessionLocal
from app.models.models import User, TechnicalRole
from app.services.auth_service import hash_password
db = SessionLocal()
user = User(email='admin@yourcompany.com', display_name='Admin', technical_role=TechnicalRole.admin, is_active=True, password_hash=hash_password('your-secure-password'))
db.add(user)
db.commit()
print('Admin user created!')
"
```

**Option B: Local script against production DB**
```bash
# Set DATABASE_URL to production, then run:
python -c "
from app.database import SessionLocal
from app.models.models import User, TechnicalRole
from app.services.auth_service import hash_password
db = SessionLocal()
user = User(email='admin@yourcompany.com', display_name='Admin', technical_role=TechnicalRole.admin, is_active=True, password_hash=hash_password('your-secure-password'))
db.add(user)
db.commit()
"
```

---

## Part 2: Two-Factor Authentication (2FA)

### How 2FA Works

StaffPlan uses **TOTP (Time-based One-Time Password)** authentication, the same technology used by:
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password

**The flow:**

1. **Setup** (one-time per user):
   - App generates a unique secret key for the user
   - Secret is encoded into a QR code
   - User scans QR code with their authenticator app
   - Authenticator app stores the secret
   - User enters a code from the app to verify setup

2. **Login** (every time after setup):
   - User enters email + password
   - If 2FA is enabled, redirect to 2FA page
   - User enters 6-digit code from authenticator app
   - App verifies the code is correct (within 30-second window)
   - User is logged in

---

### Enabling 2FA for Your Account

1. **Log in** to StaffPlan with your admin account

2. **Go to 2FA Setup**:
   - Click your name in the top-right corner
   - Click **Setup 2FA**

3. **Scan the QR Code**:
   - Open your authenticator app (Google Authenticator, Microsoft Authenticator, etc.)
   - Tap **Add account** or **+**
   - Scan the QR code shown on screen
   - The app will show a 6-digit code

4. **Verify Setup**:
   - Enter the 6-digit code from your authenticator app
   - Click **Enable 2FA**
   - You'll see a confirmation message

5. **Test Login**:
   - Log out
   - Log in with email + password
   - You'll be redirected to the 2FA page
   - Enter the 6-digit code from your authenticator app
   - You're in!

---

### Managing 2FA for Users

As an admin, you can:

**View 2FA status:**
- Go to **Users** page
- The list shows which users have 2FA enabled

**Disable 2FA for a user:**
- Currently requires direct database access
- Run:
```sql
UPDATE users SET totp_enabled = false, totp_secret = NULL WHERE email = 'user@example.com';
```

**Force 2FA for specific roles:**
- This would require code changes
- Currently 2FA is optional per user

---

### How TOTP Works (Technical Details)

The TOTP algorithm (RFC 6238):

1. **Secret Generation**:
   - App generates a random 160-bit (32-character) base32 secret
   - This secret is stored encrypted in the database

2. **QR Code**:
   - Format: `otpauth://totp/StaffPlan:user@email.com?secret=XXXX&issuer=StaffPlan`
   - This is what gets encoded into the QR code

3. **Code Generation** (in authenticator app):
   - Current time (Unix timestamp) divided by 30 (30-second windows)
   - HMAC-SHA1 of the time counter using the secret
   - Take last 4 bits of HMAC to determine offset
   - Extract 6 digits starting at offset

4. **Verification** (on server):
   - Server calculates the same expected code
   - Compares user input with expected code
   - Allows ±1 window (30 seconds before/after) for clock drift

---

### Security Best Practices

1. **Backup Codes**: Consider implementing backup codes for account recovery
2. **Rate Limiting**: The 2FA page should have rate limiting to prevent brute force
3. **Session Timeout**: After failed 2FA attempts, clear the pending session
4. **Secret Storage**: The TOTP secret is stored in the database - consider encrypting at rest

---

## Troubleshooting

### Common Issues

**"Invalid CSRF token" on login:**
- Clear your browser cookies
- Try incognito/private mode
- Ensure cookies are enabled

**"Invalid input value for enum" error:**
- This was a bug with enum handling - should be fixed now
- Pull the latest code

**2FA codes not working:**
- Check server time is accurate (TOTP depends on time)
- Try the code quickly (codes expire in 30 seconds)
- Ensure your authenticator app's time is synced

**Email notifications not sending:**
- SMTP credentials not configured
- Check the Outbox page (admin only) for pending/failed emails

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Create admin user
3. ✅ Enable 2FA for your admin account
4. ✅ Create team members
5. ✅ Create clients and engagements
6. ✅ Start assigning work!

For questions or issues, check the logs in Render dashboard.