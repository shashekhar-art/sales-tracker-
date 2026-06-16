# Bishwa Medicare — Sales Tracking System

AI-powered field visit tracker for medical representatives in India.

**Stack:** Python 3.10+ / Flask · SQLite · geopy · scikit-learn · rapidfuzz

Live demo: `https://shashekhar.pythonanywhere.com`

---

## Setup

```bash
# 1. Clone and create a virtual environment
git clone https://github.com/shashekhar-art/sales-tracker-.git
cd sales-tracker-
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
copy .env.example .env        # edit FLASK_SECRET at minimum

# 4. Initialise the database and seed baseline data
python init_db.py             # creates sales_tracker.db with schema + India geo data
python seed_admin.py          # admin@example.com / admin123
python seed_shashekhar.py     # shashekhar / shashekhar123 (employee)
python seed_accounts.py       # sample doctors, chemists, stockists, retailers, wholesalers

# 5. Run
python app.py
```

Open `http://127.0.0.1:5000`.

---

## Key URLs

| URL | Who |
|---|---|
| `/dashboard` | Employee — today's stats, check-ins |
| `/plan` | Employee — declare today's visit plan |
| `/visit` | Employee — log a visit with GPS + selfie |
| `/history` | Employee — past check-ins with entry/exit times |
| `/admin` | Admin — manage employees, review anomalies |
| `/proctor` | Admin — all-India rollup (region → district → employee) |

---

## Project layout

```
app.py              — Flask routes (auth, dashboard, visit, admin, proctor)
api_*.py            — REST API blueprints (/api/*)
ai/matcher.py       — geo + fuzzy-name matching
ai/anomaly.py       — IsolationForest anomaly detection
db.py               — SQLite connection helper
config.py           — .env loading
init_db.py          — schema creation + India geo seed
seed_*.py           — data seeders
templates/          — Jinja2 HTML templates
static/             — CSS
```

---

## Environment variables (`.env`)

```
DB_PATH=sales_tracker.db          # path to SQLite file
FLASK_SECRET=change-me            # session signing key
API_KEY=change-me-too             # for /api/* endpoints
GEO_THRESHOLD_KM=5
MATCH_THRESHOLD=0.6
```
