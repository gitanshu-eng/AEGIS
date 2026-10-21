# Patch: fix /api/simulations to filter by dataset using traceability.source_dataset
# Mapping from API slug -> old dataset name used in SIM traceability field

SLUG_TO_OLD = {
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

content = open("D:/AEGIS-local/api.py", "r", encoding="utf-8").read()

old_func = """@app.get("/api/simulations")
def get_simulations(dataset: str = Query(...)):
    _require_dataset(dataset)
    files = sorted(glob.glob(os.path.join(OUTPUTS_DIR, "phase6_simulations", "SIM-*.json")))
    if not files: raise HTTPException(status_code=404, detail="No Phase 6 simulation files found")
    result = []
    for fpath in files:
        with open(fpath) as f: sim = json.load(f)
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
            })
    return result"""

new_func = """SLUG_TO_OLD_DATASET = {
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
    return result"""

if old_func in content:
    content = content.replace(old_func, new_func)
    open("D:/AEGIS-local/api.py", "w", encoding="utf-8").write(content)
    print("SUCCESS - simulations endpoint patched")
else:
    print("ERROR - old function not found in api.py")
    print("Looking for match...")
    if "@app.get(\"/api/simulations\")" in content:
        print("Decorator found but body differs")
    else:
        print("Decorator not found at all")