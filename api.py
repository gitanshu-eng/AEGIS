import os
import glob
import json
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.live_replay import replay_manager
from src.inference import predict as infer_predict, is_loaded as infer_loaded, _schema as infer_schema, MODEL_PATH as infer_model_path

app = FastAPI(
    title="AEGIS Autonomous Cyber-Defense Engine",
    description="Production API - real Phase 1-7 output files. No mocks.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DATA_DIR    = os.path.join(BASE_DIR, "data")

COMPLETE_DATASETS = [
    "cic_ids2018_mar02","cic_ids2018_mar01","cic_ids2018_feb28",
    "cic_ids2018_feb23","cic_ids2018_feb22","cic_ids2018_feb21",
    "cic_ids2018_feb20","cic_ids2018_feb16","cic_ids2018_feb15",
    "cic_ids2018_feb14","cic_ids2018","cic_ids2017",
    "cic_iot_diad_2024","cic_bccc_tabular_iot_2024","cic_apt_iiot_2024",
]

DATASET_LABELS = {
    "cic_ids2018":               "CIC-IDS2018 (All)",
    "cic_ids2018_feb14":         "CIC-IDS2018 Feb 14",
    "cic_ids2018_feb15":         "CIC-IDS2018 Feb 15",
    "cic_ids2018_feb16":         "CIC-IDS2018 Feb 16",
    "cic_ids2018_feb20":         "CIC-IDS2018 Feb 20",
    "cic_ids2018_feb21":         "CIC-IDS2018 Feb 21",
    "cic_ids2018_feb22":         "CIC-IDS2018 Feb 22",
    "cic_ids2018_feb23":         "CIC-IDS2018 Feb 23",
    "cic_ids2018_feb28":         "CIC-IDS2018 Feb 28",
    "cic_ids2018_mar01":         "CIC-IDS2018 Mar 01",
    "cic_ids2018_mar02":         "CIC-IDS2018 Mar 02",
    "cic_ids2017":               "CIC-IDS2017",
    "cic_iot_diad_2024":         "CIC-IoT-DIAD-2024",
    "cic_bccc_tabular_iot_2024": "CIC-BCCC-TabularIoT-2024",
    "cic_apt_iiot_2024":         "CIC-APT-IIoT-2024",
}

def _phase_flags(slug):
    p1  = bool(glob.glob(os.path.join(DATA_DIR,    "processed",           f"{slug}_temporal_continuous.csv")))
    p2  = bool(glob.glob(os.path.join(DATA_DIR,    "final_forecasts",      f"{slug}_final_forecast.csv")))
    p3  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "incident_records",     f"{slug}_incidents.json")))
    p4  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase4_investigations", f"{slug}_episodes.json")))
    p5  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase5_memory",        "phase5_memory_store.json")))
    p6  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase6_simulations",   "SIM-*.json")))
    p7  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase7_executions",    "EXEC-*.json")))
    p6b = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase6b_executions",   "EXEC-*.json")))
    return {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5,"p6":p6,"p7":p7,"p6b":p6b}

def _require_dataset(slug):
    if slug not in COMPLETE_DATASETS:
        raise HTTPException(status_code=404, detail=f"Dataset '{slug}' not found. Available: {COMPLETE_DATASETS}")

def _safe_float(v):
    if v is None: return None
    try:
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return None

def _df_to_records(df):
    records = []
    for _, row in df.iterrows():
        rec = {}
        for k, v in row.items():
            if not isinstance(v, (list, dict)) and pd.isna(v):
                rec[k] = None
            elif isinstance(v, np.integer):
                rec[k] = int(v)
            elif isinstance(v, np.floating):
                rec[k] = _safe_float(v)
            else:
                rec[k] = v
        records.append(rec)
    return records


from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, status as http_status

AEGIS_API_KEY = os.environ.get('AEGIS_API_KEY', 'dev-insecure-key')
_api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)

async def verify_key(key: str = Security(_api_key_header)):
    if key != AEGIS_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid or missing API key')

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/health")
def health():
    return {"status":"ONLINE","version":"3.0.0","platform":"local-windows",
            "outputs_dir_exists":os.path.exists(OUTPUTS_DIR),"data_dir_exists":os.path.exists(DATA_DIR)}

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/datasets", dependencies=[Depends(verify_key)])
def list_datasets():
    return [{"id":s,"label":DATASET_LABELS.get(s,s),"phases":_phase_flags(s),"complete":all(_phase_flags(s).values())} for s in COMPLETE_DATASETS]

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/network-state", dependencies=[Depends(verify_key)])
def get_network_state(dataset: str = Query(...), limit: int = Query(default=0, ge=0)):
    _require_dataset(dataset)
    path = os.path.join(DATA_DIR, "processed", f"{dataset}_temporal_continuous.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 1 file not found for {dataset}")
    df = pd.read_csv(path)
    if "time_window" in df.columns: df = df.rename(columns={"time_window":"timestamp"})
    if "observed" in df.columns:
        df["observed"]   = df["observed"].astype(bool)
        df["unobserved"] = ~df["observed"]
    if limit > 0: df = df.tail(limit)
    return _df_to_records(df)

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/forecasts", dependencies=[Depends(verify_key)])
def get_forecasts(dataset: str = Query(...), limit: int = Query(default=0, ge=0)):
    _require_dataset(dataset)
    path = os.path.join(DATA_DIR, "final_forecasts", f"{dataset}_final_forecast.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 2 file not found for {dataset}")
    df = pd.read_csv(path)
    if "time_window" in df.columns: df = df.rename(columns={"time_window":"timestamp"})
    if "p_escalation" in df.columns and "escalation_probability" not in df.columns:
        df = df.rename(columns={"p_escalation": "escalation_probability"})
    if "escalation_probability" not in df.columns:
        df["escalation_probability"] = float("nan")
    if "primary_evidence_feature" not in df.columns:
        top_lag = [c for c in df.columns if c.startswith("attack_rate_lag")]
        df["primary_evidence_feature"] = top_lag[0] if top_lag else None
    if limit > 0: df = df.tail(limit)
    return _df_to_records(df)

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/incidents", dependencies=[Depends(verify_key)])
def get_incidents(dataset: str = Query(...)):
    _require_dataset(dataset)
    path = os.path.join(OUTPUTS_DIR, "incident_records", f"{dataset}_incidents.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 3 file not found for {dataset}")
    with open(path) as f: raw = json.load(f)
    incidents = raw if isinstance(raw, list) else raw.get("incidents", [])
    result = []
    for inc in incidents:
        ctx = inc.get("candidate_attack_context", {})
        result.append({
            "id": inc.get("incident_id"), "incident_id": inc.get("incident_id"),
            "timestamp": inc.get("timestamp"),
            "risk_score": inc.get("risk", {}).get("score"),
            "score": inc.get("risk", {}).get("score"),
            "risk_level": inc.get("risk", {}).get("level"),
            "technique_name": (ctx.get("possible_techniques") or ["Unknown"])[0],
            "technique": (ctx.get("possible_techniques") or [""])[0],
            "mitre_id": (ctx.get("candidate_tactics") or [""])[0],
            "source": str(inc.get("observations", {}).get("attack_rate", "")),
            "target": str(inc.get("metadata", {}).get("dataset_target", "")),
            "escalation_probability": inc.get("forecast", {}).get("escalation_probability"),
            "primary_driver": inc.get("forecast", {}).get("primary_driver"),
            "evidence": inc.get("evidence", []),
        })
    return result

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/episodes", dependencies=[Depends(verify_key)])
def get_episodes(dataset: str = Query(...)):
    _require_dataset(dataset)
    path = os.path.join(OUTPUTS_DIR, "phase4_investigations", f"{dataset}_episodes.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 4 file not found for {dataset}")
    with open(path) as f: raw = json.load(f)
    episodes = raw if isinstance(raw, list) else raw.get("episodes", [])
    result = []
    for ep in episodes:
        tb = ep.get("temporal_bounds", {})
        fc = ep.get("forecast_behavior", {})
        rp = ep.get("risk_profile", {})
        ms = ep.get("candidate_mitre_summary", {})
        result.append({
            "id": ep.get("episode_id"), "episode_id": ep.get("episode_id"),
            "title": ep.get("episode_id"), "dataset": ep.get("dataset"),
            "investigation_state": ep.get("investigation_state"),
            "start_time": tb.get("start_time"), "end_time": tb.get("end_time"),
            "duration_minutes": tb.get("duration_minutes"),
            "peak_risk_score": rp.get("peak_risk_score"),
            "peak_risk_level": rp.get("peak_risk_level"),
            "lead_lag_classification": fc.get("classification"),
            "lead_time_minutes": fc.get("lead_time_minutes"),
            "lag_window": fc.get("lead_time_minutes", 0),
            "dominant_signal": ep.get("dominant_signal_at_peak"),
            "narrative": ep.get("dominant_signal_at_peak"),
            "lead_indicator": fc.get("classification"),
            "sustained_tactics": ms.get("sustained_tactics", []),
            "sustained_techniques": ms.get("sustained_techniques", []),
            "evidence": ep,
        })
    return result

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/memory")
def get_memory(dataset: str = Query(...)):
    _require_dataset(dataset)
    path = os.path.join(OUTPUTS_DIR, "phase5_memory", "phase5_memory_store.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Phase 5 memory store not found")
    with open(path) as f: raw = json.load(f)
    records = raw if isinstance(raw, list) else raw.get("records", [])
    result = []
    for rec in records:
        if rec.get("dataset") and rec["dataset"] != dataset: continue
        kv = rec.get("semantic_context", {}).get("kinematic_vector", [])
        sm = rec.get("structured_metadata", {})
        norm = float(np.linalg.norm(kv)) / 300.0 if kv else None
        result.append({
            "id": rec.get("memory_id"), "signature": rec.get("memory_id"),
            "dataset_origin": rec.get("dataset"),
            "context": sm.get("lead_lag_classification"),
            "peak_risk_level": sm.get("peak_risk_level"),
            "sustained_tactics": sm.get("sustained_tactics", []),
            "similarity": _safe_float(norm), "kinematic_vector": kv,
        })
    return result

SLUG_TO_OLD_DATASET = {
    "cic_ids2018_mar02": "Friday-02-03-2018",
    "cic_ids2018_mar01": "Thursday-01-03-2018",
    "cic_ids2018_feb28": "Wednesday-28-02-2018",
    "cic_ids2018_feb23": "Friday-23-02-2018",
    "cic_ids2018_feb22": "Thursday-22-02-2018",
    "cic_ids2018_feb21": "Thuesday-20-02-2018",
    "cic_ids2018_feb20": "Thuesday-20-02-2018",
    "cic_ids2018_feb16": "Friday-16-02-2018",
    "cic_ids2018_feb15": "Thursday-15-02-2018",
    "cic_ids2018_feb14": "Wednesday-14-02-2018",
    "cic_ids2018":       "Friday-02-03-2018",
    "cic_ids2017":       "cic_ids2017",
    "cic_iot_diad_2024": "cic_iot_diad_2024",
    "cic_bccc_tabular_iot_2024": "cic_bccc_tabular_iot_2024",
    "cic_apt_iiot_2024": "cic_apt_iiot_2024",
}

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/simulations")
def get_simulations(dataset: str = Query(...)):
    _require_dataset(dataset)
    old_name = SLUG_TO_OLD_DATASET.get(dataset, dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase6_simulations", "SIM-*.json")))
    if not files: raise HTTPException(status_code=404, detail="No Phase 6 simulation files found")
    result = []
    for fpath in files:
        with open(fpath) as f: sim = json.load(f)
        td = sim.get("traceability", {})
        source_ds = td.get("source_dataset")
        # Only include SIM files that match this dataset
        # SIM files with None source_dataset are orphaned - skip them
        if source_ds is None: continue
        if source_ds != old_name: continue
        baseline = sim.get("baseline_risk_score")
        for scenario in sim.get("simulations", []):
            outcomes = scenario.get("outcomes", {})
            chosen = outcomes.get("median") or outcomes.get("min") or {}
            hyp = chosen.get("hypothetical_risk_score")
            delta = (_safe_float(hyp) - _safe_float(baseline)) if (hyp is not None and baseline is not None) else None
            result.append({
                "simulation_id": sim.get("simulation_id"),
                "name": scenario.get("intervention_name"),
                "hypothesis": scenario.get("intervention_name"),
                "description": scenario.get("description"),
                "assumption": scenario.get("assumption"),
                "baseline_risk": _safe_float(baseline),
                "simulated_risk": _safe_float(hyp),
                "delta": _safe_float(delta),
                "risk_reduction_pct": _safe_float(chosen.get("risk_reduction_pct")),
                "intervention_code": scenario.get("intervention_code"),
                "source_dataset": source_ds,
                "source_episode_id": td.get("source_episode_id"),
            })
    return result

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/executions")
def get_executions(dataset: str = Query(...)):
    _require_dataset(dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase7_executions", "EXEC-*.json")))
    if not files: raise HTTPException(status_code=404, detail="No Phase 7 execution files found")
    result = []
    for fpath in files:
        with open(fpath) as f: ex = json.load(f)
        auth = ex.get("authorization", {})
        payload = ex.get("infrastructure_payload", {})
        result.append({
            "id": ex.get("execution_id"), "execution_id": ex.get("execution_id"),
            "source_sim": ex.get("source_simulation_id"),
            "execution_mode": ex.get("execution_mode"),
            "soc_authorized": auth.get("soc_authorized"),
            "timestamp": auth.get("timestamp"), "dispatched_at": auth.get("timestamp"),
            "action": payload.get("action"), "command": payload.get("action"),
            "api_target": payload.get("api_target"),
            "target_identifiers": payload.get("target_identifiers", []),
            "dry_run": payload.get("dry_run"),
            "stdout": f"Mode: {ex.get('execution_mode')} | Action: {payload.get('action')}",
            "result": ex.get("execution_mode"),
        })
    return result

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/verifications")
def get_verifications(dataset: str = Query(...)):
    _require_dataset(dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase6b_executions", "EXEC-*.json")))
    if not files: raise HTTPException(status_code=404, detail="No Phase 6B verification files found")
    result = []
    for fpath in files:
        with open(fpath) as f: ex = json.load(f)
        auth = ex.get("authorization", {})
        payload = ex.get("infrastructure_payload", {})
        metrics = ex.get("verification_metrics", {})
        mem_cal = ex.get("memory_calibration_status", "")
        if metrics.get("simulated_observed_risk_score") is not None:
            err = abs(metrics.get("prediction_error", 999))
            state = "VERIFIED" if err < 5.0 else "CONFIRMED"
        elif "PENDING_LIVE_DATA" in mem_cal and auth.get("soc_authorized"):
            state = "DISPATCHING"
        elif auth.get("soc_authorized"):
            state = "QUEUED"
        else:
            state = "QUEUED"
        targets = payload.get("target_identifiers") or []
        result.append({
            "id": ex.get("execution_id"), "action_id": ex.get("execution_id"),
            "execution_id": ex.get("execution_id"),
            "source_sim": ex.get("source_simulation_id"),
            "execution_mode": ex.get("execution_mode"),
            "soc_authorized": auth.get("soc_authorized"),
            "timestamp": auth.get("timestamp"),
            "action": payload.get("action"),
            "target_host": targets[0] if targets else payload.get("api_target", "unknown"),
            "dry_run": payload.get("dry_run"),
            "predicted_risk": _safe_float(metrics.get("predicted_risk_score")),
            "observed_risk": _safe_float(metrics.get("simulated_observed_risk_score")),
            "prediction_error": _safe_float(metrics.get("prediction_error")),
            "accuracy_note": metrics.get("accuracy_note"),
            "memory_calibration_status": mem_cal,
            "state": state,
        })
    return result

# --- Live Replay Endpoints -------------------------------------------

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/live/tick")
def live_tick(dataset: str = Query(...)):
    _require_dataset(dataset)
    return replay_manager.tick(dataset)

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/live/status")
def live_status(dataset: str = Query(...)):
    _require_dataset(dataset)
    return replay_manager.status(dataset)

@app.post("/api/live/reset")
def live_reset(dataset: str = Query(...)):
    _require_dataset(dataset)
    replay_manager.reset(dataset)
    return {"status": "reset", "dataset": dataset}



# --- Static SPA serving ----------------------------------------------
DIST_PATH   = os.path.join(BASE_DIR, "frontend", "dist")
ASSETS_PATH = os.path.join(DIST_PATH, "assets")

if os.path.isdir(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")

@app.get("/")
def serve_root():
    index = os.path.join(DIST_PATH, "index.html")
    return FileResponse(index) if os.path.exists(index) else {"status": "AEGIS API online - no frontend dist yet"}

@app.post("/api/infer")
def infer_escalation(features: Dict[str, Any]):
    if not infer_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    result = infer_predict(features)
    if result["inference_mode"] != "RUNTIME_RF":
        raise HTTPException(status_code=422, detail=str(result))
    return result

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/infer/status")
def infer_status():
    return {
        "model_loaded": infer_loaded(),
        "model_path":   infer_model_path,
        "schema":       infer_schema,
    }


from src.pcap_replay import pcap_replay_manager

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/pcap/tick", dependencies=[Depends(verify_key)])
def pcap_tick(name: str = Query(...)):
    return pcap_replay_manager.tick(name)

@app.get("/api/health-public", include_in_schema=False)
@app.get("/api/pcap/status")
def pcap_status(name: str = Query(...)):
    return pcap_replay_manager.status(name)

@app.post("/api/pcap/reset")
def pcap_reset(name: str = Query(...)):
    pcap_replay_manager.reset(name)
    return {"ok": True}

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    file_path = os.path.join(DIST_PATH, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    index = os.path.join(DIST_PATH, "index.html")
    return FileResponse(index) if os.path.exists(index) else {"status": "AEGIS API online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)


