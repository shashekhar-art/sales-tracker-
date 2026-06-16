"""JSON API consumed by the Drupal 11 frontend module.

Trust model: Flask trusts Drupal. Every request must carry:
  X-API-Key:        shared secret (config.API_KEY)
  X-Employee-Email: identifies the logged-in Drupal user (auto-provisioned in MySQL)
  X-Employee-Name:  display name (used on first provisioning)
  X-Employee-Role:  "employee" or "admin" (mirrors Drupal role)

Bind Flask to 127.0.0.1 so only the local Drupal instance can reach it.
"""
from datetime import date, datetime
from functools import wraps

from flask import Blueprint, request, jsonify, g

import config
from db import query
from ai.matcher import match
from ai.anomaly import score_checkin

api = Blueprint("api", __name__, url_prefix="/api")


def _err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def _ensure_employee(email, name, role):
    # Normalize role passed from Drupal — preserve admin/proctor/employee as-is.
    role_in = role if role in ("admin", "proctor", "employee") else "employee"
    rows, _ = query("SELECT * FROM employees WHERE email=%s", (email,))
    if rows:
        emp = rows[0]
        # Promote stored role to admin/proctor if Drupal says so; never downgrade
        # an existing admin back to employee just because Drupal sent 'employee'.
        if role_in == "admin" and emp["role"] != "admin":
            query("UPDATE employees SET role='admin' WHERE id=%s",
                  (emp["id"],), fetch=False, commit=True)
            emp["role"] = "admin"
        elif role_in == "proctor" and emp["role"] not in ("admin", "proctor"):
            query("UPDATE employees SET role='proctor' WHERE id=%s",
                  (emp["id"],), fetch=False, commit=True)
            emp["role"] = "proctor"
        return emp
    # auto-provision — keep whichever role Drupal sent (admin/proctor/employee).
    _, new_id = query(
        "INSERT INTO employees (name, email, password_hash, role) VALUES (%s,%s,'drupal-managed',%s)",
        (name or email.split("@")[0], email, role_in),
        fetch=False, commit=True,
    )
    rows, _ = query("SELECT * FROM employees WHERE id=%s", (new_id,))
    return rows[0]


def require_drupal(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != config.API_KEY:
            return _err("invalid api key", 401)
        email = (request.headers.get("X-Employee-Email") or "").strip().lower()
        if not email:
            return _err("missing X-Employee-Email", 400)
        name = request.headers.get("X-Employee-Name") or email
        role = request.headers.get("X-Employee-Role") or "employee"
        g.employee = _ensure_employee(email, name, role)
        return f(*args, **kwargs)
    return wrapper


def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.employee["role"] != "admin":
            return _err("admin only", 403)
        return f(*args, **kwargs)
    return wrapper


@api.get("/health")
def health():
    return jsonify({"ok": True, "service": "sales_tracker"})


@api.get("/plan/today")
@require_drupal
def get_plan_today():
    rows, _ = query(
        "SELECT * FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (g.employee["id"], date.today()),
    )
    plan_row = rows[0] if rows else None
    items = []
    if plan_row:
        item_rows, _ = query(
            """
            SELECT pvi.id, pvi.account_id, pvi.order_idx, pvi.notes,
                   a.name AS account_name, a.type AS account_type,
                   a.address AS account_address,
                   (SELECT COUNT(*) FROM checkins c
                     WHERE c.employee_id=%s AND c.account_id=pvi.account_id
                       AND DATE(c.checkin_time)=%s) AS visited_count
            FROM planned_visit_items pvi
            JOIN accounts a ON a.id = pvi.account_id
            WHERE pvi.plan_id=%s
            ORDER BY pvi.order_idx, pvi.id
            """,
            (g.employee["id"], date.today(), plan_row["id"]),
        )
        for it in item_rows or []:
            items.append({
                "id": it["id"],
                "account_id": it["account_id"],
                "account_name": it["account_name"],
                "account_type": it["account_type"],
                "account_address": it["account_address"],
                "order_idx": it["order_idx"],
                "notes": it["notes"],
                "visited": (it["visited_count"] or 0) > 0,
            })
    return jsonify({"ok": True, "plan": plan_row, "items": items})


@api.post("/plan")
@require_drupal
def post_plan():
    data = request.get_json(silent=True) or {}
    place = (data.get("place") or "").strip()
    account_ids = data.get("account_ids")
    # Backward-compat: if no place AND no accounts, reject. If only accounts supplied,
    # auto-fill the place name so the schema NOT NULL constraint is satisfied.
    if not place and not account_ids:
        return _err("place is required")
    if not place and account_ids:
        place = "(planned accounts)"
    lat = data.get("lat")
    lon = data.get("lon")
    notes = (data.get("notes") or "").strip() or None
    query(
        """
        INSERT INTO planned_visits (employee_id, plan_date, planned_place_name, planned_lat, planned_lon, notes)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT(employee_id, plan_date) DO UPDATE SET
          planned_place_name=excluded.planned_place_name,
          planned_lat=excluded.planned_lat,
          planned_lon=excluded.planned_lon,
          notes=excluded.notes
        """,
        (g.employee["id"], date.today(), place,
         float(lat) if lat not in (None, "") else None,
         float(lon) if lon not in (None, "") else None,
         notes),
        fetch=False, commit=True,
    )
    # Re-fetch the plan id (handles both INSERT and UPDATE branches).
    plan_rows, _ = query(
        "SELECT id FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (g.employee["id"], date.today()),
    )
    plan_id = plan_rows[0]["id"] if plan_rows else None

    # If account_ids was supplied (even as []), replace the items.
    if plan_id is not None and account_ids is not None:
        query("DELETE FROM planned_visit_items WHERE plan_id=%s",
              (plan_id,), fetch=False, commit=True)
        for idx, aid in enumerate(account_ids or []):
            try:
                aid_int = int(aid)
            except (TypeError, ValueError):
                continue
            query(
                "INSERT OR IGNORE INTO planned_visit_items (plan_id, account_id, order_idx) VALUES (%s,%s,%s)",
                (plan_id, aid_int, idx),
                fetch=False, commit=True,
            )

    return jsonify({"ok": True, "plan_id": plan_id})


@api.post("/checkin")
@require_drupal
def post_checkin():
    data = request.get_json(silent=True) or {}
    source = data.get("source", "manual")
    if source not in ("manual", "gps"):
        return _err("source must be manual or gps")
    actual_name = (data.get("actual_place_name") or "").strip() or None
    lat = data.get("lat")
    lon = data.get("lon")
    if source == "gps" and (lat in (None, "") or lon in (None, "")):
        return _err("GPS source requires lat and lon")
    if source == "manual" and not actual_name:
        return _err("Manual source requires actual_place_name")

    # Optional visit-linkage fields
    account_id = data.get("account_id")
    outcome = data.get("outcome") or None
    if outcome and outcome not in ("met", "not_met", "rescheduled"):
        return _err("outcome must be met|not_met|rescheduled")
    visit_notes = (data.get("visit_notes") or "").strip() or None

    rows, _ = query(
        "SELECT * FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (g.employee["id"], date.today()),
    )
    if not rows:
        return _err("No plan declared for today", 409)
    plan_row = rows[0]

    actual = {
        "name": actual_name,
        "lat": float(lat) if lat not in (None, "") else None,
        "lon": float(lon) if lon not in (None, "") else None,
    }
    planned = {
        "name": plan_row["planned_place_name"],
        "lat": plan_row["planned_lat"],
        "lon": plan_row["planned_lon"],
    }
    result = match(planned, actual)
    if actual["lat"] is None and result["actual_coords"]:
        actual["lat"], actual["lon"] = result["actual_coords"]

    now = datetime.now()
    _, checkin_id = query(
        """
        INSERT INTO checkins
          (employee_id, plan_id, checkin_time, source, actual_place_name,
           actual_lat, actual_lon, distance_km, text_similarity, match_score, matched,
           account_id, outcome, visit_notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (g.employee["id"], plan_row["id"], now, source, actual["name"],
         actual["lat"], actual["lon"],
         result["distance_km"], result["text_similarity"], result["match_score"],
         1 if result["matched"] else 0,
         int(account_id) if account_id else None,
         outcome,
         visit_notes),
        fetch=False, commit=True,
    )

    anomaly = score_checkin(g.employee["id"], {
        "distance_km": result["distance_km"],
        "text_similarity": result["text_similarity"],
        "match_score": result["match_score"],
        "checkin_time": now,
    })
    if anomaly["is_anomaly"]:
        query(
            "INSERT INTO anomaly_flags (employee_id, checkin_id, score, reason) VALUES (%s,%s,%s,%s)",
            (g.employee["id"], checkin_id, anomaly["score"], anomaly["reason"]),
            fetch=False, commit=True,
        )

    return jsonify({
        "ok": True,
        "checkin_id": checkin_id,
        "match": {
            "distance_km": result["distance_km"],
            "text_similarity": result["text_similarity"],
            "match_score": result["match_score"],
            "matched": result["matched"],
        },
        "anomaly": anomaly,
    })


@api.get("/history")
@require_drupal
def get_history():
    limit = min(int(request.args.get("limit", 50)), 200)
    rows, _ = query(
        """
        SELECT c.id, c.checkin_time, c.source, c.actual_place_name,
               c.distance_km, c.text_similarity, c.match_score, c.matched,
               p.planned_place_name, p.plan_date
        FROM checkins c
        LEFT JOIN planned_visits p ON p.id = c.plan_id
        WHERE c.employee_id=%s
        ORDER BY c.checkin_time DESC
        LIMIT %s
        """,
        (g.employee["id"], limit),
    )
    for r in rows or []:
        r["checkin_time"] = r["checkin_time"].isoformat() if r["checkin_time"] else None
        r["plan_date"] = r["plan_date"].isoformat() if r["plan_date"] else None
    return jsonify({"ok": True, "rows": rows or []})


@api.get("/admin/summary")
@require_drupal
@require_admin
def admin_summary():
    today = date.today()
    rows, _ = query(
        """
        SELECT e.id, e.name, e.email,
               p.planned_place_name,
               (SELECT COUNT(*) FROM checkins c
                  WHERE c.employee_id=e.id AND DATE(c.checkin_time)=%s) AS today_checkins,
               (SELECT MAX(c.match_score) FROM checkins c
                  WHERE c.employee_id=e.id AND DATE(c.checkin_time)=%s) AS best_score_today
        FROM employees e
        LEFT JOIN planned_visits p ON p.employee_id=e.id AND p.plan_date=%s
        WHERE e.role='employee'
        ORDER BY e.name
        """,
        (today, today, today),
    )
    return jsonify({"ok": True, "rows": rows or []})


@api.get("/admin/flags")
@require_drupal
@require_admin
def admin_flags():
    rows, _ = query(
        """
        SELECT f.id, f.score, f.reason, f.created_at,
               e.name AS employee_name, e.email,
               c.actual_place_name, c.checkin_time
        FROM anomaly_flags f
        JOIN employees e ON e.id = f.employee_id
        JOIN checkins   c ON c.id = f.checkin_id
        ORDER BY f.created_at DESC
        LIMIT 50
        """
    )
    for r in rows or []:
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
        r["checkin_time"] = r["checkin_time"].isoformat() if r["checkin_time"] else None
    return jsonify({"ok": True, "rows": rows or []})
