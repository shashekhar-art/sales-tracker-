"""Stats API blueprint — per-employee period rollups + target achievement."""
from datetime import date, datetime, time, timedelta

from flask import Blueprint, request, jsonify, g

from db import query
from api import require_drupal


bp = Blueprint("stats", __name__, url_prefix="/api")


PERIODS = ("day", "week", "month", "quarter")


def period_window(period, today=None):
    """Return (start_datetime, end_datetime) for the named period anchored at today."""
    today = today or date.today()
    if period == "day":
        start_d = today
        end_d = today
    elif period == "week":
        start_d = today - timedelta(days=today.weekday())  # Monday
        end_d = today
    elif period == "month":
        start_d = today.replace(day=1)
        end_d = today
    elif period == "quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start_d = today.replace(month=q_start_month, day=1)
        end_d = today
    else:
        start_d = today
        end_d = today
    return datetime.combine(start_d, time.min), datetime.combine(end_d, time.max), start_d, end_d


def fetch_period_counts(employee_id, start_dt, end_dt):
    """Returns dict: {total, doctor, chemist, stockist, matched, anomalies}."""
    rows, _ = query(
        """
        SELECT a.type AS account_type, COUNT(*) AS cnt
        FROM checkins c
        JOIN accounts a ON a.id = c.account_id
        WHERE c.employee_id=%s AND c.account_id IS NOT NULL
          AND c.checkin_time BETWEEN %s AND %s
        GROUP BY a.type
        """,
        (employee_id, start_dt, end_dt),
    )
    counts = {"doctor": 0, "chemist": 0, "stockist": 0, "retailer": 0, "wholesaler": 0}
    for r in rows or []:
        if r["account_type"] in counts:
            counts[r["account_type"]] = int(r["cnt"])
    total = sum(counts.values())

    matched_rows, _ = query(
        """
        SELECT COUNT(*) AS cnt FROM checkins c
        WHERE c.employee_id=%s AND c.account_id IS NOT NULL
          AND c.matched=1
          AND c.checkin_time BETWEEN %s AND %s
        """,
        (employee_id, start_dt, end_dt),
    )
    matched = int((matched_rows or [{"cnt": 0}])[0]["cnt"])

    anomaly_rows, _ = query(
        """
        SELECT COUNT(*) AS cnt FROM anomaly_flags
        WHERE employee_id=%s AND created_at BETWEEN %s AND %s
        """,
        (employee_id, start_dt, end_dt),
    )
    anomalies = int((anomaly_rows or [{"cnt": 0}])[0]["cnt"])

    out = dict(counts)
    out["total"] = total
    out["matched"] = matched
    out["anomalies"] = anomalies
    return out


def fetch_period_outcomes(employee_id, start_dt, end_dt):
    """Return dict {met, not_met, rescheduled} of visit outcomes for the period."""
    rows, _ = query(
        """
        SELECT c.outcome, COUNT(*) AS cnt
        FROM checkins c
        WHERE c.employee_id=%s AND c.account_id IS NOT NULL
          AND c.checkin_time BETWEEN %s AND %s
        GROUP BY c.outcome
        """,
        (employee_id, start_dt, end_dt),
    )
    out = {"met": 0, "not_met": 0, "rescheduled": 0}
    for r in rows or []:
        if r["outcome"] in out:
            out[r["outcome"]] = int(r["cnt"])
    return out


def fetch_target(employee_id, period_type, on_date=None):
    """Resolve the most specific applicable target (employee > district > region > company)."""
    on_date = on_date or date.today()
    rows, _ = query(
        """
        SELECT * FROM targets
        WHERE period_type=%s
          AND effective_from <= %s
          AND (effective_to IS NULL OR effective_to >= %s)
          AND (
            (scope='employee' AND employee_id=%s)
            OR (scope='district' AND district_id=(SELECT district_id FROM employees WHERE id=%s))
            OR (scope='region'   AND region_id=(SELECT region_id FROM employees WHERE id=%s))
            OR (scope='company')
          )
        ORDER BY FIELD(scope, 'employee','district','region','company'), effective_from DESC
        LIMIT 1
        """,
        (period_type, on_date, on_date, employee_id, employee_id, employee_id),
    )
    return rows[0] if rows else None


def period_to_target_period(period):
    return {"day": "daily", "week": "weekly", "month": "monthly", "quarter": "quarterly"}.get(period, "daily")


def compute_stats(employee_id, period="day"):
    if period not in PERIODS:
        period = "day"
    start_dt, end_dt, start_d, end_d = period_window(period)
    counts = fetch_period_counts(employee_id, start_dt, end_dt)
    outcomes = fetch_period_outcomes(employee_id, start_dt, end_dt)
    target = fetch_target(employee_id, period_to_target_period(period))
    target_count = int(target["target_count"]) if target else 0
    achievement_pct = (counts["total"] / target_count * 100.0) if target_count > 0 else None
    return {
        "period": period,
        "from": start_d.isoformat(),
        "to": end_d.isoformat(),
        "counts": counts,
        # Flat keys the Drupal Twig reports template (and dashboard period tabs) read.
        "total_visits": counts["total"],
        "by_type": {
            "doctor": counts["doctor"],
            "chemist": counts["chemist"],
            "stockist": counts["stockist"],
        },
        "by_outcome": outcomes,
        "target": {
            "target_count": target_count,
            "scope": target["scope"] if target else None,
            "account_type": target["account_type"] if target else None,
        } if target else None,
        "achievement_pct": round(achievement_pct, 1) if achievement_pct is not None else None,
    }


@bp.get("/stats")
@require_drupal
def get_stats():
    period = request.args.get("period", "day")
    return jsonify({"ok": True, **compute_stats(g.employee["id"], period)})
