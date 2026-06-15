"""Reports API blueprint — CSV downloads."""
import csv
import io
from datetime import datetime

from flask import Blueprint, request, Response, g

from db import query
from api import require_drupal


bp = Blueprint("reports", __name__, url_prefix="/api")


def _parse_date(s, end=False):
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def build_visits_csv(employee_id, from_dt=None, to_dt=None, role="employee"):
    """Build CSV of visits. Admin/proctor sees everyone, employee sees own only."""
    if role in ("admin", "proctor"):
        sql = (
            "SELECT c.id, c.checkin_time, c.source, c.actual_place_name, "
            "       c.actual_lat, c.actual_lon, c.distance_km, c.match_score, "
            "       c.matched, c.outcome, c.visit_notes, "
            "       e.name AS employee_name, e.email AS employee_email, "
            "       a.name AS account_name, a.type AS account_type, "
            "       a.specialty AS account_specialty, a.address AS account_address, "
            "       d.name AS district_name, r.name AS region_name "
            "FROM checkins c "
            "JOIN accounts a   ON a.id = c.account_id "
            "JOIN employees e  ON e.id = c.employee_id "
            "LEFT JOIN districts d ON d.id = a.district_id "
            "LEFT JOIN regions   r ON r.id = d.region_id "
            "WHERE c.account_id IS NOT NULL"
        )
        params = []
    else:
        sql = (
            "SELECT c.id, c.checkin_time, c.source, c.actual_place_name, "
            "       c.actual_lat, c.actual_lon, c.distance_km, c.match_score, "
            "       c.matched, c.outcome, c.visit_notes, "
            "       e.name AS employee_name, e.email AS employee_email, "
            "       a.name AS account_name, a.type AS account_type, "
            "       a.specialty AS account_specialty, a.address AS account_address, "
            "       d.name AS district_name, r.name AS region_name "
            "FROM checkins c "
            "JOIN accounts a   ON a.id = c.account_id "
            "JOIN employees e  ON e.id = c.employee_id "
            "LEFT JOIN districts d ON d.id = a.district_id "
            "LEFT JOIN regions   r ON r.id = d.region_id "
            "WHERE c.account_id IS NOT NULL AND c.employee_id=%s"
        )
        params = [employee_id]
    if from_dt:
        sql += " AND c.checkin_time >= %s"
        params.append(from_dt)
    if to_dt:
        sql += " AND c.checkin_time <= %s"
        params.append(to_dt)
    sql += " ORDER BY c.checkin_time DESC"

    rows, _ = query(sql, tuple(params))
    rows = rows or []

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "checkin_time", "employee_name", "employee_email",
        "account_name", "account_type", "account_specialty", "account_address",
        "district", "region", "source", "actual_place_name",
        "actual_lat", "actual_lon", "distance_km", "match_score", "matched",
        "outcome", "visit_notes",
    ])
    for r in rows:
        writer.writerow([
            r["id"],
            r["checkin_time"].isoformat() if r["checkin_time"] else "",
            r["employee_name"] or "",
            r["employee_email"] or "",
            r["account_name"] or "",
            r["account_type"] or "",
            r["account_specialty"] or "",
            r["account_address"] or "",
            r["district_name"] or "",
            r["region_name"] or "",
            r["source"] or "",
            r["actual_place_name"] or "",
            r["actual_lat"] if r["actual_lat"] is not None else "",
            r["actual_lon"] if r["actual_lon"] is not None else "",
            r["distance_km"] if r["distance_km"] is not None else "",
            r["match_score"] if r["match_score"] is not None else "",
            "yes" if r["matched"] else "no",
            r["outcome"] or "",
            r["visit_notes"] or "",
        ])
    return buf.getvalue()


def build_accounts_csv(role="employee", employee_id=None):
    rows, _ = query(
        """
        SELECT a.id, a.name, a.type, a.specialty, a.address, a.phone, a.email,
               a.lat, a.lon, a.created_at,
               d.name AS district_name, r.name AS region_name,
               e.name AS created_by_name
        FROM accounts a
        LEFT JOIN districts d ON d.id = a.district_id
        LEFT JOIN regions   r ON r.id = d.region_id
        LEFT JOIN employees e ON e.id = a.created_by
        ORDER BY a.name
        """
    )
    rows = rows or []
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "name", "type", "specialty", "district", "region",
        "address", "phone", "email", "lat", "lon", "created_by", "created_at",
    ])
    for r in rows:
        writer.writerow([
            r["id"], r["name"] or "", r["type"] or "", r["specialty"] or "",
            r["district_name"] or "", r["region_name"] or "",
            r["address"] or "", r["phone"] or "", r["email"] or "",
            r["lat"] if r["lat"] is not None else "",
            r["lon"] if r["lon"] is not None else "",
            r["created_by_name"] or "",
            r["created_at"].isoformat() if r["created_at"] else "",
        ])
    return buf.getvalue()


@bp.get("/reports/csv")
@require_drupal
def reports_csv():
    rtype = (request.args.get("type") or "visits").strip().lower()
    if rtype == "accounts":
        body = build_accounts_csv(role=g.employee["role"], employee_id=g.employee["id"])
        fname = "accounts.csv"
    else:
        body = build_visits_csv(
            g.employee["id"],
            from_dt=_parse_date(request.args.get("from")),
            to_dt=_parse_date(request.args.get("to"), end=True),
            role=g.employee["role"],
        )
        fname = "visits.csv"
    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
