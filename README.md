# YouJudge

A Django web application for running competitions with weighted scoring, real-time leaderboards, judge invitations, and a client subscription system.

**New here?** See [QUICKSTART.md](QUICKSTART.md) for the full setup guide (0 → 100).

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL |
| Frontend | Bootstrap 5 (CDN) |
| Task Queue | Celery + Redis |
| Email | Gmail SMTP (console backend in dev) |

---

## Key Features

### Competitions

- Create competitions with custom icon, colour, start/end dates
- Add scoring criteria with weights (1–5)
- Organise entries into optional categories
- Status workflow: Draft → Active → Closed

### Judging

- Invite judges by email — existing users or new (they receive a signup invite)
- Judges score each entry per criterion (0 to `max_score`)
- Real-time progress tracking per judge

### Leaderboard and Scoring Formula

```text
weighted_score  = score_value × criteria_weight
entry_total     = SUM(weighted_score for all criteria scored by all judges)
```

Results export to a styled Excel file with a bar chart on Sheet 2.

### Subscription / Paywall

- New users are **judges** by default (free tier)
- To create competitions a user must be **subscribed** (`user.is_subscribed = True`)
- In development use `/accounts/paywall/` to activate with the mock payment
- `SubscriptionMiddleware` enforces this on every request; judges bypass it for scoring routes

### Soft Deletes

All core models extend `SoftDeleteModel`. Calling `.delete()` sets `deleted_at` rather than removing the row. Use `.hard_delete()` for permanent removal.

---

## Project Structure

```text
YouJudge/
├── manage.py
├── requirements.txt
├── .env.example              ← copy to .env and fill in your values
├── setup.ps1                 ← Windows one-step setup script
│
├── youjudge/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── middleware.py         ← subscription paywall enforcement
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── core/                 ← shared SoftDeleteModel base
│   ├── accounts/             ← auth, profiles, email verification, paywall
│   ├── competitions/         ← competition CRUD, judge invites, entries, categories
│   ├── scoring/              ← judging, weighted scores, leaderboard, Excel export
│   └── notifications/        ← in-app + email notifications
│
├── static/                   ← your custom static files (create this directory)
├── media/                    ← uploaded files (avatars, entry attachments)
└── templates/
    ├── base.html
    ├── landing.html
    ├── accounts/
    ├── competitions/
    ├── scoring/
    └── notifications/
```

---

## URL Reference

| URL | Description |
| --- | --- |
| `/` | Landing page |
| `/accounts/register/` | Create account |
| `/accounts/login/` | Login |
| `/accounts/verify/<token>/` | Email verification link |
| `/accounts/profile/` | Edit profile and change password |
| `/accounts/paywall/` | Subscription upgrade page |
| `/dashboard/` | My competitions |
| `/dashboard/create/` | New competition |
| `/dashboard/<uuid>/` | Competition detail (entries, judges, criteria) |
| `/dashboard/my-judges/` | All judges across your competitions |
| `/scoring/` | Judge dashboard |
| `/scoring/competition/<uuid>/` | Score all entries in a competition |
| `/scoring/leaderboard/<uuid>/` | Live leaderboard |
| `/scoring/leaderboard/<uuid>/export/` | Download Excel export |
| `/notifications/` | Notifications inbox |
| `/api/docs/` | Swagger API documentation |
| `/admin/` | Django admin |

---

## License

MIT
