"""Proctor (national-visibility) API blueprint.

Hierarchy: India -> Region -> District -> Employee.
Access: admin or proctor only.
"""
from datetime import date, datetime, time, timedelta
from functools import wraps

from flask import Blueprint, jsonify, g

from db import query
from api import require_drupal


bp = Blueprint("proctor", __name__, url_prefix="/api")


def require_proctor_or_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        role = g.employee.get("role") if hasattr(g, "employee") else None
        if role not in ("admin", "proctor"):
            return jsonify({"ok": False, "error": "proctor or admin only"}), 403
        return f(*args, **kwargs)
    return wrapper


def _windows(today=None):
    """Return mapping period -> (start_dt, end_dt) for day/week/month/quarter."""
    today = today or date.today()
    wk_start = today - timedelta(days=today.weekday())
    mo_start = today.replace(day=1)
    q_start_month = ((today.month - 1) // 3) * 3 + 1
    q_start = today.replace(month=q_start_month, day=1)
    end = datetime.combine(today, time.max)
    return {
        "day":     (datetime.combine(today, time.min), end),
        "week":    (datetime.combine(wk_start, time.min), end),
        "month":   (datetime.combine(mo_start, time.min), end),
        "quarter": (datetime.combine(q_start, time.min), end),
    }


def _count_visits_by_region(start_dt, end_dt):
    """Return dict: region_id -> visit count for the period (visits = checkins with account_id)."""
    rows, _ = query(
        """
        SELECT r.id AS region_id, COUNT(c.id) AS cnt
        FROM checkins c
        JOIN accounts a   ON a.id = c.account_id
        JOIN districts d  ON d.id = a.district_id
        JOIN regions   r  ON r.id = d.region_id
        WHERE c.account_id IS NOT NULL
          AND c.checkin_time BETWEEN %s AND %s
        GROUP BY r.id
        """,
        (start_dt, end_dt),
    )
    return {int(r["region_id"]): int(r["cnt"]) for r in (rows or [])}


def fetch_india_rollups():
    """Return a dict with 'regions' (list) and 'totals' (dict) for the Drupal proctor page.

    Each region row exposes 'today/week/month/quarter' and 'employees' aligned with
    the Twig template field names, plus the legacy visits_* and employee_count keys
    so older consumers keep working.
    """
    win = _windows()
    by_period = {p: _count_visits_by_region(*win[p]) for p in win}
    regions, _ = query(
        """
        SELECT r.id, r.name, r.code, r.type,
               (SELECT COUNT(*) FROM employees e WHERE e.region_id=r.id) AS employee_count
        FROM regions r
        ORDER BY r.name
        """
    )
    rows = []
    totals = {"today": 0, "week": 0, "month": 0, "quarter": 0}
    for r in regions or []:
        today_cnt = by_period["day"].get(r["id"], 0)
        week_cnt = by_period["week"].get(r["id"], 0)
        month_cnt = by_period["month"].get(r["id"], 0)
        quarter_cnt = by_period["quarter"].get(r["id"], 0)
        emp_cnt = int(r["employee_count"] or 0)
        totals["today"] += today_cnt
        totals["week"] += week_cnt
        totals["month"] += month_cnt
        totals["quarter"] += quarter_cnt
        rows.append({
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "type": r["type"],
            # New (Drupal Twig) field names.
            "employees": emp_cnt,
            "today": today_cnt,
            "week": week_cnt,
            "month": month_cnt,
            "quarter": quarter_cnt,
            # Legacy aliases.
            "employee_count": emp_cnt,
            "visits_day":     today_cnt,
            "visits_week":    week_cnt,
            "visits_month":   month_cnt,
            "visits_quarter": quarter_cnt,
        })
    return {"regions": rows, "totals": totals}


def fetch_region_rollups(region_id):
    """Return dict {'region': {...}, 'districts': [...], 'totals': {...}}."""
    win = _windows()

    def _count_by_district(start_dt, end_dt):
        rows, _ = query(
            """
            SELECT d.id AS district_id, COUNT(c.id) AS cnt
            FROM checkins c
            JOIN accounts a  ON a.id = c.account_id
            JOIN districts d ON d.id = a.district_id
            WHERE c.account_id IS NOT NULL
              AND d.region_id=%s
              AND c.checkin_time BETWEEN %s AND %s
            GROUP BY d.id
            """,
            (region_id, start_dt, end_dt),
        )
        return {int(r["district_id"]): int(r["cnt"]) for r in (rows or [])}

    region_rows, _ = query(
        "SELECT id, name, code, type FROM regions WHERE id=%s",
        (region_id,),
    )
    region = region_rows[0] if region_rows else None

    by_period = {p: _count_by_district(*win[p]) for p in win}
    districts, _ = query(
        """
        SELECT d.id, d.name, d.code,
               (SELECT COUNT(*) FROM employees e WHERE e.district_id=d.id) AS employee_count
        FROM districts d
        WHERE d.region_id=%s
        ORDER BY d.name
        """,
        (region_id,),
    )
    out = []
    totals = {"today": 0, "week": 0, "month": 0, "quarter": 0}
    for d in districts or []:
        today_cnt = by_period["day"].get(d["id"], 0)
        week_cnt = by_period["week"].get(d["id"], 0)
        month_cnt = by_period["month"].get(d["id"], 0)
        quarter_cnt = by_period["quarter"].get(d["id"], 0)
        emp_cnt = int(d["employee_count"] or 0)
        totals["today"] += today_cnt
        totals["week"] += week_cnt
        totals["month"] += month_cnt
        totals["quarter"] += quarter_cnt
        out.append({
            "id": d["id"],
            "name": d["name"],
            "code": d["code"],
            # New (Drupal Twig) field names.
            "employees": emp_cnt,
            "today": today_cnt,
            "week": week_cnt,
            "month": month_cnt,
            "quarter": quarter_cnt,
            # Legacy aliases.
            "employee_count": emp_cnt,
            "visits_day":     today_cnt,
            "visits_week":    week_cnt,
            "visits_month":   month_cnt,
            "visits_quarter": quarter_cnt,
        })
    return {"region": region, "districts": out, "totals": totals}


def fetch_district_rollups(district_id):
    """Return {'district': {...}, 'region': {...}, 'employees': [...], 'totals': {...}}."""
    win = _windows()

    def _count_by_employee(start_dt, end_dt):
        rows, _ = query(
            """
            SELECT c.employee_id AS eid, COUNT(c.id) AS cnt
            FROM checkins c
            JOIN employees e ON e.id = c.employee_id
            WHERE c.account_id IS NOT NULL
              AND e.district_id=%s
              AND c.checkin_time BETWEEN %s AND %s
            GROUP BY c.employee_id
            """,
            (district_id, start_dt, end_dt),
        )
        return {int(r["eid"]): int(r["cnt"]) for r in (rows or [])}

    district_rows, _ = query(
        """
        SELECT d.id, d.name, d.code, d.region_id,
               r.id   AS r_id, r.name AS r_name, r.code AS r_code, r.type AS r_type
        FROM districts d
        LEFT JOIN regions r ON r.id = d.region_id
        WHERE d.id=%s
        """,
        (district_id,),
    )
    district = None
    region = None
    if district_rows:
        d0 = district_rows[0]
        district = {"id": d0["id"], "name": d0["name"], "code": d0["code"], "region_id": d0["region_id"]}
        if d0.get("r_id"):
            region = {"id": d0["r_id"], "name": d0["r_name"], "code": d0["r_code"], "type": d0["r_type"]}

    by_period = {p: _count_by_employee(*win[p]) for p in win}
    employees, _ = query(
        """
        SELECT e.id, e.name, e.email, e.territory, e.phone
        FROM employees e
        WHERE e.district_id=%s AND e.role='employee'
        ORDER BY e.name
        """,
        (district_id,),
    )
    out = []
    totals = {"today": 0, "week": 0, "month": 0, "quarter": 0}
    for e in employees or []:
        today_cnt = by_period["day"].get(e["id"], 0)
        week_cnt = by_period["week"].get(e["id"], 0)
        month_cnt = by_period["month"].get(e["id"], 0)
        quarter_cnt = by_period["quarter"].get(e["id"], 0)
        totals["today"] += today_cnt
        totals["week"] += week_cnt
        totals["month"] += month_cnt
        totals["quarter"] += quarter_cnt
        out.append({
            "id": e["id"],
            "name": e["name"],
            "email": e["email"],
            "territory": e["territory"],
            "phone": e["phone"],
            # New names.
            "today": today_cnt,
            "week": week_cnt,
            "month": month_cnt,
            "quarter": quarter_cnt,
            # Legacy aliases.
            "visits_day":     today_cnt,
            "visits_week":    week_cnt,
            "visits_month":   month_cnt,
            "visits_quarter": quarter_cnt,
        })
    return {"district": district, "region": region, "employees": out, "totals": totals}


def fetch_employee_detail(employee_id):
    """Return detail dict with stats (flat ints per period), recent visits and flags.

    stats exposes BOTH a flat int per period for the Drupal Twig template
    (stats.today/week/month/quarter) AND the rich compute_stats() dict under
    stats.day_full/stats.week_full/etc. for callers that need the full shape.
    """
    from api_stats import compute_stats
    rows, _ = query(
        """
        SELECT e.id, e.name, e.email, e.phone, e.territory, e.role,
               r.id AS region_id, r.name AS region_name,
               d.id AS district_id, d.name AS district_name,
               m.id AS manager_id, m.name AS manager_name
        FROM employees e
        LEFT JOIN regions   r ON r.id = e.region_id
        LEFT JOIN districts d ON d.id = e.district_id
        LEFT JOIN employees m ON m.id = e.manager_id
        WHERE e.id=%s
        """,
        (int(employee_id),),
    )
    if not rows:
        return None
    employee = rows[0]
    eid = int(employee_id)
    full_periods = {p: compute_stats(eid, p) for p in ("day", "week", "month", "quarter")}
    stats = {
        "today":   full_periods["day"]["counts"]["total"],
        "week":    full_periods["week"]["counts"]["total"],
        "month":   full_periods["month"]["counts"]["total"],
        "quarter": full_periods["quarter"]["counts"]["total"],
        # Keep the original keyed-by-period rich form available too.
        "day_full":     full_periods["day"],
        "week_full":    full_periods["week"],
        "month_full":   full_periods["month"],
        "quarter_full": full_periods["quarter"],
    }

    recent, _ = query(
        """
        SELECT c.id, c.checkin_time, c.actual_place_name, c.distance_km,
               c.match_score, c.matched, c.outcome, c.visit_notes,
               a.id AS account_id, a.name AS account_name, a.type AS account_type
        FROM checkins c
        LEFT JOIN accounts a ON a.id = c.account_id
        WHERE c.employee_id=%s AND c.account_id IS NOT NULL
        ORDER BY c.checkin_time DESC
        LIMIT 25
        """,
        (eid,),
    )
    for r in recent or []:
        if r.get("checkin_time"):
            r["checkin_time"] = r["checkin_time"].isoformat()

    flags, _ = query(
        """
        SELECT f.id, f.score, f.reason, f.created_at,
               c.actual_place_name, c.checkin_time
        FROM anomaly_flags f
        JOIN checkins c ON c.id = f.checkin_id
        WHERE f.employee_id=%s
        ORDER BY f.created_at DESC
        LIMIT 25
        """,
        (eid,),
    )
    for r in flags or []:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
        if r.get("checkin_time"):
            r["checkin_time"] = r["checkin_time"].isoformat()

    return {
        "employee": employee,
        "stats": stats,
        "recent": recent or [],
        "flags": flags or [],
    }


# -------- endpoints --------

@bp.get("/proctor/india")
@require_drupal
@require_proctor_or_admin
def get_india():
    payload = fetch_india_rollups()
    # Keep 'rows' alias for legacy callers (proctor.html in Flask, older Drupal).
    return jsonify({"ok": True, "rows": payload["regions"], **payload})


@bp.get("/proctor/region/<int:rid>")
@require_drupal
@require_proctor_or_admin
def get_region(rid):
    payload = fetch_region_rollups(rid)
    return jsonify({"ok": True, "rows": payload["districts"], **payload})


@bp.get("/proctor/district/<int:did>")
@require_drupal
@require_proctor_or_admin
def get_district_rollup(did):
    payload = fetch_district_rollups(did)
    return jsonify({"ok": True, "rows": payload["employees"], **payload})


@bp.get("/proctor/employee/<int:eid>")
@require_drupal
@require_proctor_or_admin
def get_employee(eid):
    detail = fetch_employee_detail(eid)
    if not detail:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, **detail})
