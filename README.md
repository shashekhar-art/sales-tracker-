# Bishwa Medicare Pvt Ltd — Sales Operations Tracking System

A two-stack application for tracking medical-representative field activity across India:

- **Backend** — Python + Flask exposes `/api/*` JSON endpoints, talks to MariaDB, and runs the AI features (geo + fuzzy text matching, IsolationForest anomaly detection).
- **Frontend** — Drupal 10 with the custom `sales_tracker` module and the custom `bishwa` theme. Drupal handles login and user management; on each call to Flask it sends the logged-in user's email and a shared API key so Flask auto-provisions the matching MySQL record.

```
Browser ─▶ Drupal 10 (PHP / Apache 8080) ──HTTP + API key──▶ Flask (127.0.0.1:5000) ─▶ MariaDB (3306)
                                                              └─▶ geopy + scikit-learn (AI)
```

A second, simpler **Flask HTML fallback UI** also lives at `http://127.0.0.1:5000/` if Apache isn't running.

---

## 1. What you need installed

| Tool | Version | Purpose |
|---|---|---|
| **XAMPP** | 8.2.x (PHP 8.2, MariaDB 10.4, Apache 2.4) | Web server + database |
| **Composer** | 2.x | Drupal install + drush |
| **Python** | 3.10 – 3.13 | Backend + AI |
| **Git** | any modern | Source control |

> XAMPP for Windows is at https://www.apachefriends.org/download.html  
> Composer for Windows is at https://getcomposer.org/Composer-Setup.exe (during install, point it at `C:\xampp\php\php.exe`)

---

## 2. Quick start — full local install

The whole stack ends up at `http://localhost:8080/drupal/` once these steps are done.

### 2.1 — Start XAMPP

1. Install XAMPP to `C:\xampp` (default).
2. **Change Apache to port 8080** before starting. Port 80 is often held by other services (IIS, Skype, SCCM client, etc.).  
   Edit `C:\xampp\apache\conf\httpd.conf`:
   ```
   Listen 8080
   ServerName localhost:8080
   ```
3. Open the XAMPP Control Panel → click **Start** next to **Apache** (green = OK) and **MySQL** (green = OK).
4. Open <http://localhost:8080/phpmyadmin> to confirm DB access. Default user is `root` with **empty password**.

### 2.2 — Install Composer

Download and run https://getcomposer.org/Composer-Setup.exe, point it at `C:\xampp\php\php.exe`. Open a **new** shell so the `composer` command is on PATH (or use `php C:\xampp\composer\composer.phar` if you installed it as a phar).

> On corporate Windows boxes (Deloitte, etc.) you may hit a TLS revocation error during `composer` and `git` calls. Fix once:
> ```bash
> git config --global http.schannelCheckRevoke false
> ```
> For Composer/PHP, merge the Windows root certificate store into PHP's CA bundle (see *Troubleshooting* below).

### 2.3 — Clone the project

```bash
cd "C:\<your projects folder>"
git clone https://github.com/shashekhar-art/sales-tracker- sales_tracker
cd sales_tracker
```

### 2.4 — Create the MariaDB databases

In the XAMPP shell or `phpMyAdmin` SQL tab:

```sql
CREATE DATABASE IF NOT EXISTS drupal10
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then import the sales-tracker schema + India geography:

```bash
# from the sales_tracker root
"C:\xampp\mysql\bin\mysql.exe" -u root < schema.sql            # creates DB + base tables
"C:\xampp\mysql\bin\mysql.exe" -u root < schema_v2.sql         # adds geo/multi-visit tables
"C:\xampp\mysql\bin\mysql.exe" -u root sales_tracker < india_geo_seed.sql   # 36 states + 786 districts + 40 sample accounts
```

After this `mysql -u root -e "USE sales_tracker; SHOW TABLES;"` should list:
`accounts, anomaly_flags, checkins, districts, employees, planned_visit_items, planned_visits, regions, targets`.

### 2.5 — Set up the Python backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set a long random `API_KEY` and `FLASK_SECRET`. The defaults assume XAMPP's empty-password root.

```bash
# Seed the Flask admin row (password: admin123)
.venv\Scripts\python.exe seed_admin.py

# (Optional) Seed demo employees + visits — useful for first-time demo
.venv\Scripts\python.exe seed_demo.py
.venv\Scripts\python.exe seed_districts.py
```

Start Flask:

```bash
.venv\Scripts\python.exe app.py
# leave this running. Health check: http://127.0.0.1:5000/api/health
```

### 2.6 — Install Drupal 10 + drush

```bash
cd C:\Users\<you>\
composer create-project drupal/recommended-project:^10 drupal-site
cd drupal-site
composer require drush/drush
```

Tell Drupal which DB to use and create the site (uses the `drupal10` DB you created in step 2.4):

```bash
php vendor/drush/drush/drush.php site:install standard \
  --db-url=mysql://root:@127.0.0.1:3306/drupal10 \
  --account-name=admin \
  --account-pass=admin123 \
  --account-mail=admin@example.com \
  --site-name="Bishwa Medicare Pvt Ltd" \
  --yes
```

### 2.7 — Install the `sales_tracker` Drupal module

```bash
# copy the module source into Drupal's custom modules directory
xcopy /E /I "C:\<your projects folder>\sales_tracker\drupal_module\sales_tracker" ^
            "C:\Users\<you>\drupal-site\web\modules\custom\sales_tracker"

cd C:\Users\<you>\drupal-site
php vendor/drush/drush/drush.php en sales_tracker --yes
```

Then point the module at your running Flask backend:

```bash
php vendor/drush/drush/drush.php cset sales_tracker.settings api_url 'http://127.0.0.1:5000' --yes
php vendor/drush/drush/drush.php cset sales_tracker.settings api_key "<paste-the-API_KEY-from-your-.env>" --yes
```

Grant permissions:

```bash
php vendor/drush/drush/drush.php role:perm:add authenticated 'use sales tracker'
# (administer sales tracker is already on the administrator role)
```

### 2.8 — Install the custom `bishwa` Drupal theme

```bash
xcopy /E /I "C:\<your projects folder>\sales_tracker\drupal_theme\bishwa" ^
            "C:\Users\<you>\drupal-site\web\themes\custom\bishwa"

cd C:\Users\<you>\drupal-site
php vendor/drush/drush/drush.php theme:enable bishwa --yes
php vendor/drush/drush/drush.php config:set system.theme default bishwa --yes
php vendor/drush/drush/drush.php cr
```

### 2.9 — Tell Apache to serve the Drupal install

Edit `C:\xampp\apache\conf\extra\httpd-sales-tracker.conf` (create it):

```apache
Alias /drupal "C:/Users/<you>/drupal-site/web"

<Directory "C:/Users/<you>/drupal-site/web">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
    DirectoryIndex index.php
</Directory>
```

And include it from `C:\xampp\apache\conf\httpd.conf`:

```apache
Include conf/extra/httpd-sales-tracker.conf
```

Restart Apache from the XAMPP Control Panel. Browse to **http://localhost:8080/drupal/**.

---

## 3. Demo accounts (after `seed_demo.py`)

| Drupal user | Display name | Role | Region · district |
|---|---|---|---|
| `admin` | Admin | administrator | — |
| `demo_priya` | Priya Sharma | employee | MH · Mumbai area |
| `demo_arjun` | Arjun Patel | employee | GJ · Ahmedabad |
| `demo_aditi` | Aditi Rao | employee | KA · Bengaluru Urban |
| `demo_vikram` | Vikram Singh | employee | DL · New Delhi |
| `demo_anjali` | Anjali Iyer | employee | TN · Chennai |
| `demo_rajesh` | Rajesh Kumar | administrator (acts as proctor) | TG · Hyderabad |
| `demo_suresh` | Suresh Reddy | administrator | DL · New Delhi |

All demo passwords: **`demo123`**. Admin password set during `drush site:install` (default `admin123`).

To remove every demo row added by `seed_demo.py` + `seed_districts.py`:

```bash
.venv\Scripts\python.exe remove_demo.py
```

(Drupal demo *users* are intentionally preserved by this script — drop them via `drush user:cancel <username>` if you also want them gone.)

---

## 4. Where things live

```
sales_tracker/
├── app.py                  Flask entry point — HTML routes + blueprint registration
├── api.py                  /api/* — plan / checkin / history / admin endpoints
├── api_accounts.py         /api/accounts/*
├── api_visits.py           /api/visits/*
├── api_geo.py              /api/regions/* and /api/districts/*
├── api_stats.py            /api/stats?period=day|week|month|quarter
├── api_proctor.py          /api/proctor/* (admin only)
├── api_reports.py          /api/reports/csv?type=visits|accounts
├── api_targets.py          /api/targets (admin only)
├── ai/
│   ├── matcher.py          geopy distance + rapidfuzz text similarity
│   └── anomaly.py          IsolationForest, retrains on demand
├── config.py · db.py       env config + MySQL connection pool
├── schema.sql              base DDL (employees, planned_visits, checkins, anomaly_flags)
├── schema_v2.sql           additive migration: regions, districts, accounts, planned_visit_items, targets
├── india_geo_seed.sql      36 states/UTs + 786 districts + 40 metro accounts
├── seed_admin.py           sets the admin password hash
├── seed_demo.py            7 hand-picked sample employees + visits + flags
├── seed_districts.py       1 sample medical rep per district (full national coverage)
├── remove_demo.py          wipes every demo row via the `_demo_data_ids` tracking table
├── templates/              Jinja HTML fallback UI
├── static/style.css        Flask UI stylesheet
├── drupal_module/sales_tracker/
│   ├── sales_tracker.{info,routing,permissions,services,libraries,links.menu}.yml
│   ├── sales_tracker.module    hooks (menubar preprocess, login redirect, form alter)
│   ├── css/{_tokens.css,sales_tracker.css}
│   ├── js/sales-tracker.js     geolocation behaviour (.js-st-geolocate)
│   ├── src/Controller/         Drupal controllers — Dashboard, Accounts, Visits, Reports, Proctor, Admin
│   ├── src/Form/               Drupal Form API — Plan, Checkin, Visit, Account, Target, Settings
│   ├── src/Service/SalesTrackerApiClient.php   thin Guzzle wrapper that calls Flask
│   └── templates/              Twig — dashboard, accounts, visit history, reports, proctor (national + drill-downs), menubar
└── drupal_theme/bishwa/
    ├── bishwa.{info,libraries}.yml + bishwa.theme
    ├── css/bishwa.css          theme styles (header, footer, login forms, responsive)
    └── templates/page.html.twig branded page wrapper
```

---

## 5. Day-to-day operations

### Start everything fresh

```bash
# 1) XAMPP: Start Apache + MySQL from the Control Panel
# 2) Flask
cd C:\<your-projects>\sales_tracker
.venv\Scripts\python.exe app.py
# 3) Browse http://localhost:8080/drupal/
```

### After you edit the Drupal module or theme

```bash
# Resync source into Drupal's custom dirs:
rm -rf C:\Users\<you>\drupal-site\web\modules\custom\sales_tracker
xcopy /E /I drupal_module\sales_tracker C:\Users\<you>\drupal-site\web\modules\custom\sales_tracker
# (theme analogously)
rm -rf C:\Users\<you>\drupal-site\web\themes\custom\bishwa
xcopy /E /I drupal_theme\bishwa C:\Users\<you>\drupal-site\web\themes\custom\bishwa

# Then clear Drupal's cache:
cd C:\Users\<you>\drupal-site
php vendor/drush/drush/drush.php cr
```

### After you edit any `.py` file

Restart Flask (Ctrl+C in the terminal that's running it, then `python app.py` again). The dev server hot-reloads templates but not module imports.

---

## 6. URLs

Drupal (primary UI), once logged in:

| URL | Who |
|---|---|
| `/drupal/user/login` | everyone |
| `/drupal/sales/dashboard` | employee + admin (admin redirected here on login) |
| `/drupal/sales/plan` | employee — declare today's plan |
| `/drupal/sales/visit` | employee — log a visit |
| `/drupal/sales/visits/history` | employee |
| `/drupal/sales/accounts` | everyone |
| `/drupal/sales/accounts/add` | admin |
| `/drupal/sales/reports` | everyone |
| `/drupal/sales/reports/csv/visits` (or `/accounts`) | everyone — CSV download |
| `/drupal/sales/admin` | admin |
| `/drupal/sales/targets` | admin |
| `/drupal/sales/proctor` | **admin only** |
| `/drupal/sales/proctor/region/{rid}` | admin only |
| `/drupal/sales/proctor/district/{did}` | admin only |
| `/drupal/sales/proctor/employee/{eid}` | admin only |
| `/drupal/admin/config/sales-tracker/settings` | admin — sets the Flask API URL + key |

Flask fallback UI: `http://127.0.0.1:5000/login` (uses Flask session auth — see `seed_admin.py`).

---

## 7. Configuration knobs (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASS` / `DB_NAME` | XAMPP defaults | MariaDB connection |
| `FLASK_SECRET` | dev value | Flask session signing key |
| `API_KEY` | dev value | Shared secret with the Drupal module — must match Drupal `sales_tracker.settings.api_key` |
| `GEO_THRESHOLD_KM` | 5 | Distance at which the geo-score hits 0 |
| `MATCH_THRESHOLD` | 0.6 | Combined match-score required to count as `matched` |

---

## 8. Troubleshooting

| Symptom | Cause + Fix |
|---|---|
| `Cannot reach Sales Tracker API` in the Drupal UI | Flask isn't running, or `api_url` is wrong. Start `python app.py` and recheck `/admin/config/sales-tracker/settings`. |
| `invalid api key` from Flask | The `API_KEY` in `.env` doesn't match `sales_tracker.settings.api_key` in Drupal. Update one, restart Flask. |
| Apache won't start on port 80 | Some other process holds it (IIS, SQL Server Reporting, Skype 4, SCCM client). Use port 8080 instead — see step 2.1. |
| Composer / git fails with TLS revocation errors on a corporate laptop | `git config --global http.schannelCheckRevoke false`. For Composer, export your Windows root CAs into `C:\xampp\apache\bin\curl-ca-bundle-merged.crt` and point `php.ini` at it (both `curl.cainfo` and `openssl.cafile`). |
| Drupal returns HTTP 500 with a Twig SyntaxError | Twig uses `{% elseif %}`, not `{% elif %}`. Search the module's `.twig` files. |
| `/drupal/sales/proctor` returns 403 even for admin | The role of the logged-in Drupal user must include `administrator`. Run `drush user:role:add administrator <username>`. |
| Browser still shows old CSS / JS after a code change | Hard refresh (Ctrl+F5) and `drush cr`. |

---

## 9. Security notes

- The Drupal ↔ Flask trust model is "Drupal sends the logged-in user's email + a shared API key, Flask trusts it". This is fine on `localhost` only.  
  **Do NOT expose Flask to a network without adding mTLS or a signed JWT.** Flask is intentionally bound to `127.0.0.1` in `app.py`.
- `.env` contains the API key and the Flask session secret. It's in `.gitignore`. Never commit it.
- All new database access uses `%s` parameter substitution — no string interpolation. Drupal Form API handles XSS on user input on its side.

---

## 10. Credits

- Schema, AI scoring, Drupal module + theme, demo seeds: this project.
- Drupal 10, drush, Symfony, Twig: their respective maintainers.
- Indian state/district lists: compiled from public sources.
