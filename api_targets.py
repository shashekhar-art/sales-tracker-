"""Targets API blueprint — admin-only CRUD over the targets table.

The targets table is read by api_stats.fetch_target which resolves the most
specific applicable row for a (employee, period). This blueprint lets the
Drupal TargetForm POST a new row and list existing rows.
"""
from datetime import date

from flask import Blueprint, request, jsonify, g

from db import query
from api import require_drupal, require_admin


bp = Blueprint("targets", __name__, url_prefix="/api")


ALLOWED_SCOPES = ("company", "region", "district", "employee")
ALLOWED_PERIODS = ("daily", "weekly", "monthly", "quarterly")
ALLOWED_ACCOUNT_TYPES = ("any", "doctor", "chemist", "stockist")


def _err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def _parse_date(s):
    if not s:
        return None
    if isinstance(s, date):
        return s
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def insert_target(data):
    scope = (data.get("scope") or "").strip().lower()
    if scope not in ALLOWED_SCOPES:
        raise ValueError("scope must be one of company|region|district|employee")
    period_type = (data.get("period_type") or "").strip().lower()
    if period_type not in ALLOWED_PERIODS:
        raise ValueError("period_type must be one of daily|weekly|monthly|quarterly")
    account_type = (data.get("account_type") or "any").strip().lower()
    if account_type not in ALLOWED_ACCOUNT_TYPES:
        raise ValueError("account_type must be one of any|doctor|chemist|stockist")
    try:
        target_count = int(data.get("target_count") or 0)
    except (TypeError, ValueError):
        raise ValueError("target_count must be an integer")
    if target_count < 0:
        raise ValueError("target_count must be >= 0")

    effective_from = _parse_date(data.get("effective_from")) or date.today()
    effective_to = _parse_date(data.get("effective_to"))

    employee_id = data.get("employee_id") or None
    region_id = data.get("region_id") or None
    district_id = data.get("district_id") or None

    if scope == "employee" and not employee_id:
        raise ValueError("employee_id is required for an employee-scoped target")
    if scope == "region" and not region_id:
        raise ValueError("region_id is required for a region-scoped target")
    if scope == "district" and not district_id:
        raise ValueError("district_id is required for a district-scoped target")

    _, new_id = query(
        """
        INSERT INTO targets
          (scope, employee_id, region_id, district_id, account_type,
           period_type, target_count, effective_from, effective_to)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            scope,
            int(employee_id) if employee_id else None,
            int(region_id) if region_id else None,
            int(district_id) if district_id else None,
            account_type,
            period_type,
            target_count,
            effective_from,
            effective_to,
        ),
        fetch=False, commit=True,
    )
    return new_id


def fetch_targets(scope=None, period_type=None, employee_id=None,
                  district_id=None, region_id=None, limit=200):
    sql = (
        "SELECT t.*, e.name AS employee_name, r.name AS region_name, d.name AS district_name "
        "FROM targets t "
        "LEFT JOIN employees e ON e.id = t.employee_id "
        "LEFT JOIN regions   r ON r.id = t.region_id "
        "LEFT JOIN districts d ON d.id = t.district_id "
        "WHERE 1=1"
    )
    params = []
    if scope:
        sql += " AND t.scope=%s"
        params.append(scope)
    if period_type:
        sql += " AND t.period_type=%s"
        params.append(period_type)
    if employee_id:
        sql += " AND t.employee_id=%s"
        params.append(int(employee_id))
    if district_id:
        sql += " AND t.district_id=%s"
        params.append(int(district_id))
    if region_id:
        sql += " AND t.region_id=%s"
        params.append(int(region_id))
    sql += " ORDER BY t.effective_from DESC, t.id DESC LIMIT %s"
    params.append(int(limit))
    rows, _ = query(sql, tuple(params))
    out = []
    for r in rows or []:
        if r.get("effective_from"):
            r["effective_from"] = r["effective_from"].isoformat()
        if r.get("effective_to"):
            r["effective_to"] = r["effective_to"].isoformat()
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
        out.append(r)
    return out


@bp.post("/targets")
@require_drupal
@require_admin
def post_target():
    data = request.get_json(silent=True) or {}
    try:
        new_id = insert_target(data)
    except ValueError as e:
        return _err(str(e))
    return jsonify({"ok": True, "id": new_id})


@bp.get("/targets")
@require_drupal
@require_admin
def get_targets():
    rows = fetch_targets(
        scope=request.args.get("scope"),
        period_type=request.args.get("period_type"),
        employee_id=request.args.get("employee_id"),
        district_id=request.args.get("district_id"),
        region_id=request.args.get("region_id"),
        limit=min(int(request.args.get("limit", 200)), 500),
    )
    return jsonify({"ok": True, "rows": rows})
