# Sales Employee Tracking System

A two-stack app:

- **Backend** — Python **Flask** exposes `/api/*` JSON endpoints, talks to **MySQL** (XAMPP / MariaDB), runs the AI: smart location matching (`geopy` distance + `rapidfuzz` fuzzy text) and per-employee anomaly detection (`scikit-learn` IsolationForest).
- **Frontend** — **Drupal 11** custom module `sales_tracker` provides login, forms, dashboard, and admin pages. Drupal uses its built-in user system; on every API call it sends the logged-in user's email plus a shared API key. Flask auto-provisions employees in MySQL on first use.

```
Browser ─▶ Drupal 11 (PHP, XAMPP htdocs) ──HTTP+API key──▶ Flask 5000 ─▶ MySQL (XAMPP)
                                                            └─▶ AI (geopy / scikit-learn)
```

---

## 1. Prerequisites

- **XAMPP** (Apache + MariaDB + PHP 8.3+) — https://www.apachefriends.org/
- **Python 3.10+**
- **Composer** (for Drupal install) — https://getcomposer.org/

## 2. Start XAMPP

1. Open the XAMPP Control Panel → Start **Apache** and **MySQL**.
2. Open <http://localhost/phpmyadmin> to verify MySQL is up.

## 3. Create the database

In phpMyAdmin click **Import**, choose `sales_tracker/schema.sql`, click **Go**. (Or run `mysql -u root < schema.sql` from the XAMPP shell.)

## 4. Install & run the Python backend

```bash
cd "C:\self projects using claude\sales_tracker"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `API_KEY` to a long random string — you'll paste the same value into Drupal.

```bash
python seed_admin.py     # (optional, only needed for the Flask HTML fallback UI)
python app.py            # serves on http://127.0.0.1:5000
```

Smoke test: `curl http://127.0.0.1:5000/api/health` → `{"ok": true, "service": "sales_tracker"}`.

## 5. Install Drupal 11 in XAMPP

```bash
cd C:\xampp\htdocs
composer create-project drupal/recommended-project drupal
```

Create a MySQL database for Drupal in phpMyAdmin (e.g. `drupal11`), then open <http://localhost/drupal/web> and run the installer:

- Database type: MySQL/MariaDB
- DB name: `drupal11`, user: `root`, password: *(empty)*, host: `127.0.0.1`
- Finish the install, set an admin password.

## 6. Install the Sales Tracker module

Copy the module into Drupal's modules folder:

```bash
xcopy /E /I "C:\self projects using claude\sales_tracker\drupal_module\sales_tracker" ^
            "C:\xampp\htdocs\drupal\web\modules\custom\sales_tracker"
```

Then in Drupal:

1. **Extend** (`/admin/modules`) → search "Sales Tracker" → install.
2. **Configuration → Sales Tracker settings** (`/admin/config/sales-tracker/settings`):
   - Flask API URL: `http://127.0.0.1:5000`
   - Shared API key: *paste the same `API_KEY` from Flask `.env`*
3. **People → Permissions** (`/admin/people/permissions`):
   - Grant **Use sales tracker** to *authenticated user* (or a custom "Sales Employee" role).
   - Grant **Administer sales tracker** to *administrator* (or a custom "Sales Admin" role).

## 7. Use it

| URL | Role | Purpose |
|---|---|---|
| `/sales/plan` | employee | Declare today's planned place |
| `/sales/checkin` | employee | Submit GPS or manual check-in |
| `/sales/dashboard` | employee | Today's plan + recent check-ins |
| `/sales/history` | employee | Full history with match scores |
| `/sales/admin` | admin | Everyone's status + recent anomaly flags |

1. As Drupal admin, create a Drupal user → email = the employee's email.
2. Log in as that user, visit `/sales/plan`, declare a place (e.g. `Connaught Place, New Delhi`).
3. Visit `/sales/checkin`:
   - **Manual** with the same place → high match score, `matched=YES`.
   - **GPS** with coordinates far from the plan → low score, `matched=NO`; after ~10 check-ins the IsolationForest starts flagging outliers.
4. Switch to the admin user → `/sales/admin` shows the table and anomaly flags.

## How the AI works

**Matching (`ai/matcher.py`)**
- If both planned and actual have coords → `geopy.distance.geodesic` in km.
- Geo score = `max(0, 1 - dist_km / GEO_THRESHOLD_KM)`.
- Text similarity = `rapidfuzz.fuzz.token_set_ratio` ÷ 100.
- Combined = `0.7 × geo + 0.3 × text`. `matched = combined ≥ MATCH_THRESHOLD`.
- Missing coords are filled in via `Nominatim` geocoding (cached, requires internet).

**Anomaly detection (`ai/anomaly.py`)**
- Per employee, loads the last 60 check-ins.
- Features: `distance_km`, `text_similarity`, `hour_of_day`, `day_of_week`, `match_score`.
- Trains `IsolationForest(contamination=0.1)` on demand and predicts the current check-in.
- If flagged, reports which feature is the largest z-score outlier.
- Fewer than 10 prior check-ins → falls back to a rule (`distance > 20 km`).

## Configuration knobs (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DB_*` | XAMPP defaults | MySQL connection |
| `API_KEY` | dev value | Shared secret with Drupal — must match |
| `GEO_THRESHOLD_KM` | 5 | Distance at which geo-score hits 0 |
| `MATCH_THRESHOLD` | 0.6 | Combined score required for `matched=True` |

## Project layout

```
sales_tracker/
├── app.py                 Flask app + HTML fallback routes
├── api.py                 Flask /api/* JSON blueprint (used by Drupal)
├── config.py / db.py      Config + MySQL pool
├── seed_admin.py          Sets admin password
├── schema.sql             MySQL tables
├── ai/
│   ├── matcher.py         Geo + fuzzy match scoring
│   └── anomaly.py         IsolationForest
├── templates/ static/     Flask HTML fallback UI
├── drupal_module/
│   └── sales_tracker/     <-- COPY THIS into Drupal's modules/custom/
│       ├── sales_tracker.info.yml
│       ├── sales_tracker.routing.yml
│       ├── sales_tracker.permissions.yml
│       ├── sales_tracker.services.yml
│       ├── sales_tracker.libraries.yml
│       ├── sales_tracker.links.menu.yml
│       ├── sales_tracker.module
│       ├── config/install/sales_tracker.settings.yml
│       ├── css/sales_tracker.css
│       ├── src/Service/SalesTrackerApiClient.php
│       ├── src/Form/{PlanForm,CheckinForm,SettingsForm}.php
│       ├── src/Controller/{DashboardController,AdminController}.php
│       └── templates/sales-tracker-{dashboard,history,admin}.html.twig
└── requirements.txt
```

## Trust model (important)

Flask trusts Drupal: identity is read from `X-Employee-Email` plus a shared `X-API-Key`. Anyone able to reach Flask with the key can act as any email. Mitigations baked in:

- Flask binds to `127.0.0.1` only (see `app.py`).
- The API key is required on every call.

Do **not** expose port 5000 to the network as-is. If you need to, add proper auth (JWT signed by Drupal, or mTLS).

## Troubleshooting

- **`Cannot reach Sales Tracker API`** in Drupal — make sure `python app.py` is running and the URL in `/admin/config/sales-tracker/settings` matches.
- **`invalid api key`** in Flask logs — the `API_KEY` in `.env` and the Drupal settings page don't match.
- **`Access denied for user 'root'@'localhost'`** — XAMPP root has no password by default; leave `DB_PASS=` empty.
- **Geocoding fails** — `Nominatim` needs internet; provide GPS coords or a clearly-spelled `"Area, City"` name.
- **Browser refuses geolocation** — only works on `https://` or `http://localhost`. Drupal at `http://localhost/drupal/web` is fine.
