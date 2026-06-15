# Bishwa Medicare — Sales Tracking System

AI-powered field tracker for medical reps. Python/Flask + scikit-learn + MariaDB. Optional Drupal 10 frontend (custom `sales_tracker` module + `bishwa` theme).

```
Browser ─▶ Drupal (Apache :8080)  ─┐
                                    ├─▶ Flask (:5000) ─▶ MariaDB (:3306)
Browser ─▶ Flask UI (:5000) ───────┘     + geopy + scikit-learn
```

The Flask UI at `http://127.0.0.1:5000` works standalone — Drupal is optional.

## Prerequisites

| Tool | Version |
|---|---|
| XAMPP (MariaDB + Apache, PHP 8.2) | 8.2.x |
| Python | 3.10 – 3.13 |
| Composer (only for Drupal) | 2.x |

## Quick start (Flask only)

```bash
# 1. Start XAMPP's MariaDB (XAMPP Control Panel → Start MySQL)

# 2. Create the DB
mysql -u root -e "CREATE DATABASE sales_tracker CHARACTER SET utf8mb4;"
mysql -u root sales_tracker < schema.sql
mysql -u root sales_tracker < schema_v2.sql
mysql -u root sales_tracker < india_geo_seed.sql

# 3. Python env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 4. Config
copy .env.example .env       # then edit if your DB creds aren't root/empty

# 5. Seed accounts + run
python seed_admin.py         # admin@example.com / admin123
python seed_shashekhar.py    # shashekhar / shashekhar123  (employee)
python app.py
```

Open `http://127.0.0.1:5000`. Sign in, or click **Create an account** to self-register.

## Default logins

| Username | Password | Role |
|---|---|---|
| `admin@example.com` | `admin123` | admin (sees `/admin`, `/proctor`) |
| `shashekhar` | `shashekhar123` | employee |

## Key URLs

- `/dashboard` — your day, check-ins
- `/plan` — declare today's plan
- `/visit` — log a visit
- `/history` — your past check-ins
- `/admin` — admin only
- `/proctor` — admin only, all-India rollups

## Drupal frontend (optional)

Only needed if you want the polished Drupal UI on top of Flask. See `drupal_module/sales_tracker/` and `drupal_theme/bishwa/`. Install Drupal 10 via Composer, then symlink (or copy) those folders into `web/modules/custom/` and `web/themes/custom/`. Enable with `drush en sales_tracker -y && drush theme:enable bishwa && drush config-set system.theme default bishwa -y`.

Apache must run on **port 8080** (not 80) to avoid conflicts on Windows. Set `Listen 8080` and `ServerName localhost:8080` in `C:\xampp\apache\conf\httpd.conf`.

## Demo data

```bash
python seed_demo.py       # 7 demo employees + plans + visits
python seed_districts.py  # one rep per district (~780 rows)
python remove_demo.py     # roll everything back
```

The seeders record what they insert in `_demo_data_ids`, so `remove_demo.py` deletes only seeded rows — real data is untouched.

## Project layout

```
sales_tracker/
├── app.py                   # Flask routes (auth, dashboard, checkin, visit, admin, proctor)
├── api*.py                  # JSON endpoints for Drupal (/api/*)
├── ai/matcher.py            # geo distance + fuzzy name match + reverse geocode
├── ai/anomaly.py            # IsolationForest anomaly detection
├── db.py, config.py         # MariaDB pool + env loading
├── schema*.sql              # DDL
├── seed_*.py, remove_demo.py
├── templates/               # Flask Jinja templates
├── static/                  # CSS only (no JS)
├── drupal_module/sales_tracker/    # Drupal 10 custom module
└── drupal_theme/bishwa/             # Drupal 10 custom theme
```

## .env

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=
DB_NAME=sales_tracker
FLASK_SECRET=change-me
API_KEY=change-me-too        # shared with Drupal
GEO_THRESHOLD_KM=5
MATCH_THRESHOLD=0.6
```

## Troubleshooting

- **Port 5000 already in use** — change Flask port in `app.py` (`app.run(port=5001)`).
- **Geolocation button does nothing** — turn on Windows Settings → Privacy → Location, and allow location for the site in your browser. The status line below the button now shows the exact reason.
- **Corporate TLS errors on git/composer** — run `git config --global http.schannelCheckRevoke false` once. For Composer, merge Windows CA certs into PHP's `curl-ca-bundle.crt`.
- **Drupal Twig error `{% elif %}`** — Twig uses `{% elseif %}`. Already fixed in this repo.

## Security note

This is a local-dev/demo setup. Hashes are pbkdf2-sha256 via Werkzeug; sessions are signed with `FLASK_SECRET`. There's no HTTPS, no rate limiting, and the API key is shared via env. Don't expose to the public internet without putting it behind a real WSGI server + TLS + a real auth layer.
