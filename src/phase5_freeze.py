import json, math, glob
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase5_retrieval import EpisodeMemory

EPISODE_DIR = Path("outputs/phase4_investigations")
PHASE5_DIR  = Path("outputs/phase5_memory")

def default_serializer(obj):
    if isinstance(obj, datetime): return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def freeze_phase5():
    print("=================================================================")
    print("      PHASE 5: FINAL ARTIFACT FREEZE")
    print("=================================================================\n")
    PHASE5_DIR.mkdir(parents=True, exist_ok=True)
    memory = EpisodeMemory()
    leading_ep_id = leading_dataset = None
    count = 0
    for file in sorted(glob.glob(str(EPISODE_DIR / "*_episodes.json"))):
        dataset = Path(file).name.replace("_episodes.json", "")
        with open(file) as f:
            episodes = json.load(f)
        for ep in episodes:
            lt = ep["forecast_behavior"].get("lead_time_minutes") or 0
            mem_obj = {
                "memory_id": ep["episode_id"],
                "dataset":   dataset,
                "structured_metadata": {
                    "peak_risk_level":         ep["risk_profile"]["peak_risk_level"],
                    "lead_lag_classification": ep["forecast_behavior"]["classification"],
                    "sustained_tactics":       ep["candidate_mitre_summary"].get("sustained_tactics", [])
                },
                "semantic_context": {
                    "kinematic_vector": [
                        ep["risk_profile"]["peak_risk_score"] / 100.0,
                        float(ep["temporal_bounds"]["duration_minutes"]),
                        float(ep["raw_evidence_at_peak"].get("attack_rate", 0.0)),
                        float(lt)
                    ]
                }
            }
            memory.from_memory_obj(mem_obj)
            count += 1
            if ep["forecast_behavior"]["classification"] == "LEADING":
                leading_ep_id   = ep["episode_id"]
                leading_dataset = dataset
    print(f"[✓] Ingested {count} episodes into EpisodeMemory")
    with open(PHASE5_DIR / "phase5_memory_store.json", "w") as f:
        json.dump(list(memory.bank.values()), f, indent=2)
    print(f"[✓] Serialized {count} episodes to phase5_memory_store.json")
    config = {
        "engine": "EpisodeMemory (patched)",
        "n_episodes": count,
        "weights": {"risk": 0.3, "duration": 0.2, "attack_rate": 0.3, "lead_time": 0.2},
        "kinematic_final_weight": 0.7,
        "mitre_final_weight": 0.3,
        "scales": {"risk": 0.25, "attack_rate": 0.25,
                   "duration": round(math.log(10), 6), "lead_time": 15.0},
        "lead_exclusion_rule": "excluded when both sides are 0 (INDETERMINATE/unknown)",
        "live_query_features":    ["risk", "attack_rate"],
        "posthoc_query_features": ["risk", "duration", "attack_rate", "lead_time"]
    }
    with open(PHASE5_DIR / "phase5_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print(f"[✓] Saved deterministic retrieval parameters to phase5_config.json")
    results = {}
    if leading_ep_id:
        post = memory.query_by_id(leading_ep_id, exclude_dataset=leading_dataset, k=1)
        live = memory.query_by_id(leading_ep_id, exclude_dataset=leading_dataset, k=1,
                                  use=["risk", "attack_rate"])
        results["headline_leading_query_post_hoc"] = {"query_id": leading_ep_id,
                                                       "top_match": post[0] if post else None}
        results["headline_leading_query_live"]     = {"query_id": leading_ep_id,
                                                       "top_match": live[0] if live else None}
    with open(PHASE5_DIR / "phase5_retrieval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"[✓] Saved headline retrieval benchmarks to phase5_retrieval_results.json")
    print("\n[✓] Phase 5 is officially complete and frozen.")

if __name__ == "__main__":
    freeze_phase5()
