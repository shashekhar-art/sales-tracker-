"""Seed sample pharma accounts (doctor/chemist/stockist/retailer/wholesaler)
for every district in every Indian state/UT.

Adds 2 doctors, 2 chemists, 2 stockists, 1 retailer, 1 wholesaler per district.
~640 districts × 8 = ~5 120 accounts total.

Safe to run multiple times — skips districts that already have ≥5 accounts.

Run:
    python seed_accounts.py
"""
import random
import sys
from db import query

# ---------------------------------------------------------------------------
# Approximate lat/lon for each state/UT capital (used as district base coord)
# ---------------------------------------------------------------------------
STATE_COORDS = {
    "AP": (16.52,  80.52), "AR": (27.08,  93.60), "AS": (26.14,  91.74),
    "BR": (25.59,  85.13), "CG": (21.25,  81.63), "GA": (15.49,  73.82),
    "GJ": (23.21,  72.63), "HR": (30.74,  76.79), "HP": (31.10,  77.17),
    "JH": (23.35,  85.33), "KA": (12.97,  77.59), "KL": ( 8.52,  76.94),
    "MP": (23.26,  77.40), "MH": (19.08,  72.88), "MN": (24.80,  93.94),
    "ML": (25.57,  91.88), "MZ": (23.72,  92.72), "NL": (25.67,  94.11),
    "OR": (20.30,  85.82), "PB": (30.74,  76.79), "RJ": (26.92,  75.79),
    "SK": (27.33,  88.62), "TN": (13.08,  80.27), "TG": (17.38,  78.49),
    "TR": (23.83,  91.28), "UP": (26.85,  80.95), "UK": (30.32,  78.03),
    "WB": (22.57,  88.37), "AN": (11.62,  92.73), "CH": (30.74,  76.79),
    "DN": (20.39,  72.83), "DL": (28.61,  77.21), "JK": (32.73,  74.87),
    "LA": (34.17,  77.58), "LD": (10.56,  72.64), "PY": (11.93,  79.83),
}

# ---------------------------------------------------------------------------
# Name pools
# ---------------------------------------------------------------------------
FIRST_NAMES = [
    "Rajesh", "Suresh", "Mahesh", "Ramesh", "Ganesh", "Naresh",
    "Priya", "Anita", "Sunita", "Kavita", "Geeta", "Sita",
    "Amit", "Sumit", "Rohit", "Mohit", "Ankit", "Vinit",
    "Ravi", "Kavi", "Shyam", "Ram", "Hari", "Shiv",
    "Anil", "Sunil", "Vijay", "Ajay", "Sanjay", "Manoj",
]
SURNAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Singh", "Kumar",
    "Rao", "Reddy", "Nair", "Pillai", "Iyer", "Menon",
    "Shah", "Joshi", "Mishra", "Pandey", "Tiwari", "Dubey",
    "Das", "Dey", "Bose", "Roy", "Sen", "Ghosh",
    "Chatterjee", "Mukherjee", "Banerjee", "Chakraborty", "Bhatt", "Trivedi",
]
DOCTOR_SUFFIXES = [
    "Clinic", "Medical Centre", "Health Clinic",
    "Nursing Home", "Poly Clinic", "Hospital",
]
CHEMIST_SUFFIXES = [
    "Pharmacy", "Medical Store", "Drug House",
    "Medical Hall", "Medicines", "Chemist",
]
STOCKIST_SUFFIXES = [
    "Pharmaceuticals", "Drug Traders", "Medico Distributors",
    "Pharma Distributors", "Drug Agencies", "Pharma Depot",
]
RETAILER_SUFFIXES = [
    "Medical Shop", "Health Store", "Medical Point",
    "Wellness Store", "Life Care", "Med Mart",
]
WHOLESALER_SUFFIXES = [
    "Wholesale Pharma", "Drug Wholesale", "Bulk Medicals",
    "Pharma Wholesale Hub", "Drug Depot Wholesale", "Mass Medico",
]
SPECIALTIES = [
    "General Physician", "Cardiologist", "Dermatologist",
    "Gynaecologist", "Paediatrician", "Orthopaedician",
    "ENT Specialist", "Neurologist", "Oncologist", "Diabetologist",
]
PHONE_PREFIXES = ["98", "97", "96", "95", "94", "93", "92", "91", "90", "89"]


def _rng(seed_str):
    """Return a seeded random instance for deterministic generation per district."""
    r = random.Random()
    r.seed(hash(seed_str) & 0xFFFFFFFF)
    return r


def _phone(r):
    return f"+91 {r.choice(PHONE_PREFIXES)}{r.randint(10000000, 99999999)}"


def _coords(base_lat, base_lon, r):
    """Jitter coordinates ±1.5° from state capital."""
    return (
        round(base_lat + r.uniform(-1.5, 1.5), 6),
        round(base_lon + r.uniform(-1.5, 1.5), 6),
    )


def _make_accounts(district_name, region_code, base_lat, base_lon):
    """Return list of account dicts for one district."""
    r = _rng(f"{region_code}:{district_name}")
    accounts = []

    def _name(first, last, suffix):
        return f"{first} {last} {suffix}"

    # 2 doctors
    for _ in range(2):
        fn, ln = r.choice(FIRST_NAMES), r.choice(SURNAMES)
        lat, lon = _coords(base_lat, base_lon, r)
        accounts.append({
            "name": f"Dr. {fn} {ln} {r.choice(DOCTOR_SUFFIXES)}",
            "type": "doctor",
            "specialty": r.choice(SPECIALTIES),
            "address": f"{district_name}, {region_code}",
            "phone": _phone(r),
            "lat": lat, "lon": lon,
        })

    # 2 chemists
    for _ in range(2):
        fn, ln = r.choice(FIRST_NAMES), r.choice(SURNAMES)
        lat, lon = _coords(base_lat, base_lon, r)
        accounts.append({
            "name": f"{fn} {ln} {r.choice(CHEMIST_SUFFIXES)}",
            "type": "chemist",
            "specialty": None,
            "address": f"Market Area, {district_name}, {region_code}",
            "phone": _phone(r),
            "lat": lat, "lon": lon,
        })

    # 2 stockists
    for _ in range(2):
        fn, ln = r.choice(FIRST_NAMES), r.choice(SURNAMES)
        lat, lon = _coords(base_lat, base_lon, r)
        accounts.append({
            "name": f"{fn} {ln} {r.choice(STOCKIST_SUFFIXES)}",
            "type": "stockist",
            "specialty": None,
            "address": f"Industrial Area, {district_name}, {region_code}",
            "phone": _phone(r),
            "lat": lat, "lon": lon,
        })

    # 1 retailer
    fn, ln = r.choice(FIRST_NAMES), r.choice(SURNAMES)
    lat, lon = _coords(base_lat, base_lon, r)
    accounts.append({
        "name": f"{fn} {ln} {r.choice(RETAILER_SUFFIXES)}",
        "type": "retailer",
        "specialty": None,
        "address": f"Main Road, {district_name}, {region_code}",
        "phone": _phone(r),
        "lat": lat, "lon": lon,
    })

    # 1 wholesaler
    fn, ln = r.choice(FIRST_NAMES), r.choice(SURNAMES)
    lat, lon = _coords(base_lat, base_lon, r)
    accounts.append({
        "name": f"{fn} {ln} {r.choice(WHOLESALER_SUFFIXES)}",
        "type": "wholesaler",
        "specialty": None,
        "address": f"Warehouse Zone, {district_name}, {region_code}",
        "phone": _phone(r),
        "lat": lat, "lon": lon,
    })

    return accounts


def main(state_filter=None):
    # Fetch all districts with their region codes
    if state_filter:
        rows, _ = query(
            """
            SELECT d.id AS district_id, d.name AS district_name,
                   r.id AS region_id, r.code AS region_code, r.name AS region_name
            FROM districts d
            JOIN regions r ON r.id = d.region_id
            WHERE r.code = %s
            ORDER BY d.name
            """,
            (state_filter.upper(),),
        )
    else:
        rows, _ = query(
            """
            SELECT d.id AS district_id, d.name AS district_name,
                   r.id AS region_id, r.code AS region_code, r.name AS region_name
            FROM districts d
            JOIN regions r ON r.id = d.region_id
            ORDER BY r.code, d.name
            """,
        )
    if not rows:
        print(f"No districts found{' for state ' + state_filter if state_filter else ''}.")
        return

    print(f"Found {len(rows)} districts{' in ' + state_filter.upper() if state_filter else ' across all states/UTs'}.")
    total_inserted = 0
    total_skipped = 0

    for dist in rows:
        did = dist["district_id"]
        dname = dist["district_name"]
        rcode = dist["region_code"]
        rname = dist["region_name"]

        # Skip if district already has ≥ 5 accounts
        count_rows, _ = query(
            "SELECT COUNT(*) AS cnt FROM accounts WHERE district_id=%s",
            (did,),
        )
        existing = count_rows[0]["cnt"] if count_rows else 0
        if existing >= 5:
            total_skipped += 1
            continue

        base_lat, base_lon = STATE_COORDS.get(rcode, (20.59, 78.96))  # India centre fallback
        accs = _make_accounts(dname, rcode, base_lat, base_lon)

        for acc in accs:
            query(
                """
                INSERT INTO accounts
                  (name, type, specialty, district_id, address, phone, lat, lon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    acc["name"], acc["type"], acc["specialty"],
                    did, acc["address"], acc["phone"],
                    acc["lat"], acc["lon"],
                ),
                fetch=False, commit=True,
            )
            total_inserted += 1

        print(f"  [{rcode}] {dname}: +{len(accs)} accounts")

    print(f"\nDone. Inserted {total_inserted} accounts, skipped {total_skipped} districts (already seeded).")


if __name__ == "__main__":
    sf = sys.argv[1].upper() if len(sys.argv) > 1 else None
    main(state_filter=sf)
