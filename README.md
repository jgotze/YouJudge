# YouJudge

A Django web application for running competitions with weighted scoring, real-time leaderboards, judge invitations, and a client subscription system.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL |
| Frontend | Bootstrap 5 |
| Task Queue | Celery + Redis |
| Email | Gmail SMTP |

---

## Quick Start

**Prerequisites:** Python 3.10+, PostgreSQL, Redis

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
copy .env.example .env       # Windows
cp .env.example .env         # Linux / Mac
# Edit .env — fill in DB credentials, email app password, secret key

# 4. Create the database
psql -U postgres -c "CREATE DATABASE youjudge_db;"

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver
```

Open <http://127.0.0.1:8000>

> **Windows shortcut:** run `.\setup.ps1` to do steps 1–3 automatically.

---

## Project Structure

```text
YouJudge/
├── manage.py
├── requirements.txt
├── .env.example                 ← copy to .env and fill in your values
├── setup.ps1                    ← Windows setup script
│
├── youjudge/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── middleware.py            ← subscription enforcement
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── core/                   ← shared SoftDeleteModel base
│   ├── accounts/               ← auth, profiles, paywall, subscription
│   ├── competitions/           ← competition CRUD, judge invites, entries
│   ├── scoring/                ← judging, scores, leaderboard
│   └── notifications/          ← in-app + email notifications
│
└── templates/
    ├── base.html
    ├── landing.html
    ├── accounts/
    ├── competitions/
    ├── scoring/
    └── notifications/
```

---

## Key Features

### Competitions

- Create competitions with custom scoring criteria (weighted 1–5)
- Add entries with files, images, or video links
- Set competition status: draft → active → closed

### Judging

- Invite judges by email (existing users or new invites)
- Judges score each entry per criterion (0–10 dropdown)
- Progress tracking per judge

### Leaderboard

- Auto-calculated weighted scores
- Live rankings updated on each score submission
- CSV export

### Scoring Formula

```text
weighted_score  = (score_value / 10) × criteria_weight
entry_total     = SUM(weighted_score for all criteria)
```

Example:

| Criteria | Weight | Score | Weighted |
| --- | --- | --- | --- |
| Creativity | 5 | 8 | 4.0 |
| Technical | 3 | 10 | 3.0 |
| Presentation | 2 | 6 | 1.2 |
| **Total** | | | **8.2** |

### Subscription / Paywall

- Users are judges by default (free)
- Becoming a **Client** unlocks creating competitions
- Paywall is gated by `user.is_subscribed`; `SubscriptionMiddleware` enforces it on every request
- Judges with active assignments bypass the paywall for judging routes only

### Soft Deletes

All core models extend `SoftDeleteModel`. Calling `.delete()` sets `deleted_at` rather than removing the row. Use `.hard_delete()` for permanent removal.

---

## URL Reference

| URL | Description |
| --- | --- |
| `/` | Landing page |
| `/accounts/register/` | Create account |
| `/accounts/login/` | Login |
| `/accounts/profile/` | Account settings |
| `/accounts/paywall/` | Subscription paywall |
| `/dashboard/` | My competitions |
| `/dashboard/<uuid>/` | Competition detail |
| `/dashboard/my-judges/` | All judges across competitions |
| `/scoring/` | Judging dashboard |
| `/scoring/competition/<uuid>/` | Score entries in a competition |
| `/scoring/leaderboard/<uuid>/` | Competition leaderboard |
| `/notifications/` | Notifications list |
| `/api/docs/` | Swagger API docs |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in these values:

| Variable | Description |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` in development, `False` in production |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL host (default `localhost`) |
| `DB_PORT` | PostgreSQL port (default `5432`) |
| `EMAIL_HOST_USER` | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (16 chars — not your account password) |
| `DEFAULT_FROM_EMAIL` | From address shown in emails |
| `REDIS_URL` | Redis connection URL for Celery |
| `SITE_URL` | Base URL of the site (used in email links) |

---

## License

MIT
