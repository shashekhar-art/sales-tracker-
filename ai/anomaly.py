"""Anomaly detection over an employee's check-in history."""
import numpy as np
from sklearn.ensemble import IsolationForest

from db import query

FEATURES = ["distance_km", "text_similarity", "hour_of_day", "day_of_week", "match_score"]
MIN_HISTORY = 10
WINDOW = 60
RULE_DISTANCE_KM = 20.0


def _load_history(employee_id: int):
    rows, _ = query(
        """
        SELECT distance_km, text_similarity, match_score, checkin_time
        FROM checkins
        WHERE employee_id = %s AND distance_km IS NOT NULL
        ORDER BY checkin_time DESC
        LIMIT %s
        """,
        (employee_id, WINDOW),
    )
    return rows or []


def _row_to_features(row):
    t = row["checkin_time"]
    return [
        float(row["distance_km"] or 0.0),
        float(row["text_similarity"] or 0.0),
        float(t.hour),
        float(t.weekday()),
        float(row["match_score"] or 0.0),
    ]


def score_checkin(employee_id: int, current: dict) -> dict:
    """
    current: {"distance_km", "text_similarity", "match_score", "checkin_time" (datetime)}
    Returns {"is_anomaly": bool, "score": float|None, "reason": str}.
    """
    if current.get("distance_km") is None:
        return {"is_anomaly": False, "score": None, "reason": ""}

    cur_features = _row_to_features(current)
    history = _load_history(employee_id)

    if current.get("distance_km", 0) and current["distance_km"] > RULE_DISTANCE_KM:
        return {
            "is_anomaly": True,
            "score": None,
            "reason": f"Distance from plan ({current['distance_km']:.1f} km) exceeds {RULE_DISTANCE_KM:.0f} km threshold",
        }

    if len(history) < MIN_HISTORY:
        return {"is_anomaly": False, "score": None, "reason": "insufficient history"}

    X = np.array([_row_to_features(r) for r in history])
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X)

    cur = np.array([cur_features])
    pred = model.predict(cur)[0]
    raw_score = float(model.decision_function(cur)[0])

    if pred == -1:
        means = X.mean(axis=0)
        stds = X.std(axis=0) + 1e-9
        z = np.abs((np.array(cur_features) - means) / stds)
        idx = int(np.argmax(z))
        reason = f"Outlier in {FEATURES[idx]} (z={z[idx]:.2f})"
        return {"is_anomaly": True, "score": raw_score, "reason": reason}

    return {"is_anomaly": False, "score": raw_score, "reason": ""}
