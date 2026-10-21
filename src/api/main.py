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

app = FastAPI(
    title="AEGIS Autonomous Cyber-Defense Engine",
    description="Production API — real Phase 1-7 output files. No mocks.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "/home/ubuntu/AEGIS"
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DATA_DIR    = os.path.join(BASE_DIR, "data")

COMPLETE_DATASETS = [
    "cic_ids2018_mar02",
    "cic_ids2018_mar01",
    "cic_ids2018_feb28",
    "cic_ids2018_feb23",
    "cic_ids2018_feb22",
    "cic_ids2018_feb21",
    "cic_ids2018_feb20",
    "cic_ids2018_feb16",
    "cic_ids2018_feb15",
    "cic_ids2018_feb14",
    "cic_ids2018",
    "cic_ids2017",
    "cic_iot_diad_2024",
    "cic_bccc_tabular_iot_2024",
    "cic_apt_iiot_2024",
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

def _phase_flags(slug: str) -> Dict[str, bool]:
    p1  = bool(glob.glob(os.path.join(DATA_DIR,    "processed",            f"{slug}_temporal_continuous.csv")))
    p2  = bool(glob.glob(os.path.join(DATA_DIR,    "final_forecasts",       f"{slug}_final_forecast.csv")))
    p3  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "incident_records",      f"{slug}_incidents.json")))
    p4  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase4_investigations",  f"{slug}_episodes.json")))
    p5  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase5_memory",         "phase5_memory_store.json")))
    p6  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase6_simulations",    "SIM-*.json")))
    p7  = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase7_executions",     "EXEC-*.json")))
    p6b = bool(glob.glob(os.path.join(OUTPUTS_DIR, "phase6b_executions",    "EXEC-*.json")))
    return {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5,"p6":p6,"p7":p7,"p6b":p6b}

def _require_dataset(slug: str):
    if slug not in COMPLETE_DATASETS:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{slug}' not found or not fully complete. Available: {COMPLETE_DATASETS}"
        )

def _safe_float(v):
    if v is None: return None
    try:
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return None

def _df_to_records(df: pd.DataFrame) -> List[Dict]:
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

@app.get("/api/health")
def health():
    return {
        "status": "ONLINE",
        "version": "3.0.0",
        "platform": "AWS-EC2-Ubuntu",
        "outputs_dir_exists": os.path.exists(OUTPUTS_DIR),
        "data_dir_exists": os.path.exists(DATA_DIR),
    }

@app.get("/api/datasets")
def list_datasets():
    result = []
    for slug in COMPLETE_DATASETS:
        flags = _phase_flags(slug)
        result.append({
            "id":       slug,
            "label":    DATASET_LABELS.get(slug, slug),
            "phases":   flags,
            "complete": all(flags.values()),
        })
    return result

@app.get("/api/network-state")
def get_network_state(dataset: str = Query(...), limit: int = Query(default=0, ge=0)):
    _require_dataset(dataset)
    path = os.path.join(DATA_DIR, "processed", f"{dataset}_temporal_continuous.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 1 file not found for {dataset}")
    df = pd.read_csv(path)
    if "time_window" in df.columns:
        df = df.rename(columns={"time_window": "timestamp"})
    if "observed" in df.columns:
        df["observed"]   = df["observed"].astype(bool)
        df["unobserved"] = ~df["observed"]
    if limit > 0:
        df = df.tail(limit)
    return _df_to_records(df)

@app.get("/api/forecasts")
def get_forecasts(dataset: str = Query(...), limit: int = Query(default=0, ge=0)):
    _require_dataset(dataset)
    path = os.path.join(DATA_DIR, "final_forecasts", f"{dataset}_final_forecast.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 2 file not found for {dataset}")
    df = pd.read_csv(path)
    if "time_window" in df.columns:
        df = df.rename(columns={"time_window": "timestamp"})
    if limit > 0:
        df = df.tail(limit)
    return _df_to_records(df)

@app.get("/api/incidents")
def get_incidents(dataset: str = Query(...)):
    _require_dataset(dataset)
    path = os.path.join(OUTPUTS_DIR, "incident_records", f"{dataset}_incidents.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 3 file not found for {dataset}")
    with open(path) as f:
        raw = json.load(f)
    incidents = raw if isinstance(raw, list) else raw.get("incidents", [])
    result = []
    for inc in incidents:
        ctx = inc.get("candidate_attack_context", {})
        result.append({
            "id":                    inc.get("incident_id"),
            "incident_id":           inc.get("incident_id"),
            "timestamp":             inc.get("timestamp"),
            "risk_score":            inc.get("risk", {}).get("score"),
            "score":                 inc.get("risk", {}).get("score"),
            "risk_level":            inc.get("risk", {}).get("level"),
            "technique_name":        (ctx.get("possible_techniques") or ["Unknown"])[0],
            "technique":             (ctx.get("possible_techniques") or [""])[0],
            "mitre_id":              (ctx.get("candidate_tactics")   or [""])[0],
            "source":                str(inc.get("observations", {}).get("attack_rate", "")),
            "target":                str(inc.get("metadata", {}).get("dataset_target", "")),
            "escalation_probability":inc.get("forecast", {}).get("escalation_probability"),
            "primary_driver":        inc.get("forecast", {}).get("primary_driver"),
            "evidence":              inc.get("evidence", []),
        })
    return result

@app.get("/api/episodes")
def get_episodes(dataset: str = Query(...)):
    _require_dataset(dataset)
    path = os.path.join(OUTPUTS_DIR, "phase4_investigations", f"{dataset}_episodes.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Phase 4 file not found for {dataset}")
    with open(path) as f:
        raw = json.load(f)
    episodes = raw if isinstance(raw, list) else raw.get("episodes", [])
    result = []
    for ep in episodes:
        tb = ep.get("temporal_bounds", {})
        fc = ep.get("forecast_behavior", {})
        rp = ep.get("risk_profile", {})
        ms = ep.get("candidate_mitre_summary", {})
        result.append({
            "id":                      ep.get("episode_id"),
            "episode_id":              ep.get("episode_id"),
            "title":                   ep.get("episode_id"),
            "dataset":                 ep.get("dataset"),
            "investigation_state":     ep.get("investigation_state"),
            "start_time":              tb.get("start_time"),
            "end_time":                tb.get("end_time"),
            "duration_minutes":        tb.get("duration_minutes"),
            "peak_risk_score":         rp.get("peak_risk_score"),
            "peak_risk_level":         rp.get("peak_risk_level"),
            "lead_lag_classification": fc.get("classification"),
            "lead_time_minutes":       fc.get("lead_time_minutes"),
            "lag_window":              fc.get("lead_time_minutes", 0),
            "dominant_signal":         ep.get("dominant_signal_at_peak"),
            "narrative":               ep.get("dominant_signal_at_peak"),
            "lead_indicator":          fc.get("classification"),
            "sustained_tactics":       ms.get("sustained_tactics", []),
            "sustained_techniques":    ms.get("sustained_techniques", []),
            "evidence":                ep,
        })
    return result

@app.get("/api/memory")
def get_memory(dataset: str = Query(...)):
    _require_dataset(dataset)
    path = os.path.join(OUTPUTS_DIR, "phase5_memory", "phase5_memory_store.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Phase 5 memory store not found")
    with open(path) as f:
        raw = json.load(f)
    records = raw if isinstance(raw, list) else raw.get("records", [])
    result = []
    for rec in records:
        if rec.get("dataset") and rec["dataset"] != dataset:
            continue
        kv = rec.get("semantic_context", {}).get("kinematic_vector", [])
        sm = rec.get("structured_metadata", {})
        norm = float(np.linalg.norm(kv)) / 300.0 if kv else None
        result.append({
            "id":               rec.get("memory_id"),
            "signature":        rec.get("memory_id"),
            "dataset_origin":   rec.get("dataset"),
            "context":          sm.get("lead_lag_classification"),
            "peak_risk_level":  sm.get("peak_risk_level"),
            "sustained_tactics":sm.get("sustained_tactics", []),
            "similarity":       _safe_float(norm),
            "kinematic_vector": kv,
        })
    return result

@app.get("/api/simulations")
def get_simulations(dataset: str = Query(...)):
    _require_dataset(dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase6_simulations", "SIM-*.json")))
    if not files:
        raise HTTPException(status_code=404, detail="No Phase 6 simulation files found")
    result = []
    for fpath in files:
        with open(fpath) as f:
            sim = json.load(f)
        baseline = sim.get("baseline_risk_score")
        for scenario in sim.get("simulations", []):
            outcomes = scenario.get("outcomes", {})
            chosen   = outcomes.get("median") or outcomes.get("min") or {}
            hyp      = chosen.get("hypothetical_risk_score")
            delta    = (_safe_float(hyp) - _safe_float(baseline)) if (hyp is not None and baseline is not None) else None
            result.append({
                "simulation_id":      sim.get("simulation_id"),
                "name":               scenario.get("intervention_name"),
                "hypothesis":         scenario.get("intervention_name"),
                "description":        scenario.get("description"),
                "assumption":         scenario.get("assumption"),
                "baseline_risk":      _safe_float(baseline),
                "simulated_risk":     _safe_float(hyp),
                "delta":              _safe_float(delta),
                "risk_reduction_pct": _safe_float(chosen.get("risk_reduction_pct")),
                "intervention_code":  scenario.get("intervention_code"),
            })
    return result

@app.get("/api/executions")
def get_executions(dataset: str = Query(...)):
    _require_dataset(dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase7_executions", "EXEC-*.json")))
    if not files:
        raise HTTPException(status_code=404, detail="No Phase 7 execution files found")
    result = []
    for fpath in files:
        with open(fpath) as f:
            ex = json.load(f)
        auth    = ex.get("authorization", {})
        payload = ex.get("infrastructure_payload", {})
        result.append({
            "id":               ex.get("execution_id"),
            "execution_id":     ex.get("execution_id"),
            "source_sim":       ex.get("source_simulation_id"),
            "execution_mode":   ex.get("execution_mode"),
            "soc_authorized":   auth.get("soc_authorized"),
            "timestamp":        auth.get("timestamp"),
            "dispatched_at":    auth.get("timestamp"),
            "action":           payload.get("action"),
            "command":          payload.get("action"),
            "api_target":       payload.get("api_target"),
            "target_identifiers": payload.get("target_identifiers", []),
            "dry_run":          payload.get("dry_run"),
            "stdout":           f"Mode: {ex.get('execution_mode')} | Action: {payload.get('action')}",
            "result":           ex.get("execution_mode"),
        })
    return result

@app.get("/api/verifications")
def get_verifications(dataset: str = Query(...)):
    _require_dataset(dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase6b_executions", "EXEC-*.json")))
    if not files:
        raise HTTPException(status_code=404, detail="No Phase 6B verification files found")
    result = []
    for fpath in files:
        with open(fpath) as f:
            ex = json.load(f)
        auth    = ex.get("authorization", {})
        payload = ex.get("infrastructure_payload", {})
        metrics = ex.get("verification_metrics", {})
        mem_cal = ex.get("memory_calibration_status", "")

        if metrics.get("simulated_observed_risk_score") is not None:
            err   = abs(metrics.get("prediction_error", 999))
            state = "VERIFIED" if err < 5.0 else "CONFIRMED"
        elif "PENDING_LIVE_DATA" in mem_cal and auth.get("soc_authorized"):
            state = "DISPATCHING"
        elif auth.get("soc_authorized"):
            state = "QUEUED"
        else:
            state = "QUEUED"

        targets = payload.get("target_identifiers") or []
        result.append({
            "id":               ex.get("execution_id"),
            "action_id":        ex.get("execution_id"),
            "execution_id":     ex.get("execution_id"),
            "source_sim":       ex.get("source_simulation_id"),
            "execution_mode":   ex.get("execution_mode"),
            "soc_authorized":   auth.get("soc_authorized"),
            "timestamp":        auth.get("timestamp"),
            "action":           payload.get("action"),
            "target_host":      targets[0] if targets else payload.get("api_target", "unknown"),
            "dry_run":          payload.get("dry_run"),
            "predicted_risk":   _safe_float(metrics.get("predicted_risk_score")),
            "observed_risk":    _safe_float(metrics.get("simulated_observed_risk_score")),
            "prediction_error": _safe_float(metrics.get("prediction_error")),
            "accuracy_note":    metrics.get("accuracy_note"),
            "memory_calibration_status": mem_cal,
            "state":            state,
        })
    return result

# ─── static SPA serving ───────────────────────────────────────────────────────
DIST_PATH   = "/home/ubuntu/AEGIS/frontend_dist"
ASSETS_PATH = os.path.join(DIST_PATH, "assets")

if os.path.isdir(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")

@app.get("/")
def serve_root():
    index = os.path.join(DIST_PATH, "index.html")
    return FileResponse(index) if os.path.exists(index) else {"status": "AEGIS API online — no frontend dist yet"}

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
