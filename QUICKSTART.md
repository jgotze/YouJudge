# YouJudge — Quick Start Guide (0 → 100)

---

## Step 1 — Install Prerequisites

You need three things installed before starting.

#### Python 3.10+

- Windows: download from [python.org](https://www.python.org/downloads/) — check *Add to PATH* during install
- Verify: `python --version`

#### PostgreSQL 15+

- Windows: download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Remember the password you set for the `postgres` user during install
- Verify: `psql --version`

#### Redis (production only — skipped in development)

- Windows: use [Memurai](https://www.memurai.com/) (Redis-compatible) or WSL
- In development Redis is not required — Celery runs tasks synchronously

---

## Step 2 — Get the Code

```bash
git clone <your-repo-url>
cd YouJudge
```

---

## Step 3 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

Your terminal prompt should now show `(venv)`.

> **Windows shortcut:** run `.\setup.ps1` — this does steps 3–4 automatically and creates the required directories.

---

## Step 4 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 5 — Create the Database

Open a terminal and connect to PostgreSQL:

```bash
psql -U postgres
```

Then run:

```sql
CREATE DATABASE youjudge_db;
\q
```

If you get a connection error, make sure PostgreSQL is running.

- Windows: check *Services* → PostgreSQL is started, or run `pg_ctl start`

---

## Step 6 — Configure Environment Variables

Copy the example file and fill in your values:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and set these values:

```env
SECRET_KEY=replace-with-a-long-random-string
DEBUG=True

DB_NAME=youjudge_db
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432

# Leave these as-is for development (emails print to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

SITE_URL=http://localhost:8000
```

To generate a secret key, run:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 7 — Create Required Directories

These directories must exist for file uploads and static files:

```bash
# Windows
mkdir static media media\avatars media\entries

# macOS / Linux
mkdir -p static media/avatars media/entries
```

---

## Step 8 — Run Migrations

```bash
python manage.py migrate
```

Expected output: a list of `OK` lines for each migration.

---

## Step 9 — Create a Superuser

```bash
python manage.py createsuperuser
```

Enter an email and password. This account can access the Django admin at `/admin/`.

The superuser's `is_subscribed` field defaults to `False`. To enable competition creation, either:

- Go to `/accounts/paywall/` and click **Activate Client Account** (uses the mock payment flow), or
- In the Django admin, edit the user and check `is_subscribed`

---

## Step 10 — Start the Development Server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## First Time Walkthrough

### 1. Register and Verify

1. Go to `/accounts/register/` and create an account
2. In development, emails print to the terminal — look for the verification link in the server output
3. Copy the link from the terminal and open it in your browser to verify your email

### 2. Become a Client (to create competitions)

1. Go to `/accounts/paywall/` or click the Upgrade prompt
2. Click **Activate Client Account** — this runs a mock payment and sets `is_subscribed = True`

### 3. Create a Competition

1. Go to `/dashboard/` → **New Competition**
2. Fill in a title, start/end dates, and max score per criterion (e.g. 10)
3. Save — the competition starts as **Draft**

### 4. Add Criteria and Entries

On the competition detail page:

- **Criteria tab** → Add Criteria (title + weight 1–5). Weight controls how much a criterion influences the final score.
- **Entries tab** → Add entries (competitor names, optional categories)

### 5. Invite Judges

- **Judges tab** → enter an email address and click Invite
- Existing users get a notification; new emails get an invite to sign up
- Check **Add myself as judge** to score entries as the organizer

### 6. Activate the Competition

Click the status badge → select **Active**. Judges can now score.

### 7. Score Entries

Judges go to `/scoring/` → pick the competition → score each entry per criterion.

### 8. View Results

Go to `/scoring/leaderboard/<uuid>/` to see the live ranked leaderboard. Click **Export Excel** to download a styled spreadsheet.

---

## Running Celery (Production / Real Emails)

In development (`DEBUG=True`) Celery runs tasks synchronously — no Redis needed. To use real async email sending:

1. Start Redis (or Memurai on Windows)

2. Set in `.env`:

   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=you@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   REDIS_URL=redis://localhost:6379/0
   ```

3. Open a second terminal (with venv active) and run:

   ```bash
   celery -A youjudge worker -l info
   ```

Gmail requires an **App Password**, not your account password. Enable 2FA on your Google account, then go to *Security → App Passwords* to generate one.

---

## Environment Variables Reference

| Variable | Default | Description |
| --- | --- | --- |
| `SECRET_KEY` | *(required)* | Django secret key — generate a random one |
| `DEBUG` | `True` | Set to `False` in production |
| `DB_NAME` | `youjudge_db` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | *(required)* | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `EMAIL_BACKEND` | console backend | Use SMTP backend for real emails |
| `EMAIL_HOST_USER` | — | Gmail address |
| `EMAIL_HOST_PASSWORD` | — | Gmail App Password (16 chars) |
| `DEFAULT_FROM_EMAIL` | `noreply@youjudge.com` | From address in sent emails |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL for Celery (not needed in dev) |
| `SITE_URL` | `http://localhost:8000` | Base URL used in email links |

---

## Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate a strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Switch to real email backend (Gmail App Password or SendGrid)
- [ ] Start Redis and run a Celery worker
- [ ] Run `python manage.py collectstatic`
- [ ] Use a production WSGI server (Gunicorn) behind Nginx
- [ ] Enable HTTPS — `SECURE_SSL_REDIRECT` is auto-enabled when `DEBUG=False`
- [ ] Set up PostgreSQL backups
