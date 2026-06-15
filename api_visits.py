"""Visits API blueprint.

A "visit" is a `checkin` row with a non-null `account_id`. It links a
salesperson's check-in to a specific account (doctor/chemist/stockist) and
carries an outcome (met / not_met / rescheduled) and free-form visit notes.

Distance is computed from the account's lat/lon (if available) using the
existing geopy geodesic helper. match_score = max(0, 1 - dist / threshold).
"""
from datetime import date, datetime, time

from flask import Blueprint, request, jsonify, g
from geopy.distance import geodesic

import config
from db import query
from api import require_drupal


bp = Blueprint("visits", __name__, url_prefix="/api")


ALLOWED_OUTCOMES = ("met", "not_met", "rescheduled")
ALLOWED_SOURCES = ("gps", "manual")


def _err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def fetch_account(account_id):
    rows, _ = query("SELECT * FROM accounts WHERE id=%s", (int(account_id),))
    return rows[0] if rows else None


def get_or_create_today_plan(employee_id, today=None):
    """Get the planned_visits row for today; create a stub if needed.

    Stub gets a placeholder place_name so the schema NOT NULL constraint is satisfied.
    """
    today = today or date.today()
    rows, _ = query(
        "SELECT * FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (employee_id, today),
    )
    if rows:
        return rows[0]
    _, plan_id = query(
        """
        INSERT INTO planned_visits (employee_id, plan_date, planned_place_name)
        VALUES (%s,%s,%s)
        """,
        (employee_id, today, "(field visits)"),
        fetch=False, commit=True,
    )
    rows, _ = query("SELECT * FROM planned_visits WHERE id=%s", (plan_id,))
    return rows[0]


def log_visit(employee_id, data):
    """Insert a visit (a checkin with account_id set). Returns dict with details."""
    account_id = data.get("account_id")
    if not account_id:
        raise ValueError("account_id is required")
    account = fetch_account(account_id)
    if not account:
        raise LookupError("account not found")

    source = (data.get("source") or "manual").strip().lower()
    if source not in ALLOWED_SOURCES:
        raise ValueError("source must be gps or manual")

    outcome = data.get("outcome") or None
    if outcome and outcome not in ALLOWED_OUTCOMES:
        raise ValueError("outcome must be met|not_met|rescheduled")

    lat = data.get("lat")
    lon = data.get("lon")
    if source == "gps" and (lat in (None, "") or lon in (None, "")):
        raise ValueError("GPS source requires lat and lon")

    actual_lat = float(lat) if lat not in (None, "") else None
    actual_lon = float(lon) if lon not in (None, "") else None
    actual_name = (data.get("actual_place_name") or account["name"]).strip() or account["name"]
    visit_notes = (data.get("visit_notes") or data.get("notes") or "").strip() or None

    plan_row = get_or_create_today_plan(employee_id)

    # distance + match_score against the account location.
    distance_km = None
    match_score = None
    text_similarity = None
    if actual_lat is not None and actual_lon is not None and account.get("lat") is not None and account.get("lon") is not None:
        try:
            distance_km = geodesic(
                (actual_lat, actual_lon),
                (float(account["lat"]), float(account["lon"]))
            ).km
            ms = 1.0 - (distance_km / config.GEO_THRESHOLD_KM)
            match_score = max(0.0, min(1.0, ms))
        except Exception:
            distance_km = None
            match_score = None
    else:
        # Account has no lat/lon — fall back to text similarity between the
        # actual place name and the account's name so the visit still gets
        # a match_score and the admin status row doesn't stay 'Awaiting'.
        try:
            from ai.matcher import match as _match
            r = _match(
                {"name": account.get("name"), "lat": None, "lon": None},
                {"name": actual_name, "lat": actual_lat, "lon": actual_lon},
            )
            text_similarity = r.get("text_similarity")
            match_score = r.get("match_score")
            distance_km = r.get("distance_km")
        except Exception:
            pass

    matched = 1 if (match_score is not None and match_score >= config.MATCH_THRESHOLD) else 0
    now = datetime.now()
    selfie_path = data.get("selfie_path") or None
    _, checkin_id = query(
        """
        INSERT INTO checkins
          (employee_id, plan_id, checkin_time, source, actual_place_name,
           actual_lat, actual_lon, distance_km, text_similarity, match_score,
           matched, account_id, outcome, visit_notes, selfie_path)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            employee_id, plan_row["id"], now, source, actual_name,
            actual_lat, actual_lon,
            round(distance_km, 3) if distance_km is not None else None,
            text_similarity,
            round(match_score, 3) if match_score is not None else None,
            matched,
            int(account_id),
            outcome,
            visit_notes,
            selfie_path,
        ),
        fetch=False, commit=True,
    )
    return {
        "checkin_id": checkin_id,
        "account_id": int(account_id),
        "distance_km": round(distance_km, 3) if distance_km is not None else None,
        "match_score": round(match_score, 3) if match_score is not None else None,
        "matched": bool(matched),
        "outcome": outcome,
        "checkin_time": now,
    }


def fetch_visits(employee_id, from_date=None, to_date=None, account_type=None,
                 account_id=None, outcome=None, limit=200):
    sql = (
        "SELECT c.id, c.checkin_time, c.source, c.actual_place_name, c.actual_lat, c.actual_lon, "
        "       c.distance_km, c.match_score, c.matched, c.outcome, c.visit_notes, c.selfie_path, "
        "       a.id AS account_id, a.name AS account_name, a.type AS account_type, "
        "       a.specialty AS account_specialty, a.address AS account_address, "
        "       d.name AS district_name "
        "FROM checkins c "
        "JOIN accounts a ON a.id = c.account_id "
        "LEFT JOIN districts d ON d.id = a.district_id "
        "WHERE c.employee_id=%s AND c.account_id IS NOT NULL"
    )
    params = [employee_id]
    if from_date:
        sql += " AND c.checkin_time >= %s"
        params.append(from_date)
    if to_date:
        sql += " AND c.checkin_time <= %s"
        params.append(to_date)
    if account_type:
        sql += " AND a.type=%s"
        params.append(account_type)
    if account_id:
        sql += " AND c.account_id=%s"
        params.append(int(account_id))
    if outcome:
        sql += " AND c.outcome=%s"
        params.append(outcome)
    sql += " ORDER BY c.checkin_time DESC LIMIT %s"
    params.append(int(limit))
    rows, _ = query(sql, tuple(params))
    return rows or []


def fetch_today_visits(employee_id):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    rows = fetch_visits(employee_id, from_date=start, to_date=end, limit=500)
    return rows


def fetch_today_planned_items(employee_id):
    """Return today's planned_visit_items with account info embedded + visited flag."""
    today = date.today()
    rows, _ = query(
        "SELECT id FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (employee_id, today),
    )
    if not rows:
        return []
    plan_id = rows[0]["id"]
    items, _ = query(
        """
        SELECT pvi.id, pvi.account_id, pvi.order_idx, pvi.notes,
               a.name AS account_name, a.type AS account_type, a.address AS account_address,
               a.specialty AS account_specialty, a.lat AS account_lat, a.lon AS account_lon,
               d.name AS district_name,
               (SELECT COUNT(*) FROM checkins c
                 WHERE c.employee_id=%s AND c.account_id=pvi.account_id
                   AND DATE(c.checkin_time)=%s) AS visited_count
        FROM planned_visit_items pvi
        JOIN accounts a ON a.id = pvi.account_id
        LEFT JOIN districts d ON d.id = a.district_id
        WHERE pvi.plan_id=%s
        ORDER BY pvi.order_idx, pvi.id
        """,
        (employee_id, today, plan_id),
    )
    out = []
    for it in items or []:
        out.append({
            "id": it["id"],
            "account_id": it["account_id"],
            "order_idx": it["order_idx"],
            "notes": it["notes"],
            "account_name": it["account_name"],
            "account_type": it["account_type"],
            "account_address": it["account_address"],
            "account_specialty": it["account_specialty"],
            "account_lat": it["account_lat"],
            "account_lon": it["account_lon"],
            "district_name": it["district_name"],
            "visited": (it["visited_count"] or 0) > 0,
        })
    return out


# -------- HTTP endpoints --------

@bp.post("/visits")
@require_drupal
def post_visit():
    """Accepts either JSON (no file) or multipart/form-data (with optional 'selfie' file).
    The multipart form is what Drupal posts when the user attached a proof selfie."""
    if request.content_type and request.content_type.startswith("multipart/"):
        data = {k: v for k, v in request.form.items()}
        f = request.files.get("selfie")
        if f and f.filename:
            import os
            from werkzeug.utils import secure_filename
            from flask import current_app
            ext = (os.path.splitext(f.filename)[1] or ".jpg").lower()
            if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                ext = ".jpg"
            folder = os.path.join(current_app.static_folder, "uploads", "selfies", str(g.employee["id"]))
            os.makedirs(folder, exist_ok=True)
            fname = secure_filename(datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ext)
            f.save(os.path.join(folder, fname))
            data["selfie_path"] = f"uploads/selfies/{g.employee['id']}/{fname}"
    else:
        data = request.get_json(silent=True) or {}
    try:
        result = log_visit(g.employee["id"], data)
    except LookupError as e:
        return _err(str(e), 404)
    except ValueError as e:
        return _err(str(e))
    result["checkin_time"] = result["checkin_time"].isoformat()
    return jsonify({"ok": True, **result})


@bp.get("/visits")
@require_drupal
def list_visits():
    def _parse(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except ValueError:
                return None
    aid = request.args.get("account_id")
    rows = fetch_visits(
        g.employee["id"],
        from_date=_parse(request.args.get("from")),
        to_date=_parse(request.args.get("to")),
        account_type=request.args.get("account_type"),
        account_id=int(aid) if aid and str(aid).isdigit() else None,
        outcome=request.args.get("outcome") or None,
        limit=min(int(request.args.get("limit", 200)), 1000),
    )
    for r in rows:
        if r.get("checkin_time"):
            r["checkin_time"] = r["checkin_time"].isoformat()
    return jsonify({"ok": True, "rows": rows})


@bp.get("/visits/today")
@require_drupal
def list_today_visits():
    rows = fetch_today_visits(g.employee["id"])
    counts = {"doctor": 0, "chemist": 0, "stockist": 0, "retailer": 0, "wholesaler": 0, "total": 0}
    for r in rows:
        if r.get("checkin_time"):
            r["checkin_time"] = r["checkin_time"].isoformat()
        t = r.get("account_type")
        if t in counts:
            counts[t] += 1
            counts["total"] += 1
    return jsonify({"ok": True, "rows": rows, "counts": counts})
