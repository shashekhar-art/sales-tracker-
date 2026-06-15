"""Accounts CRUD API blueprint.

Accounts represent the people/places a salesperson visits (doctors, chemists,
stockists). Consumed by both the Flask Jinja UI and the Drupal frontend.

All endpoints (except via app.py internal use) require the standard Drupal
auth headers via @require_drupal — see api.py for header semantics.
"""
from flask import Blueprint, request, jsonify, g

from db import query
from api import require_drupal


bp = Blueprint("accounts", __name__, url_prefix="/api")


ALLOWED_TYPES = ("doctor", "chemist", "stockist", "retailer", "wholesaler")


def _err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def _row_to_dict(row):
    if not row:
        return None
    # Embed district + region name for convenience.
    return row


def fetch_accounts(type_=None, q=None, district_id=None, region_id=None, limit=200):
    """Reusable helper — used by the API and the Flask HTML route."""
    sql = (
        "SELECT a.*, d.name AS district_name, d.region_id, r.name AS region_name "
        "FROM accounts a "
        "LEFT JOIN districts d ON d.id = a.district_id "
        "LEFT JOIN regions   r ON r.id = d.region_id "
        "WHERE 1=1"
    )
    params = []
    if type_ and type_ in ALLOWED_TYPES:
        sql += " AND a.type=%s"
        params.append(type_)
    if district_id:
        sql += " AND a.district_id=%s"
        params.append(int(district_id))
    if region_id:
        sql += " AND d.region_id=%s"
        params.append(int(region_id))
    if q:
        sql += " AND (a.name LIKE %s OR a.specialty LIKE %s OR a.address LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like])
    sql += " ORDER BY a.name LIMIT %s"
    params.append(int(limit))
    rows, _ = query(sql, tuple(params))
    return rows or []


def fetch_account(account_id):
    rows, _ = query(
        "SELECT a.*, d.name AS district_name, d.region_id, r.name AS region_name "
        "FROM accounts a "
        "LEFT JOIN districts d ON d.id = a.district_id "
        "LEFT JOIN regions   r ON r.id = d.region_id "
        "WHERE a.id=%s",
        (int(account_id),),
    )
    return rows[0] if rows else None


def create_account(data, created_by=None):
    name = (data.get("name") or "").strip()
    type_ = (data.get("type") or "").strip().lower()
    if not name:
        raise ValueError("name is required")
    if type_ not in ALLOWED_TYPES:
        raise ValueError("type must be one of doctor|chemist|stockist|retailer|wholesaler")
    specialty = (data.get("specialty") or "").strip() or None
    district_id = data.get("district_id") or None
    address = (data.get("address") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None
    lat = data.get("lat")
    lon = data.get("lon")
    _, new_id = query(
        """
        INSERT INTO accounts
          (name, type, specialty, district_id, address, phone, email, lat, lon, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            name, type_, specialty,
            int(district_id) if district_id else None,
            address, phone, email,
            float(lat) if lat not in (None, "") else None,
            float(lon) if lon not in (None, "") else None,
            int(created_by) if created_by else None,
        ),
        fetch=False, commit=True,
    )
    return new_id


def update_account(account_id, data):
    if not fetch_account(account_id):
        raise LookupError("not found")
    fields = []
    params = []
    for col in ("name", "specialty", "address", "phone", "email"):
        if col in data:
            v = (data.get(col) or "").strip() or None
            fields.append(f"{col}=%s")
            params.append(v)
    if "type" in data:
        t = (data.get("type") or "").strip().lower()
        if t not in ALLOWED_TYPES:
            raise ValueError("type must be one of doctor|chemist|stockist|retailer|wholesaler")
        fields.append("type=%s")
        params.append(t)
    if "district_id" in data:
        fields.append("district_id=%s")
        params.append(int(data["district_id"]) if data["district_id"] not in (None, "") else None)
    for col in ("lat", "lon"):
        if col in data:
            v = data.get(col)
            fields.append(f"{col}=%s")
            params.append(float(v) if v not in (None, "") else None)
    if not fields:
        return
    params.append(int(account_id))
    query(
        f"UPDATE accounts SET {', '.join(fields)} WHERE id=%s",
        tuple(params),
        fetch=False, commit=True,
    )


def delete_account(account_id):
    query("DELETE FROM accounts WHERE id=%s", (int(account_id),),
          fetch=False, commit=True)


# ---------------- HTTP endpoints (Drupal-facing) ----------------

@bp.get("/accounts")
@require_drupal
def list_accounts():
    rows = fetch_accounts(
        type_=request.args.get("type"),
        q=request.args.get("q"),
        district_id=request.args.get("district_id"),
        region_id=request.args.get("region_id"),
        limit=min(int(request.args.get("limit", 200)), 500),
    )
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return jsonify({"ok": True, "rows": rows})


@bp.get("/accounts/<int:account_id>")
@require_drupal
def get_account(account_id):
    row = fetch_account(account_id)
    if not row:
        return _err("not found", 404)
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    # Bundle recent visits for the detail page so the controller doesn't have
    # to make a second request.
    visits, _ = query(
        """
        SELECT c.id, c.checkin_time, c.source, c.actual_place_name,
               c.distance_km, c.match_score, c.matched, c.outcome, c.visit_notes,
               e.id AS employee_id, e.name AS employee_name
        FROM checkins c
        JOIN employees e ON e.id = c.employee_id
        WHERE c.account_id=%s
        ORDER BY c.checkin_time DESC
        LIMIT 50
        """,
        (int(account_id),),
    )
    for v in visits or []:
        if v.get("checkin_time"):
            v["checkin_time"] = v["checkin_time"].isoformat()
    return jsonify({"ok": True, "account": row, "visits": visits or []})


@bp.post("/accounts")
@require_drupal
def post_account():
    data = request.get_json(silent=True) or {}
    try:
        new_id = create_account(data, created_by=g.employee["id"])
    except ValueError as e:
        return _err(str(e))
    return jsonify({"ok": True, "id": new_id})


@bp.put("/accounts/<int:account_id>")
@require_drupal
def put_account(account_id):
    data = request.get_json(silent=True) or {}
    try:
        update_account(account_id, data)
    except LookupError:
        return _err("not found", 404)
    except ValueError as e:
        return _err(str(e))
    return jsonify({"ok": True})


@bp.delete("/accounts/<int:account_id>")
@require_drupal
def del_account(account_id):
    delete_account(account_id)
    return jsonify({"ok": True})
