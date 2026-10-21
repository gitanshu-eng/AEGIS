import json
import glob
from pathlib import Path
from datetime import datetime

EPISODE_DIR = Path("outputs/phase4_investigations")
INCIDENT_DIR = Path("outputs/incident_records")
PHASE1_DIR = Path("data/processed")
MEMORY_DIR = Path("outputs/phase5_memory")
MEMORY_BANK_PATH = MEMORY_DIR / "aegis_memory_bank.json"

def parse_time(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

def convert_and_validate():
    print("=================================================================")
    print("      PHASE 5 — STEPS 4 & 5: MEMORY INGESTION & VALIDATION")
    print("=================================================================\n")

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    episode_files = sorted(glob.glob(str(EPISODE_DIR / "*_episodes.json")))
    
    memory_bank = []
    validation_errors = []

    for ep_file in episode_files:
        dataset_name = Path(ep_file).name.replace("_episodes.json", "")
        p3_file_path = INCIDENT_DIR / f"{dataset_name}_incidents.json"
        p1_file_path = PHASE1_DIR / f"{dataset_name}_temporal_continuous.csv"

        with open(ep_file, "r") as f:
            episodes = json.load(f)

        for ep in episodes:
            mem_id = ep["episode_id"]

            # Safe extraction of raw evidence
            raw = ep.get("raw_evidence_at_peak", {})
            attack_rate = raw.get("attack_rate", 0.0) if "error" not in raw else 0.0
            attack_flows = raw.get("attack_flows", 0) if "error" not in raw else 0
            total_flows = raw.get("total_flows", 0) if "error" not in raw else 0
            benign_flows = raw.get("benign_flows", 0) if "error" not in raw else 0

            # Kinematic vector for dense numerical comparisons
            # [normalized_risk (0-1), duration, attack_rate (0-1), lead_time]
            dur = float(ep["temporal_bounds"]["duration_minutes"])
            risk_score = float(ep["risk_profile"]["peak_risk_score"])
            lead_time = float(ep["forecast_behavior"].get("lead_time_minutes", 0))

            memory_obj = {
                "memory_id": mem_id,
                "source_traceability": {
                    "source_dataset": dataset_name,
                    "phase4_file": str(ep_file),
                    "phase3_file": str(p3_file_path),
                    "phase1_file": str(p1_file_path),
                    "temporal_bounds": ep["temporal_bounds"],
                    "constituent_incident_ids": ep["constituent_incident_ids"]
                },
                "structured_metadata": {
                    "peak_risk_level": ep["risk_profile"]["peak_risk_level"],
                    "peak_risk_score": risk_score,
                    "dominant_signal": ep["dominant_signal_at_peak"],
                    "lead_lag_classification": ep["forecast_behavior"]["classification"],
                    "lead_time_minutes": int(lead_time),
                    "sustained_tactics": ep["candidate_mitre_summary"].get("sustained_tactics", []),
                    "sustained_techniques": ep["candidate_mitre_summary"].get("sustained_techniques", []),
                    "investigation_state": "NEW",
                    "raw_evidence": {
                        "attack_rate": attack_rate,
                        "attack_flows": attack_flows,
                        "total_flows": total_flows,
                        "benign_flows": benign_flows,
                        "has_gap_error": "error" in raw
                    }
                },
                "semantic_context": {
                    "semantic_document": ep["investigation_summary"],
                    "kinematic_vector": [
                        round(risk_score / 100.0, 4),
                        round(dur, 2),
                        round(attack_rate, 4),
                        round(lead_time, 2)
                    ]
                }
            }

            # Validation checks on constructed memory object
            if not memory_obj["memory_id"].startswith("EP-"):
                validation_errors.append(f"{mem_id}: Invalid memory_id formatting")

            if memory_obj["structured_metadata"]["investigation_state"] != "NEW":
                validation_errors.append(f"{mem_id}: Non-NEW state detected")

            if not memory_obj["semantic_context"]["semantic_document"]:
                validation_errors.append(f"{mem_id}: Empty semantic document")

            if len(memory_obj["source_traceability"]["constituent_incident_ids"]) == 0:
                validation_errors.append(f"{mem_id}: Zero constituent incidents")

            memory_bank.append(memory_obj)

    # Save to disk
    with open(MEMORY_BANK_PATH, "w") as f:
        json.dump(memory_bank, f, indent=2)

    print(f"Total Memory Objects Ingested: {len(memory_bank)}")
    print(f"Validation Errors Encountered: {len(validation_errors)}")

    if validation_errors:
        print("[FAIL] Memory bank failed validation:")
        for err in validation_errors:
            print(f"  - {err}")
        return False

    print(f"[PASS] All {len(memory_bank)} memory objects constructed and validated.")
    print(f"[PASS] Persisted to: {MEMORY_BANK_PATH}")
    return True

if __name__ == "__main__":
    success = convert_and_validate()
    exit(0 if success else 1)
