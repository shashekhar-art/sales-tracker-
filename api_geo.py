"""Geo (regions / districts) API blueprint."""
from flask import Blueprint, jsonify

from db import query
from api import require_drupal


bp = Blueprint("geo", __name__, url_prefix="/api")


def fetch_regions():
    rows, _ = query(
        "SELECT id, name, code, type FROM regions ORDER BY name"
    )
    return rows or []


def fetch_districts(region_id):
    rows, _ = query(
        "SELECT id, region_id, name, code FROM districts WHERE region_id=%s ORDER BY name",
        (int(region_id),),
    )
    return rows or []


def fetch_all_districts():
    rows, _ = query(
        "SELECT d.id, d.region_id, d.name, d.code, r.name AS region_name "
        "FROM districts d JOIN regions r ON r.id = d.region_id ORDER BY r.name, d.name"
    )
    return rows or []


def fetch_district(district_id):
    rows, _ = query(
        "SELECT d.id, d.region_id, d.name, d.code, r.name AS region_name "
        "FROM districts d JOIN regions r ON r.id = d.region_id WHERE d.id=%s",
        (int(district_id),),
    )
    return rows[0] if rows else None


def fetch_region(region_id):
    rows, _ = query(
        "SELECT id, name, code, type FROM regions WHERE id=%s",
        (int(region_id),),
    )
    return rows[0] if rows else None


@bp.get("/regions")
@require_drupal
def list_regions():
    return jsonify({"ok": True, "rows": fetch_regions()})


@bp.get("/regions/<int:rid>/districts")
@require_drupal
def list_region_districts(rid):
    return jsonify({"ok": True, "rows": fetch_districts(rid)})


@bp.get("/districts/<int:did>")
@require_drupal
def get_district(did):
    row = fetch_district(did)
    if not row:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "district": row})
