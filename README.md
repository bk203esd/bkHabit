# DayFlow

Personal day manager built with Django. Each user manages their own calendar, alarms, and notes.

## Features

- **Accounts** — register, then wait for a superuser to approve (or deny). Denied usernames/emails stay reserved.
- **Calendar** — all-day and timed events, optional recurrence (daily / weekly / monthly), month / week / day views.
- **Alarms** — one-time (removed after firing) or weekly on selected weekdays, with browser notifications while the app is open.
- **Notes** — Markdown content, folders, tags, and pin support.
- **Themes** — Light, Dark, and Kawaii (pink pastels), plus per-user timezone.

UI copy is in English. User-authored titles and note bodies stay as written.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Registration flow

1. A visitor registers (account stays inactive / pending).
2. A superuser opens **Registrations** in the nav and approves or denies.
3. Only approved users can sign in.

## Project layout

```
dayflow/     # project settings
accounts/    # auth, profiles, themes, approval queue
events/      # calendar
alarms/      # alarms + notification endpoints
notes/       # notes, folders, tags
templates/   # shared templates
static/      # CSS and alarm notification JS
```
