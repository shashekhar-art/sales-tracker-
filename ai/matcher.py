"""Smart location matching: combines geo-distance and fuzzy text similarity."""
from functools import lru_cache
from typing import Optional, Tuple

from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from rapidfuzz import fuzz

import config

_geocoder = Nominatim(user_agent="sales_tracker_app", timeout=5)


@lru_cache(maxsize=512)
def geocode(place: str) -> Optional[Tuple[float, float]]:
    if not place or not place.strip():
        return None
    try:
        loc = _geocoder.geocode(place)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        return None
    return None


def _coords(lat, lon, name):
    if lat is not None and lon is not None:
        return (float(lat), float(lon))
    if name:
        return geocode(name)
    return None


def match(planned: dict, actual: dict) -> dict:
    """
    planned/actual: {"name": str, "lat": float|None, "lon": float|None}
    Returns dict with distance_km, text_similarity, match_score, matched.
    """
    p_coords = _coords(planned.get("lat"), planned.get("lon"), planned.get("name"))
    a_coords = _coords(actual.get("lat"), actual.get("lon"), actual.get("name"))

    distance_km = None
    geo_score = 0.0
    if p_coords and a_coords:
        distance_km = geodesic(p_coords, a_coords).km
        geo_score = max(0.0, 1.0 - distance_km / config.GEO_THRESHOLD_KM)
        geo_score = min(geo_score, 1.0)

    text_similarity = 0.0
    pn, an = (planned.get("name") or "").strip(), (actual.get("name") or "").strip()
    if pn and an:
        text_similarity = fuzz.token_set_ratio(pn, an) / 100.0

    if p_coords and a_coords:
        combined = 0.7 * geo_score + 0.3 * text_similarity
    else:
        combined = text_similarity

    return {
        "distance_km": round(distance_km, 3) if distance_km is not None else None,
        "text_similarity": round(text_similarity, 3),
        "match_score": round(combined, 3),
        "matched": combined >= config.MATCH_THRESHOLD,
        "planned_coords": p_coords,
        "actual_coords": a_coords,
    }
