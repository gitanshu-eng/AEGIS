import os
import json
import joblib
import pandas as pd

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH   = os.path.join(BASE_DIR, "models", "aegis_escalation_rf.joblib")
SCHEMA_PATH  = os.path.join(BASE_DIR, "models", "feature_schema.json")

_model  = None
_schema = None

def load():
    global _model, _schema
    if _model is None and os.path.exists(MODEL_PATH):
        _model  = joblib.load(MODEL_PATH)
        with open(SCHEMA_PATH) as f:
            _schema = json.load(f)

load()

def predict(row: dict) -> dict:
    if _model is None:
        return {"p_escalation": None, "risk_score": None, "inference_mode": "UNAVAILABLE"}
    features = _schema["features"]
    missing  = [f for f in features if f not in row]
    if missing:
        return {"p_escalation": None, "risk_score": None, "inference_mode": "MISSING_FEATURES", "missing": missing}
    X = pd.DataFrame([{f: row[f] for f in features}])
    p = float(_model.predict(X)[0])
    p = max(0.0, min(1.0, p))
    return {
        "p_escalation":   round(p, 4),
        "risk_score":     round(p * 100, 2),
        "inference_mode": "RUNTIME_RF",
    }

def is_loaded() -> bool:
    return _model is not None
