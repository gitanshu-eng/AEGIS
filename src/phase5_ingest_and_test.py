import json
import glob
from pathlib import Path
from datetime import datetime
import sys

try:
    from phase5_retrieval import EpisodeMemory
except ImportError:
    print("[!] Error: Could not import phase5_retrieval. Ensure the patched engine is in the src directory.")
    sys.exit(1)

EPISODE_DIR = Path("outputs/phase4_investigations")

def parse_time(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

def run_phase5_pipeline():
    print("=================================================================")
    print("      PHASE 5: INGESTION & RETRIEVAL VALIDATION")
    print("=================================================================\n")

    # STEP 1: INGESTION
    memory = EpisodeMemory()
    files = sorted(glob.glob(str(EPISODE_DIR / "*_episodes.json")))
    
    leading_ep_id = None
    ingested_count = 0

    for file in files:
        with open(file, 'r') as f:
            episodes = json.load(f)
            
        for ep in episodes:
            lt = ep["forecast_behavior"].get("lead_time_minutes")
            if lt is None: lt = 0
            
            # Normalize risk (0-100 to 0-1) and attack rate
            risk_norm = ep["risk_profile"]["peak_risk_score"] / 100.0
            attack_rate = ep["raw_evidence_at_peak"].get("attack_rate", 0.0)
            
            mem_record = {
                "memory_id": ep["episode_id"],
                "dataset": ep["dataset"],
                "closed_at": parse_time(ep["temporal_bounds"]["end_time"]),
                "structured_metadata": {
                    "peak_risk_level": ep["risk_profile"]["peak_risk_level"],
                    "lead_lag_classification": ep["forecast_behavior"]["classification"],
                    "sustained_tactics": ep["candidate_mitre_summary"].get("sustained_tactics", [])
                },
                "semantic_context": {
                    "kinematic_vector": [
                        risk_norm,
                        ep["temporal_bounds"]["duration_minutes"],
                        attack_rate,
                        lt
                    ]
                }
            }
            memory.from_memory_obj(mem_record)
            ingested_count += 1
            
            # Identify our 1 LEADING episode for Step 3
            if ep["forecast_behavior"]["classification"] == "LEADING":
                leading_ep_id = ep["episode_id"]

    print(f"[✓] Step 1: {ingested_count} episodes ingested into Memory Bank.\n")

    # STEP 2: ADVERSARIAL TESTS
    errors = 0
    
    # A. Hallucinated ID
    try:
        memory.query_by_id("EP-FAKE-999")
        print("[FAIL] Engine did not reject hallucinated ID.")
        errors += 1
    except KeyError:
        print("[PASS] Hallucinated ID explicitly rejected.")

    # B. Dataset Exclusion (Query an episode, exclude its own dataset)
    if leading_ep_id:
        test_ep = memory.bank[leading_ep_id]
        res = memory.query_by_id(leading_ep_id, exclude_dataset=test_ep["dataset"])
        excluded = [r for r in res if r["dataset"] == test_ep["dataset"]]
        if excluded:
            print("[FAIL] Dataset exclusion filter failed.")
            errors += 1
        else:
            print("[PASS] Dataset exclusion filter securely overrides similarity.")

    # C. Self-Exclusion
    if leading_ep_id:
        res = memory.query_by_id(leading_ep_id)
        if any(r["memory_id"] == leading_ep_id for r in res):
            print("[FAIL] Self-exclusion failed. Episode returned itself.")
            errors += 1
        else:
            print("[PASS] Self-exclusion intact.")

    print(f"\n[✓] Step 2: Adversarial tests complete. Errors: {errors}\n")

    # STEP 3: HEADLINE RETRIEVAL (The 7-min LEADING episode)
    if not leading_ep_id:
        print("[!] Could not locate the LEADING episode for the headline test.")
        return

    print("--- STEP 3: HEADLINE RETRIEVAL (LEADING EPISODE) ---")
    print(f"Target Episode: {leading_ep_id} (7-min predictive warning)")
    
    top_matches = memory.query_by_id(leading_ep_id, exclude_dataset=memory.bank[leading_ep_id]["dataset"], k=1)
    
    if top_matches:
        match = top_matches[0]
        print(f"\nTop Historical Match: {match['memory_id']} ({match['dataset']})")
        print(f"Total Similarity: {match['similarity_score']:.4f}")
        print(f"Sub-scores: {match['sub_scores']}")
        print(f"Match Classification: {match['structured_metadata']['lead_lag_classification']}")
        print(f"Match Tactics: {match['structured_metadata']['sustained_tactics']}")
    else:
        print("No historical matches found under current constraints.")

if __name__ == "__main__":
    run_phase5_pipeline()
