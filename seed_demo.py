"""Insert sample data for demo purposes.

Every inserted row's primary key is recorded in the `_demo_data_ids` table so
the whole demo set can be removed later by running `python remove_demo.py`.

Seeds:
- Drupal users (via drush) so demo employees can log in via the browser
- Flask `employees` rows (matching emails — auto-provisioning would otherwise
  happen on first /sales/* call, but we want richer profiles up-front)
- 7 employees across 7 metros, varied roles
- A planned_visit for today per employee, with 2-4 planned_visit_items
- 8-15 check-ins per employee spread across the last 28 days
- 2 anomaly_flags for spice

Run:
    python seed_demo.py
To wipe everything seeded by this script later:
    python remove_demo.py
"""
import random
import subprocess
import sys
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

from db import query

# Deterministic randomness so a given run produces the same data.
random.seed(20260615)

DEMO_PASSWORD = "demo123"
DEMO_PASSWORD_HASH = generate_password_hash(DEMO_PASSWORD, method="pbkdf2:sha256")

# (display_name, drupal_username, email, role, region_code, district_name, phone, territory)
EMPLOYEES = [
    ("Priya Sharma",   "demo_priya",   "demo.priya@bishwa.local",   "employee", "MH", "Mumbai",    "+91 98201 11111", "Mumbai West"),
    ("Arjun Patel",    "demo_arjun",   "demo.arjun@bishwa.local",   "employee", "GJ", "Ahmedabad", "+91 79123 22222", "Ahmedabad Central"),
    ("Aditi Rao",      "demo_aditi",   "demo.aditi@bishwa.local",   "employee", "KA", "Bengaluru Urban", "+91 80543 33333", "Bengaluru South"),
    ("Vikram Singh",   "demo_vikram",  "demo.vikram@bishwa.local",  "employee", "DL", "New Delhi", "+91 11234 44444", "Delhi NCR"),
    ("Anjali Iyer",    "demo_anjali",  "demo.anjali@bishwa.local",  "employee", "TN", "Chennai",   "+91 44765 55555", "Chennai East"),
    ("Rajesh Kumar",   "demo_rajesh",  "demo.rajesh@bishwa.local",  "proctor",  "TG", "Hyderabad", "+91 40678 66666", "South India Region"),
    ("Suresh Reddy",   "demo_suresh",  "demo.suresh@bishwa.local",  "admin",    "DL", "New Delhi", "+91 11234 77777", "National Operations"),
]

DRUSH_BIN = r"C:\xampp\php\php.exe"
DRUSH_PHP = r"C:\Users\shashekhar\drupal-site\vendor\drush\drush\drush.php"
DRUPAL_ROOT = r"C:\Users\shashekhar\drupal-site"

VISIT_NOTES = [
    "Discussed Q3 portfolio. Promised to review pricing.",
    "Brought new sample pack; received warm response.",
    "Followed up on previous order; reorder confirmed.",
    "Met with the assistant; will revisit next week.",
    "Discussed competing brand. Loyalty in question.",
    "Quick courtesy call. Friendly meeting.",
    "Showed clinical trial summary for new line.",
    "Delivered POSM kit. Confirmed display placement.",
    "Pricing dispute resolved. Order pending HQ approval.",
    "Discussed quarterly target; doctor agreed to refer 5 patients.",
]
OUTCOMES = ["met", "met", "met", "met", "not_met", "rescheduled"]  # weighted: mostly met


def _track(table_name, row_id):
    """Track an inserted ID so it can be removed later."""
    query(
        "INSERT IGNORE INTO _demo_data_ids (table_name, row_id) VALUES (%s, %s)",
        (table_name, int(row_id)),
        fetch=False,
        commit=True,
    )


def ensure_tracking_table():
    query(
        """
        CREATE TABLE IF NOT EXISTS _demo_data_ids (
          table_name VARCHAR(50) NOT NULL,
          row_id INT NOT NULL,
          PRIMARY KEY (table_name, row_id)
        )
        """,
        fetch=False,
        commit=True,
    )


def resolve_district(region_code, district_name):
    rows, _ = query(
        """
        SELECT d.id AS did, d.region_id AS rid
        FROM districts d JOIN regions r ON r.id = d.region_id
        WHERE r.code = %s AND d.name = %s
        LIMIT 1
        """,
        (region_code, district_name),
    )
    if not rows:
        # Fallback: take the first district in that region
        rows, _ = query(
            """
            SELECT d.id AS did, d.region_id AS rid
            FROM districts d JOIN regions r ON r.id = d.region_id
            WHERE r.code = %s
            ORDER BY d.id ASC
            LIMIT 1
            """,
            (region_code,),
        )
    if not rows:
        raise RuntimeError(f"No district found for region={region_code} ({district_name})")
    return rows[0]["did"], rows[0]["rid"]


def get_district_accounts(district_id, limit=12):
    """Return account rows for a district (or empty if none seeded)."""
    rows, _ = query(
        "SELECT * FROM accounts WHERE district_id=%s ORDER BY id LIMIT %s",
        (district_id, limit),
    )
    return rows or []


def get_any_accounts(limit=12):
    rows, _ = query("SELECT * FROM accounts ORDER BY id LIMIT %s", (limit,))
    return rows or []


def insert_employee(name, email, role, district_id, region_id, phone, territory):
    # Idempotent: if email exists, refresh and return.
    existing, _ = query("SELECT id FROM employees WHERE email=%s", (email,))
    if existing:
        eid = existing[0]["id"]
        query(
            "UPDATE employees SET name=%s, password_hash=%s, role=%s, phone=%s, territory=%s, region_id=%s, district_id=%s WHERE id=%s",
            (name, DEMO_PASSWORD_HASH, role, phone, territory, region_id, district_id, eid),
            fetch=False, commit=True,
        )
        _track("employees", eid)
        return eid

    _, eid = query(
        "INSERT INTO employees (name, email, password_hash, role, phone, territory, region_id, district_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (name, email, DEMO_PASSWORD_HASH, role, phone, territory, region_id, district_id),
        fetch=False, commit=True,
    )
    _track("employees", eid)
    return eid


def insert_plan(employee_id, plan_date, place_name, notes, lat=None, lon=None):
    existing, _ = query(
        "SELECT id FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (employee_id, plan_date),
    )
    if existing:
        pid = existing[0]["id"]
        query(
            "UPDATE planned_visits SET planned_place_name=%s, notes=%s, planned_lat=%s, planned_lon=%s WHERE id=%s",
            (place_name, notes, lat, lon, pid),
            fetch=False, commit=True,
        )
        _track("planned_visits", pid)
        return pid

    _, pid = query(
        "INSERT INTO planned_visits (employee_id, plan_date, planned_place_name, planned_lat, planned_lon, notes) VALUES (%s,%s,%s,%s,%s,%s)",
        (employee_id, plan_date, place_name, lat, lon, notes),
        fetch=False, commit=True,
    )
    _track("planned_visits", pid)
    return pid


def insert_planned_item(plan_id, account_id, order_idx):
    existing, _ = query(
        "SELECT id FROM planned_visit_items WHERE plan_id=%s AND account_id=%s",
        (plan_id, account_id),
    )
    if existing:
        _track("planned_visit_items", existing[0]["id"])
        return existing[0]["id"]
    _, iid = query(
        "INSERT INTO planned_visit_items (plan_id, account_id, order_idx) VALUES (%s,%s,%s)",
        (plan_id, account_id, order_idx),
        fetch=False, commit=True,
    )
    _track("planned_visit_items", iid)
    return iid


def insert_checkin(employee_id, plan_id, account_id, when, lat, lon, place_name, source, outcome, distance_km, score, notes):
    matched = 1 if score is not None and score >= 0.6 else 0
    _, cid = query(
        """
        INSERT INTO checkins
          (employee_id, plan_id, checkin_time, source, actual_place_name,
           actual_lat, actual_lon, distance_km, text_similarity, match_score, matched,
           account_id, outcome, visit_notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (employee_id, plan_id, when, source, place_name,
         lat, lon, distance_km, score, score, matched,
         account_id, outcome, notes),
        fetch=False, commit=True,
    )
    _track("checkins", cid)
    return cid


def insert_anomaly_flag(employee_id, checkin_id, reason, score=None):
    _, fid = query(
        "INSERT INTO anomaly_flags (employee_id, checkin_id, score, reason) VALUES (%s,%s,%s,%s)",
        (employee_id, checkin_id, score, reason),
        fetch=False, commit=True,
    )
    _track("anomaly_flags", fid)
    return fid


def create_drupal_user(username, email, display_name, password=DEMO_PASSWORD):
    """Best-effort: create matching Drupal user via drush. Skipped if drush unavailable."""
    try:
        # Create the user (idempotent: drush returns error if exists, we ignore).
        subprocess.run(
            [DRUSH_BIN, DRUSH_PHP, "--root=" + DRUPAL_ROOT, "user:create", username,
             "--mail=" + email, "--password=" + password],
            capture_output=True, timeout=30, text=True,
        )
        # Make sure the password is the one we want (re-set in case user exists).
        subprocess.run(
            [DRUSH_BIN, DRUSH_PHP, "--root=" + DRUPAL_ROOT, "user:password", username, password],
            capture_output=True, timeout=30, text=True,
        )
        # Unblock in case it was blocked.
        subprocess.run(
            [DRUSH_BIN, DRUSH_PHP, "--root=" + DRUPAL_ROOT, "user:unblock", username],
            capture_output=True, timeout=30, text=True,
        )
        print(f"  Drupal user {username} ({display_name}) ready")
    except Exception as e:
        print(f"  Drupal user {username} — skipped ({e})")


def main():
    print("Seeding demo data for Bishwa Medicare...")
    ensure_tracking_table()

    # 1) Employees + matching Drupal users
    employee_records = []
    print("\nCreating sample employees...")
    for (name, drupal_user, email, role, region_code, district_name, phone, territory) in EMPLOYEES:
        try:
            did, rid = resolve_district(region_code, district_name)
        except RuntimeError as e:
            print(f"  SKIP {name}: {e}")
            continue
        eid = insert_employee(name, email, role, did, rid, phone, territory)
        create_drupal_user(drupal_user, email, name)
        employee_records.append({"id": eid, "name": name, "email": email, "role": role, "district_id": did, "region_id": rid})
        print(f"  {name} ({role}) -> employee_id={eid}, district_id={did}")

    if not employee_records:
        print("No employees created — nothing else to seed. Exiting.")
        return

    # 2) Plans for today + planned items
    print("\nCreating today's plans + planned items...")
    today = date.today()
    for emp in employee_records:
        if emp["role"] in ("admin", "proctor"):
            continue  # they manage, they don't visit
        accounts = get_district_accounts(emp["district_id"], limit=8)
        if not accounts:
            accounts = get_any_accounts(limit=6)
        if not accounts:
            print(f"  SKIP plan for {emp['name']} — no accounts seeded anywhere")
            continue
        first = accounts[0]
        plan_id = insert_plan(
            emp["id"],
            today,
            f"{(first.get('address') or 'Field territory')[:80]}",
            f"Demo plan for {emp['name']}.",
            lat=first.get("lat"),
            lon=first.get("lon"),
        )
        chosen = accounts[: min(4, len(accounts))]
        for idx, acc in enumerate(chosen):
            insert_planned_item(plan_id, acc["id"], idx)
        print(f"  {emp['name']}: plan_id={plan_id}, {len(chosen)} planned account(s)")

    # 3) Historical check-ins (visits) across the last 28 days
    print("\nCreating ~28 days of historical check-ins/visits...")
    now = datetime.now()
    total_checkins = 0
    for emp in employee_records:
        if emp["role"] in ("admin", "proctor"):
            continue
        accounts = get_district_accounts(emp["district_id"], limit=8)
        if not accounts:
            accounts = get_any_accounts(limit=6)
        if not accounts:
            continue
        # 1-3 visits per business day for ~22 of the last 28 days
        for days_ago in range(0, 28):
            day_dt = now - timedelta(days=days_ago)
            if day_dt.weekday() >= 5:  # skip weekends
                continue
            n_visits = random.choice([0, 1, 2, 2, 3])
            for _ in range(n_visits):
                acc = random.choice(accounts)
                hour = random.randint(9, 19)
                minute = random.randint(0, 59)
                when = day_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # jitter location slightly around the account's coords
                base_lat = acc.get("lat") or 19.0760
                base_lon = acc.get("lon") or 72.8777
                dlat = random.uniform(-0.03, 0.03)
                dlon = random.uniform(-0.03, 0.03)
                actual_lat = base_lat + dlat
                actual_lon = base_lon + dlon
                # crude distance approx: 1 deg ~ 111 km, take Pythagorean
                distance_km = round(((dlat * 111) ** 2 + (dlon * 95) ** 2) ** 0.5, 3)
                # score inversely proportional to distance, clamped
                score = max(0.0, min(1.0, 1.0 - distance_km / 6.0))
                outcome = random.choice(OUTCOMES)
                source = random.choice(["gps", "gps", "gps", "manual"])
                notes = random.choice(VISIT_NOTES)
                cid = insert_checkin(
                    emp["id"], None, acc["id"], when,
                    actual_lat, actual_lon,
                    f"Near {(acc.get('address') or acc['name'])[:60]}",
                    source, outcome, distance_km, round(score, 3), notes,
                )
                total_checkins += 1
                # occasional anomaly flag for low-score visits
                if score < 0.25 and random.random() < 0.3:
                    insert_anomaly_flag(emp["id"], cid, f"Far from planned area ({distance_km:.1f} km)", score=score)
    print(f"  Inserted {total_checkins} historical check-ins")

    # 4) One extra obvious anomaly to make the proctor dashboard pop
    if employee_records:
        emp = employee_records[0]
        accounts = get_any_accounts(limit=1)
        if accounts:
            acc = accounts[0]
            when = now - timedelta(days=2, hours=4)
            cid = insert_checkin(
                emp["id"], None, acc["id"], when,
                28.61, 77.21,  # Delhi
                "Anomalous remote location",
                "gps", "not_met", 850.0, 0.05, "Demo anomaly: visit far from plan.",
            )
            insert_anomaly_flag(emp["id"], cid, "Distance from plan (850.0 km) exceeds 20 km threshold", score=None)
            print(f"  Extra demo anomaly flagged for {emp['name']}")

    print("\nDone.")
    print(f"  Demo password (for all sample users): {DEMO_PASSWORD}")
    print( "  To remove all demo data later, run: python remove_demo.py")


if __name__ == "__main__":
    main()
