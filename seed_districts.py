"""Seed one sample medical representative per district + per-district sample
accounts + a handful of visits each. All inserts are tagged in
`_demo_data_ids` so they're removable via remove_demo.py.

Idempotent: safe to re-run. Skips districts that already have a tagged sample
employee.

Roughly produces:
- ~786 sample employees (one per district)
- ~600-2300 sample accounts (3 per district that didn't already have any;
  the 8 metro districts already have 5 each from india_geo_seed.sql)
- ~3-8 visits per new employee = ~3-6k visits

Run from the sales_tracker dir:
    .venv\\Scripts\\python.exe seed_districts.py

Cleanup later:
    .venv\\Scripts\\python.exe remove_demo.py
"""
import random
import time
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from db import get_conn

random.seed(20260615)

DEMO_PASSWORD = "demo123"
DEMO_PASSWORD_HASH = generate_password_hash(DEMO_PASSWORD, method="pbkdf2:sha256")

# Diverse pool of Indian first + last names (mix of regions/genders).
FIRST_NAMES = [
    "Aarav", "Aditi", "Aditya", "Akash", "Amit", "Anil", "Anjali", "Ankit",
    "Anuj", "Anusha", "Arjun", "Aryan", "Ashish", "Asmita", "Avani",
    "Bhavna", "Chetan", "Deepika", "Devika", "Dhruv", "Divya", "Faisal",
    "Farhan", "Gaurav", "Geeta", "Harish", "Harsh", "Hemant", "Ishaan",
    "Ishita", "Jagdish", "Jaya", "Kabir", "Kajal", "Kalyan", "Kamal",
    "Karan", "Kavita", "Kiran", "Krishna", "Kunal", "Lakshmi", "Lalit",
    "Madhav", "Mahesh", "Manish", "Manoj", "Meera", "Mohammed", "Mohit",
    "Nandini", "Naresh", "Neha", "Nikhil", "Nirmala", "Nisha", "Pallavi",
    "Parul", "Pooja", "Prakash", "Pranav", "Pratik", "Preeti", "Priya",
    "Rachit", "Radha", "Raghav", "Rahul", "Rajesh", "Rajiv", "Rakesh",
    "Ramesh", "Rani", "Ravi", "Rekha", "Riya", "Rohan", "Rohit", "Sahil",
    "Sandeep", "Sanjay", "Sanjana", "Sapna", "Sarita", "Shalini",
    "Shankar", "Shivani", "Shreya", "Shruti", "Siddharth", "Simran",
    "Sneha", "Soumya", "Srinivas", "Subhash", "Sumit", "Sunita", "Suresh",
    "Swati", "Tanvi", "Tarun", "Uday", "Usha", "Vandana", "Varun",
    "Venkat", "Vidya", "Vikas", "Vikram", "Vinay", "Vinod", "Vivek",
    "Yogesh",
]
LAST_NAMES = [
    "Acharya", "Aggarwal", "Anand", "Banerjee", "Bansal", "Bhalla",
    "Bhardwaj", "Bhatt", "Bhattacharya", "Bose", "Chakraborty", "Chand",
    "Chatterjee", "Chauhan", "Chopra", "Das", "Datta", "Desai",
    "Deshmukh", "Dhawan", "Dixit", "Dube", "Dutta", "Gandhi", "Ganesh",
    "Garg", "George", "Ghosh", "Gill", "Goel", "Gowda", "Gupta", "Hegde",
    "Iyer", "Jain", "Jha", "Johar", "Joshi", "Kapoor", "Karthik",
    "Khan", "Khanna", "Krishnan", "Kulkarni", "Kumar", "Kurian",
    "Lal", "Mahajan", "Malhotra", "Manjunath", "Marathe", "Mathur",
    "Mehta", "Menon", "Mishra", "Mittal", "Mukherjee", "Murthy",
    "Nadkarni", "Nag", "Nair", "Naidu", "Narayan", "Nath", "Patel",
    "Pathak", "Patil", "Pillai", "Prasad", "Raghavan", "Rajan", "Rao",
    "Reddy", "Roy", "Saha", "Saini", "Saxena", "Sen", "Sengupta",
    "Sethi", "Shah", "Sharma", "Shetty", "Shukla", "Singh", "Singhal",
    "Sinha", "Soni", "Srinivas", "Subramanian", "Suri", "Talwar",
    "Tandon", "Thakur", "Tiwari", "Trivedi", "Varma", "Venkatesan",
    "Verma", "Vyas",
]

VISIT_NOTES = [
    "Brief courtesy visit. Verified stock.",
    "Discussed new product line, samples handed over.",
    "Promotional material delivered, display arranged.",
    "Reorder confirmed for the month.",
    "Met assistant; doctor not available. Rescheduled.",
    "Follow-up on quarterly target. Healthy progress.",
    "Discussed competitor pricing concerns.",
    "Collected feedback on last sample batch.",
    "Demonstrated new combination therapy data.",
    "Discussed CME participation for next quarter.",
    "Confirmed delivery schedule for institutional order.",
    "Reviewed Q3 prescription patterns.",
]
OUTCOMES = ["met", "met", "met", "met", "met", "not_met", "rescheduled"]


def main():
    t0 = time.time()
    conn = get_conn()
    conn.autocommit = False
    try:
        cur = conn.cursor(dictionary=True)

        # 1) Make sure the tracking table exists
        cur.execute(
            """CREATE TABLE IF NOT EXISTS _demo_data_ids (
                 table_name VARCHAR(50) NOT NULL,
                 row_id INT NOT NULL,
                 PRIMARY KEY (table_name, row_id)
               )"""
        )

        # 2) Districts
        cur.execute(
            """SELECT d.id AS did, d.region_id AS rid, d.name AS dname, r.code AS rcode
               FROM districts d JOIN regions r ON r.id = d.region_id
               ORDER BY d.id"""
        )
        districts = cur.fetchall()
        print(f"Loaded {len(districts)} districts")

        # 3) Which districts already have a tagged sample employee? (idempotency)
        cur.execute(
            """SELECT e.district_id
               FROM employees e
               JOIN _demo_data_ids t ON t.table_name='employees' AND t.row_id=e.id
               WHERE e.district_id IS NOT NULL
               GROUP BY e.district_id"""
        )
        already_seeded = {row["district_id"] for row in cur.fetchall()}
        todo = [d for d in districts if d["did"] not in already_seeded]
        print(f"{len(already_seeded)} districts already have a sample rep; {len(todo)} to seed")

        # 4) Insert one employee per remaining district
        emp_inserted = 0
        for d in todo:
            first = random.choice(FIRST_NAMES)
            last  = random.choice(LAST_NAMES)
            name  = f"{first} {last}"
            email = f"rep.{first.lower()}.{last.lower()}.{d['did']}@bishwa.local"
            cur.execute(
                """INSERT INTO employees
                     (name, email, password_hash, role, region_id, district_id, territory, phone)
                   VALUES (%s,%s,%s,'employee',%s,%s,%s,%s)""",
                (name, email, DEMO_PASSWORD_HASH, d["rid"], d["did"],
                 d["dname"], f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"),
            )
            eid = cur.lastrowid
            cur.execute("INSERT INTO _demo_data_ids (table_name, row_id) VALUES ('employees', %s)", (eid,))
            emp_inserted += 1
            if emp_inserted % 100 == 0:
                conn.commit()  # checkpoint
                print(f"  ...{emp_inserted} employees inserted (committed)")

        conn.commit()
        print(f"Employees: {emp_inserted} new")

        # 5) Add accounts to districts that have none.
        cur.execute(
            """SELECT d.id AS did, d.name AS dname,
                      (SELECT COUNT(*) FROM accounts a WHERE a.district_id=d.id) AS acct_count
               FROM districts d
               HAVING acct_count = 0"""
        )
        empty_districts = cur.fetchall()
        print(f"{len(empty_districts)} districts have no accounts; adding 3 each (doctor/chemist/stockist)")

        acc_inserted = 0
        acc_types = ["doctor", "chemist", "stockist"]
        specialty_pool = {
            "doctor":   ["General Physician", "Pediatrician", "Cardiologist", "Dermatologist",
                         "Gynecologist", "Orthopedic Surgeon", "ENT Specialist", "Diabetologist",
                         "Neurologist", "Oncologist"],
            "chemist":  [None],
            "stockist": [None],
        }
        for d in empty_districts:
            for t in acc_types:
                first = random.choice(FIRST_NAMES)
                last  = random.choice(LAST_NAMES)
                if t == "doctor":
                    acc_name = f"Dr. {first} {last}"
                    addr = f"Medical Plaza, {d['dname']}"
                elif t == "chemist":
                    acc_name = f"{last} {random.choice(['Medicals', 'Pharmacy', 'Chemist', 'Medical Store'])}"
                    addr = f"Main Market, {d['dname']}"
                else:
                    acc_name = f"{last} {random.choice(['Distributors', 'Pharma Stockist', 'Medical Supplies'])}"
                    addr = f"Wholesale Market, {d['dname']}"
                specialty = random.choice(specialty_pool[t]) if t == "doctor" else None
                cur.execute(
                    """INSERT INTO accounts (name, type, specialty, district_id, address, phone)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (acc_name, t, specialty, d["did"], addr,
                     f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"),
                )
                aid = cur.lastrowid
                cur.execute("INSERT INTO _demo_data_ids (table_name, row_id) VALUES ('accounts', %s)", (aid,))
                acc_inserted += 1
            if acc_inserted % 300 == 0:
                conn.commit()
                print(f"  ...{acc_inserted} accounts inserted (committed)")
        conn.commit()
        print(f"Accounts: {acc_inserted} new")

        # 6) Visits for each new employee (those we just inserted; we re-query by tag)
        cur.execute(
            """SELECT e.id AS eid, e.district_id AS did, e.region_id AS rid
               FROM employees e
               JOIN _demo_data_ids t ON t.table_name='employees' AND t.row_id=e.id
               WHERE e.district_id IS NOT NULL"""
        )
        all_demo_emps = cur.fetchall()
        # only seed visits for employees that don't already have visits
        cur.execute(
            """SELECT employee_id, COUNT(*) AS n
               FROM checkins
               WHERE account_id IS NOT NULL
               GROUP BY employee_id"""
        )
        existing_visit_count = {row["employee_id"]: row["n"] for row in cur.fetchall()}
        emps_needing_visits = [e for e in all_demo_emps if existing_visit_count.get(e["eid"], 0) == 0]
        print(f"{len(emps_needing_visits)} employees need historical visits")

        visit_inserted = 0
        now = datetime.now()
        for e in emps_needing_visits:
            cur.execute("SELECT id, name FROM accounts WHERE district_id=%s ORDER BY id", (e["did"],))
            accounts_here = cur.fetchall()
            if not accounts_here:
                continue
            n_visits = random.randint(3, 8)
            for _ in range(n_visits):
                acc = random.choice(accounts_here)
                days_ago = random.randint(0, 27)
                day_dt = now - timedelta(days=days_ago)
                if day_dt.weekday() >= 5:
                    continue
                when = day_dt.replace(
                    hour=random.randint(9, 19),
                    minute=random.randint(0, 59),
                    second=0,
                    microsecond=0,
                )
                distance_km = round(random.uniform(0.05, 1.6), 3)
                score = round(max(0.0, 1.0 - distance_km / 4.0), 3)
                matched = 1 if score >= 0.6 else 0
                outcome = random.choice(OUTCOMES)
                source = random.choice(["gps", "gps", "gps", "manual"])
                cur.execute(
                    """INSERT INTO checkins
                         (employee_id, account_id, checkin_time, source, actual_place_name,
                          distance_km, text_similarity, match_score, matched, outcome, visit_notes)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (e["eid"], acc["id"], when, source, f"Near {acc['name']}",
                     distance_km, score, score, matched, outcome,
                     random.choice(VISIT_NOTES)),
                )
                cid = cur.lastrowid
                cur.execute("INSERT INTO _demo_data_ids (table_name, row_id) VALUES ('checkins', %s)", (cid,))
                visit_inserted += 1
            if visit_inserted % 500 == 0:
                conn.commit()
                print(f"  ...{visit_inserted} visits inserted (committed)")

        conn.commit()
        print(f"Visits: {visit_inserted} new")

        # 7) Final summary numbers
        cur.execute("SELECT COUNT(*) AS n FROM employees WHERE district_id IS NOT NULL")
        emps_total = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM accounts")
        accs_total = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM checkins WHERE account_id IS NOT NULL")
        visits_total = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(DISTINCT region_id) AS n FROM employees WHERE region_id IS NOT NULL")
        states_covered = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(DISTINCT district_id) AS n FROM employees WHERE district_id IS NOT NULL")
        districts_covered = cur.fetchone()["n"]
        print(f"\nFinal totals:")
        print(f"  employees with district : {emps_total}")
        print(f"  accounts                : {accs_total}")
        print(f"  account-linked visits   : {visits_total}")
        print(f"  states covered          : {states_covered} / 36")
        print(f"  districts covered       : {districts_covered}")
        print(f"\nElapsed: {time.time() - t0:.1f}s")
        print("Cleanup later with: .venv\\Scripts\\python.exe remove_demo.py")
    finally:
        try: cur.close()
        except Exception: pass
        conn.close()


if __name__ == "__main__":
    main()
