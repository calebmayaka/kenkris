# KenKris Logistics website

Django site for KenKris Logistics: customs brokerage, freight forwarding and trade training.
Server-rendered from the original Claude Design export (kept in `design/` for reference).

## What's where

| Path | Purpose |
| --- | --- |
| `config/` | Django settings (all config from `.env`), URLs, WSGI |
| `website/models.py` | Site settings, stats, courses, quote requests |
| `website/content.py` | Fixed page copy (services, process, corridors, documents) |
| `website/templates/website/` | Page templates |
| `website/static/website/` | CSS, JS, self-hosted fonts |
| `deploy/` | systemd unit and Caddyfile |

## Admin panel (`/admin/`)

The staff-facing panel is the `panel` app — a custom UI, not the Django admin.

- **Inquiries** (all staff): filter by status, search, open one to reply by email/call/WhatsApp, update status and internal notes.
- **Users** (administrators only): create users, change role (Staff / Administrator), deactivate, set passwords.
- **Change password**: every user, from the sidebar.

Safety rails: login lockout after 10 failures per IP for 15 minutes; you can't deactivate or demote yourself; the last active administrator can't be removed.

Create the first administrator from the shell: `.venv/bin/python manage.py createsuperuser`.

## Editing content (hidden Django admin)

Site settings, stats and courses are still edited in the built-in Django admin, which is hidden:
it's only mounted at `/<DJANGO_ADMIN_URL>` (a random path set in `.env`) and only administrators can sign in.
Leave `DJANGO_ADMIN_URL` empty to switch it off completely.

- **Site settings**: phone numbers, email, address, hours, and where quote emails go
- **Stats**: figures in the "Why KenKris" grid; tick *show in hero* to also show in the banner
- **Courses**: only published courses with a future start date appear (max 4)
- **Quote requests**: every form submission, with status and internal notes

Services, the process steps, corridors and document requirements live in `website/content.py`.

## Local setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # fill in values
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createcachetable
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py test website
```

## Deploying an update

```bash
cd ~/kenkris && git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl reload kenkris
```

## Quote form protections

CSRF token, a hidden honeypot field, and a per-IP limit (`QUOTE_RATE_LIMIT_PER_HOUR`, default 5).
If the notification email fails, the request is still saved and shows `email_sent = False` in the admin.
