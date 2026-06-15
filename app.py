from datetime import date, datetime, time, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort,
    Response
)
from werkzeug.security import check_password_hash, generate_password_hash

import config
from db import query
from ai.matcher import match
from ai.anomaly import score_checkin
from api import api as api_blueprint
import api_accounts
import api_visits
import api_geo
import api_stats
import api_proctor
import api_reports
import api_targets

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET
app.register_blueprint(api_blueprint)
app.register_blueprint(api_accounts.bp)
app.register_blueprint(api_visits.bp)
app.register_blueprint(api_geo.bp)
app.register_blueprint(api_stats.bp)
app.register_blueprint(api_proctor.bp)
app.register_blueprint(api_reports.bp)
app.register_blueprint(api_targets.bp)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def proctor_required(f):
    """Allow admin OR proctor."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") not in ("admin", "proctor"):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        rows, _ = query("SELECT * FROM employees WHERE email=%s", (email,))
        user = rows[0] if rows else None
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("admin" if user["role"] == "admin" else "dashboard"))
        flash("Invalid credentials", "error")
    return render_template("login.html")


def _save_selfie(employee_id):
    """Save an uploaded visit selfie to static/uploads/selfies/{employee_id}/
    and return its path relative to the app root (e.g. 'uploads/selfies/7/1734-...jpg').
    Returns None when no usable file was uploaded.
    """
    import os
    from werkzeug.utils import secure_filename
    f = request.files.get("selfie")
    if not f or not f.filename:
        return None
    # Accept jpeg/png only; webcam captures arrive as image/jpeg blobs.
    ext = (os.path.splitext(f.filename)[1] or ".jpg").lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    folder_abs = os.path.join(app.static_folder, "uploads", "selfies", str(employee_id))
    os.makedirs(folder_abs, exist_ok=True)
    fname = secure_filename(datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ext)
    f.save(os.path.join(folder_abs, fname))
    return f"uploads/selfies/{employee_id}/{fname}"


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    form = {"name": "", "email": ""}
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        login = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        form["name"], form["email"] = name, login
        if not name or not login or not password:
            flash("Name, username, and password are required.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            existing, _ = query("SELECT id FROM employees WHERE email=%s", (login,))
            if existing:
                flash("That username or email is already taken.", "error")
            else:
                pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
                query(
                    "INSERT INTO employees (name, email, password_hash, role) VALUES (%s, %s, %s, 'employee')",
                    (name, login, pw_hash),
                    fetch=False, commit=True,
                )
                rows, _ = query("SELECT id, name, role FROM employees WHERE email=%s", (login,))
                u = rows[0]
                session["user_id"] = u["id"]
                session["name"] = u["name"]
                session["role"] = u["role"]
                flash("Welcome aboard! Your account is ready.", "ok")
                return redirect(url_for("dashboard"))
    return render_template("register.html", form=form)


@app.route("/api/reverse_geocode")
@login_required
def api_reverse_geocode():
    """Turn (lat, lon) into a human-readable address for the form to display."""
    from ai.matcher import reverse_geocode
    from flask import jsonify
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "lat/lon required"}), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"ok": False, "error": "lat/lon out of range"}), 400
    address = reverse_geocode(lat, lon)
    if not address:
        return jsonify({"ok": False, "error": "address lookup unavailable"}), 502
    return jsonify({"ok": True, "address": address, "lat": lat, "lon": lon})


@app.route("/plan", methods=["GET", "POST"])
@login_required
def plan():
    today = date.today()
    if request.method == "POST":
        place = request.form.get("place", "").strip()
        lat = request.form.get("lat") or None
        lon = request.form.get("lon") or None
        notes = request.form.get("notes", "").strip() or None
        account_ids_raw = request.form.getlist("account_ids")
        # Allow accounts-only plans: synthesize a placeholder name.
        if not place and account_ids_raw:
            place = "(planned accounts)"
        if not place:
            flash("Place is required", "error")
            return redirect(url_for("plan"))
        query(
            """
            INSERT INTO planned_visits (employee_id, plan_date, planned_place_name, planned_lat, planned_lon, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              planned_place_name=VALUES(planned_place_name),
              planned_lat=VALUES(planned_lat),
              planned_lon=VALUES(planned_lon),
              notes=VALUES(notes)
            """,
            (session["user_id"], today, place,
             float(lat) if lat else None,
             float(lon) if lon else None,
             notes),
            fetch=False, commit=True,
        )
        # Resolve the plan id (covers both INSERT and UPDATE).
        prows, _ = query(
            "SELECT id FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
            (session["user_id"], today),
        )
        plan_id = prows[0]["id"] if prows else None
        # If the form posted any account_ids field at all, replace the items.
        if plan_id is not None and "account_ids" in request.form:
            query("DELETE FROM planned_visit_items WHERE plan_id=%s",
                  (plan_id,), fetch=False, commit=True)
            for idx, aid in enumerate(account_ids_raw):
                try:
                    aid_int = int(aid)
                except (TypeError, ValueError):
                    continue
                query(
                    "INSERT IGNORE INTO planned_visit_items (plan_id, account_id, order_idx) VALUES (%s,%s,%s)",
                    (plan_id, aid_int, idx),
                    fetch=False, commit=True,
                )
        flash("Plan saved for today.", "ok")
        return redirect(url_for("dashboard"))

    rows, _ = query(
        "SELECT * FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (session["user_id"], today),
    )
    existing = rows[0] if rows else None
    selected_ids = set()
    if existing:
        sel_rows, _ = query(
            "SELECT account_id FROM planned_visit_items WHERE plan_id=%s",
            (existing["id"],),
        )
        selected_ids = {r["account_id"] for r in (sel_rows or [])}
    # Account list for the multi-picker (used by Jinja). District list for filtering.
    from api_accounts import fetch_accounts
    from api_geo import fetch_all_districts
    accounts = fetch_accounts(limit=500)
    districts = fetch_all_districts()
    return render_template(
        "plan.html",
        existing=existing,
        today=today,
        accounts=accounts,
        districts=districts,
        selected_ids=selected_ids,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin"))
    if session.get("role") == "proctor":
        return redirect(url_for("proctor_index"))
    today = date.today()
    rows, _ = query(
        "SELECT * FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (session["user_id"], today),
    )
    plan_row = rows[0] if rows else None

    history, _ = query(
        """
        SELECT c.*, p.planned_place_name
        FROM checkins c
        LEFT JOIN planned_visits p ON p.id = c.plan_id
        WHERE c.employee_id=%s
        ORDER BY c.checkin_time DESC
        LIMIT 10
        """,
        (session["user_id"],),
    )
    flags, _ = query(
        """
        SELECT f.*, c.actual_place_name
        FROM anomaly_flags f
        JOIN checkins c ON c.id = f.checkin_id
        WHERE f.employee_id=%s
        ORDER BY f.created_at DESC LIMIT 5
        """,
        (session["user_id"],),
    )

    # New v2 widgets: today metrics, planned items, period tabs.
    from api_visits import fetch_today_planned_items
    from api_stats import compute_stats

    planned_items = fetch_today_planned_items(session["user_id"])

    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    type_rows, _ = query(
        """
        SELECT a.type AS account_type, COUNT(*) AS cnt
        FROM checkins c JOIN accounts a ON a.id = c.account_id
        WHERE c.employee_id=%s AND c.account_id IS NOT NULL
          AND c.checkin_time BETWEEN %s AND %s
        GROUP BY a.type
        """,
        (session["user_id"], start, end),
    )
    today_metrics = {"doctor": 0, "chemist": 0, "stockist": 0, "retailer": 0, "wholesaler": 0, "total": 0}
    for r in type_rows or []:
        if r["account_type"] in today_metrics:
            today_metrics[r["account_type"]] = int(r["cnt"])
            today_metrics["total"] += int(r["cnt"])

    # Period stats — default to "day" but honour ?period=
    active_period = request.args.get("period", "day")
    if active_period not in ("day", "week", "month", "quarter"):
        active_period = "day"
    period_stats = compute_stats(session["user_id"], active_period)

    return render_template(
        "dashboard.html",
        plan=plan_row,
        history=history or [],
        flags=flags or [],
        planned_items=planned_items,
        today_metrics=today_metrics,
        active_period=active_period,
        period_stats=period_stats,
    )


@app.route("/checkin", methods=["POST"])
@login_required
def checkin():
    today = date.today()
    rows, _ = query(
        "SELECT * FROM planned_visits WHERE employee_id=%s AND plan_date=%s",
        (session["user_id"], today),
    )
    if not rows:
        flash("Please declare today's plan before checking in.", "error")
        return redirect(url_for("plan"))
    plan_row = rows[0]

    source = request.form.get("source", "manual")
    actual_name = request.form.get("actual_place_name", "").strip()
    lat = request.form.get("lat") or None
    lon = request.form.get("lon") or None

    if source == "gps" and (not lat or not lon):
        flash("GPS coordinates missing.", "error")
        return redirect(url_for("dashboard"))
    if source == "manual" and not actual_name:
        flash("Please type your current place.", "error")
        return redirect(url_for("dashboard"))

    actual = {
        "name": actual_name or None,
        "lat": float(lat) if lat else None,
        "lon": float(lon) if lon else None,
    }
    planned = {
        "name": plan_row["planned_place_name"],
        "lat": plan_row["planned_lat"],
        "lon": plan_row["planned_lon"],
    }
    result = match(planned, actual)

    # If we resolved actual coords via geocoding and none were provided, persist them.
    if actual["lat"] is None and result["actual_coords"]:
        actual["lat"], actual["lon"] = result["actual_coords"]

    now = datetime.now()
    _, checkin_id = query(
        """
        INSERT INTO checkins
          (employee_id, plan_id, checkin_time, source, actual_place_name,
           actual_lat, actual_lon, distance_km, text_similarity, match_score, matched)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (session["user_id"], plan_row["id"], now, source, actual["name"],
         actual["lat"], actual["lon"],
         result["distance_km"], result["text_similarity"], result["match_score"],
         1 if result["matched"] else 0),
        fetch=False, commit=True,
    )

    anomaly = score_checkin(session["user_id"], {
        "distance_km": result["distance_km"],
        "text_similarity": result["text_similarity"],
        "match_score": result["match_score"],
        "checkin_time": now,
    })
    if anomaly["is_anomaly"]:
        query(
            "INSERT INTO anomaly_flags (employee_id, checkin_id, score, reason) VALUES (%s,%s,%s,%s)",
            (session["user_id"], checkin_id, anomaly["score"], anomaly["reason"]),
            fetch=False, commit=True,
        )
        flash(f"Check-in recorded but flagged: {anomaly['reason']}", "warn")
    elif result["matched"]:
        flash(f"Check-in matched the plan (score {result['match_score']}).", "ok")
    else:
        flash(f"Check-in did NOT match the plan (score {result['match_score']}).", "warn")

    return redirect(url_for("dashboard"))


@app.route("/history")
@login_required
def history():
    rows, _ = query(
        """
        SELECT c.*, p.planned_place_name, p.plan_date
        FROM checkins c
        LEFT JOIN planned_visits p ON p.id = c.plan_id
        WHERE c.employee_id=%s
        ORDER BY c.checkin_time DESC
        LIMIT 200
        """,
        (session["user_id"],),
    )
    return render_template("history.html", rows=rows or [])


@app.route("/admin", methods=["GET", "POST"])
@login_required
@admin_required
def admin():
    if request.method == "POST" and request.form.get("action") == "create_employee":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if name and email and password:
            try:
                query(
                    "INSERT INTO employees (name, email, password_hash, role) VALUES (%s,%s,%s,'employee')",
                    (name, email, generate_password_hash(password)),
                    fetch=False, commit=True,
                )
                flash("Employee created.", "ok")
            except Exception as e:
                flash(f"Failed: {e}", "error")
        return redirect(url_for("admin"))

    today = date.today()
    summary, _ = query(
        """
        SELECT e.id, e.name, e.email,
               p.planned_place_name, p.plan_date,
               (SELECT COUNT(*) FROM checkins c WHERE c.employee_id=e.id AND DATE(c.checkin_time)=%s) AS today_checkins,
               (SELECT MAX(c.match_score) FROM checkins c WHERE c.employee_id=e.id AND DATE(c.checkin_time)=%s) AS best_score_today
        FROM employees e
        LEFT JOIN planned_visits p ON p.employee_id=e.id AND p.plan_date=%s
        WHERE e.role='employee'
        ORDER BY e.name
        """,
        (today, today, today),
    )
    flags, _ = query(
        """
        SELECT f.*, e.name AS employee_name, c.actual_place_name, c.checkin_time
        FROM anomaly_flags f
        JOIN employees e ON e.id = f.employee_id
        JOIN checkins   c ON c.id = f.checkin_id
        ORDER BY f.created_at DESC
        LIMIT 30
        """
    )
    return render_template("admin.html", summary=summary or [], flags=flags or [], today=today)


## --------------------------------------------------------------------
## v2 HTML routes: accounts, visit logging, reports, proctor dashboards.
## All routes preserve the existing employee/admin/proctor session model.
## --------------------------------------------------------------------

@app.route("/accounts")
@login_required
def accounts_list():
    from api_accounts import fetch_accounts
    from api_geo import fetch_regions, fetch_all_districts
    rows = fetch_accounts(
        type_=request.args.get("type"),
        q=request.args.get("q"),
        district_id=request.args.get("district_id"),
        region_id=request.args.get("region_id"),
        limit=300,
    )
    return render_template(
        "accounts.html",
        rows=rows,
        regions=fetch_regions(),
        districts=fetch_all_districts(),
        active_type=request.args.get("type", ""),
        active_q=request.args.get("q", ""),
        active_district=request.args.get("district_id", ""),
        active_region=request.args.get("region_id", ""),
    )


@app.route("/accounts/add", methods=["GET", "POST"])
@login_required
def accounts_add():
    from api_accounts import create_account
    from api_geo import fetch_all_districts
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "type": request.form.get("type"),
            "specialty": request.form.get("specialty"),
            "district_id": request.form.get("district_id") or None,
            "address": request.form.get("address"),
            "phone": request.form.get("phone"),
            "email": request.form.get("email"),
            "lat": request.form.get("lat") or None,
            "lon": request.form.get("lon") or None,
        }
        try:
            create_account(data, created_by=session["user_id"])
            flash("Account created.", "ok")
            return redirect(url_for("accounts_list"))
        except ValueError as e:
            flash(str(e), "error")
    return render_template(
        "account_form.html",
        existing=None,
        districts=fetch_all_districts(),
    )


@app.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def accounts_edit(account_id):
    from api_accounts import fetch_account, update_account
    from api_geo import fetch_all_districts
    existing = fetch_account(account_id)
    if not existing:
        abort(404)
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "type": request.form.get("type"),
            "specialty": request.form.get("specialty"),
            "district_id": request.form.get("district_id") or None,
            "address": request.form.get("address"),
            "phone": request.form.get("phone"),
            "email": request.form.get("email"),
            "lat": request.form.get("lat") or None,
            "lon": request.form.get("lon") or None,
        }
        try:
            update_account(account_id, data)
            flash("Account updated.", "ok")
            return redirect(url_for("accounts_list"))
        except ValueError as e:
            flash(str(e), "error")
    return render_template(
        "account_form.html",
        existing=existing,
        districts=fetch_all_districts(),
    )


@app.route("/visit", methods=["GET", "POST"])
@login_required
def visit():
    from api_visits import fetch_today_planned_items, log_visit, fetch_today_visits
    from api_accounts import fetch_accounts
    if request.method == "POST":
        selfie_path = _save_selfie(session["user_id"]) if "selfie" in request.files else None
        data = {
            "account_id": request.form.get("account_id"),
            "source": request.form.get("source", "manual"),
            "lat": request.form.get("lat") or None,
            "lon": request.form.get("lon") or None,
            "actual_place_name": request.form.get("actual_place_name"),
            "outcome": request.form.get("outcome") or None,
            "visit_notes": request.form.get("visit_notes") or None,
            "selfie_path": selfie_path,
        }
        try:
            result = log_visit(session["user_id"], data)
            ms = result["match_score"]
            if ms is None:
                flash("Visit logged.", "ok")
            elif result["matched"]:
                flash(f"Visit logged. Matched the account (score {ms}).", "ok")
            else:
                flash(f"Visit logged but did NOT match the account (score {ms}).", "warn")
            return redirect(url_for("visit"))
        except (ValueError, LookupError) as e:
            flash(str(e), "error")

    planned_items = fetch_today_planned_items(session["user_id"])
    today_visits = fetch_today_visits(session["user_id"])
    all_accounts = fetch_accounts(limit=500)
    return render_template(
        "visit.html",
        planned_items=planned_items,
        today_visits=today_visits,
        all_accounts=all_accounts,
    )


@app.route("/reports")
@login_required
def reports():
    from api_stats import compute_stats
    period = request.args.get("period", "day")
    if period not in ("day", "week", "month", "quarter"):
        period = "day"
    stats = compute_stats(session["user_id"], period)

    # Visits breakdown for the chart — re-query so we have outcome too.
    from api_stats import period_window
    start_dt, end_dt, _, _ = period_window(period)
    outcome_rows, _ = query(
        """
        SELECT c.outcome, COUNT(*) AS cnt
        FROM checkins c
        WHERE c.employee_id=%s AND c.account_id IS NOT NULL
          AND c.checkin_time BETWEEN %s AND %s
        GROUP BY c.outcome
        """,
        (session["user_id"], start_dt, end_dt),
    )
    outcomes = {"met": 0, "not_met": 0, "rescheduled": 0, "unset": 0}
    for r in outcome_rows or []:
        key = r["outcome"] if r["outcome"] in ("met", "not_met", "rescheduled") else "unset"
        outcomes[key] = int(r["cnt"])

    return render_template(
        "reports.html",
        active_period=period,
        stats=stats,
        outcomes=outcomes,
    )


@app.route("/reports/csv")
@login_required
def reports_csv_html():
    """HTML-facing CSV download — reuses the API helper."""
    from api_reports import build_visits_csv, build_accounts_csv
    rtype = request.args.get("type", "visits")
    role = session.get("role", "employee")
    if rtype == "accounts":
        body = build_accounts_csv(role=role, employee_id=session["user_id"])
        fname = "accounts.csv"
    else:
        body = build_visits_csv(session["user_id"], role=role)
        fname = "visits.csv"
    return Response(
        body, mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.route("/proctor")
@login_required
@proctor_required
def proctor_index():
    from api_proctor import fetch_india_rollups
    data = fetch_india_rollups()
    # Pass both the legacy 'rows' list and the new wrapped payload so existing
    # Jinja templates that use rows= keep working.
    return render_template("proctor.html", rows=data["regions"], totals=data["totals"])


@app.route("/proctor/region/<int:rid>")
@login_required
@proctor_required
def proctor_region(rid):
    from api_proctor import fetch_region_rollups
    from api_geo import fetch_region
    region = fetch_region(rid)
    if not region:
        abort(404)
    data = fetch_region_rollups(rid)
    return render_template(
        "proctor_region.html",
        region=region,
        rows=data["districts"],
        totals=data["totals"],
    )


@app.route("/proctor/district/<int:did>")
@login_required
@proctor_required
def proctor_district(did):
    from api_proctor import fetch_district_rollups
    from api_geo import fetch_district
    district = fetch_district(did)
    if not district:
        abort(404)
    data = fetch_district_rollups(did)
    return render_template(
        "proctor_district.html",
        district=district,
        rows=data["employees"],
        totals=data["totals"],
    )


@app.route("/proctor/employee/<int:eid>")
@login_required
@proctor_required
def proctor_employee(eid):
    from api_proctor import fetch_employee_detail
    detail = fetch_employee_detail(eid)
    if not detail:
        abort(404)
    return render_template(
        "proctor_employee.html",
        employee=detail["employee"],
        stats=detail["stats"],
    )


if __name__ == "__main__":
    # Bind to localhost only — the Drupal frontend runs on the same machine via XAMPP.
    app.run(debug=True, host="127.0.0.1", port=5000)
