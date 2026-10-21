import json
import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
SIMULATIONS_DIR = Path("outputs/phase6_simulations")
EXECUTIONS_DIR  = Path("outputs/phase6b_executions")

# ── Frozen Risk Formula ────────────────────────────────────────────────────
RISK_WEIGHTS = {"F": 0.35, "A": 0.35, "D": 0.15, "P": 0.15}

def compute_risk_score(F: float, A: float, D: float, P: float) -> float:
    F = max(0.0, min(1.0, F))
    A = max(0.0, min(1.0, A))
    D = max(0.0, min(1.0, D))
    P = max(0.0, min(1.0, P))
    return round((RISK_WEIGHTS["F"]*F + RISK_WEIGHTS["A"]*A +
                  RISK_WEIGHTS["D"]*D + RISK_WEIGHTS["P"]*P) * 100, 4)

# ── Execution Engine ───────────────────────────────────────────────────────
def execute_intervention(simulation_id: str, intervention_code: str, soc_authorization: bool):
    """
    Phase 6b: Defensive Execution & Verification.
    Requires explicit SOC authorization. Operates in SIMULATED mode offline.
    """
    # 1. The Authorization Gate[cite: 1]
    if not soc_authorization:
        raise PermissionError(f"EXECUTION REJECTED: Missing explicit SOC authorization for {simulation_id}")

    # Load Phase 6 Simulation
    sim_file = SIMULATIONS_DIR / f"{simulation_id}.json"
    if not sim_file.exists():
        raise FileNotFoundError(f"Simulation {simulation_id} not found.")
        
    with open(sim_file, "r") as f:
        sim_data = json.load(f)

    # Find target intervention
    target_sim = next((s for s in sim_data["simulations"] if s["intervention_code"] == intervention_code), None)
    if not target_sim:
        raise ValueError(f"Intervention {intervention_code} not found in simulation {simulation_id}")

    expected_outcomes = target_sim["outcomes"]["expected"]
    
    # 2. Execution Adapter (Infrastructure Payload Generation)[cite: 1]
    execution_payload = {
        "api_target": f"https://mock-soar.local/api/v1/intervene/{intervention_code.lower()}",
        "action": intervention_code,
        "target_identifiers": sim_data["traceability"].get("phase3_incidents", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": True
    }

    # 3. Observation Window (Variance Injector)[cite: 1]
    # In live mode, this would wait and poll real traffic. Here, we simulate variance.
    # We apply a random variance between -15% and +15% to the expected hypothetical signals.
    exp_signals = expected_outcomes["hypothetical_signals"]
    
    obs_F = exp_signals["F"] * random.uniform(0.85, 1.15)
    obs_A = exp_signals["A"] * random.uniform(0.85, 1.15)
    obs_D = exp_signals["D"] * random.uniform(0.85, 1.15)
    obs_P = exp_signals["P"] * random.uniform(0.85, 1.15)
    
    simulated_observed_risk = compute_risk_score(obs_F, obs_A, obs_D, obs_P)

    # 4. Verification Engine[cite: 1]
    predicted_risk = expected_outcomes["hypothetical_risk_score"]
    error_margin = simulated_observed_risk - predicted_risk

    execution_id = "EXEC-" + hashlib.sha256(f"{simulation_id}{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper()

    result = {
        "execution_id": execution_id,
        "source_simulation_id": simulation_id,
        "execution_mode": "SIMULATED",
        "authorization": {
            "soc_authorized": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "infrastructure_payload": execution_payload,
        "verification_metrics": {
            "predicted_risk_score": predicted_risk,
            "simulated_observed_risk_score": simulated_observed_risk,
            "prediction_error": round(error_margin, 4),
            "accuracy_note": "Positive error means the intervention was less effective than predicted. Negative means more effective."
        },
        "memory_calibration_status": "PENDING_LIVE_DATA — SIMULATED_OBSERVED outcomes must not poison Phase 5 verified memory."
    }

    EXECUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXECUTIONS_DIR / f"{execution_id}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    return result

def run_phase6b_demo():
    print("=================================================================")
    print("   PHASE 6b: DEFENSIVE EXECUTION & VERIFICATION")
    print("=================================================================\n")
    
    # We need a simulation ID from Phase 6. Grabbing the most recent one.
    sim_files = list(SIMULATIONS_DIR.glob("SIM-*.json"))
    if not sim_files:
        print("[!] No Phase 6 simulations found. Run Phase 6 first.")
        return
        
    latest_sim = sorted(sim_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    sim_id = latest_sim.stem
    
    print(f"Targeting Simulation: {sim_id}")
    print("Attempting execution without SOC authorization...")
    
    try:
        execute_intervention(sim_id, "HOST_ISOLATION", soc_authorization=False)
    except PermissionError as e:
        print(f"  [✓] Gatekeeper engaged: {e}")
        
    print("\nAttempting execution WITH SOC authorization...")
    result = execute_intervention(sim_id, "HOST_ISOLATION", soc_authorization=True)
    
    print(f"  [✓] Execution ID generated: {result['execution_id']}")
    print(f"  [✓] Execution Mode explicitly tagged as: {result['execution_mode']}")
    print(f"\n--- VERIFICATION METRICS ---")
    metrics = result['verification_metrics']
    print(f"  Predicted Risk:          {metrics['predicted_risk_score']:.2f}")
    print(f"  Simulated Observed Risk: {metrics['simulated_observed_risk_score']:.2f}")
    print(f"  Prediction Error Margin: {metrics['prediction_error']:+.2f} pts")
    
    print(f"\n--- MEMORY CALIBRATION ---")
    print(f"  Status: {result['memory_calibration_status']}")
    print(f"\nOutput saved to outputs/phase6b_executions/{result['execution_id']}.json")

if __name__ == "__main__":
    run_phase6b_demo()
