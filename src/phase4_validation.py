import json
import glob
from pathlib import Path
from datetime import datetime

EPISODE_DIR = Path("outputs/phase4_investigations")
INCIDENT_DIR = Path("outputs/incident_records")

def run_validation():
    print("=================================================================")
    print("      PHASE 4: FINAL ARCHITECTURAL VALIDATION                    ")
    print("=================================================================\n")

    total_episodes = 0
    gap_violations = 0
    peak_mismatches = 0
    duplicate_incidents = 0
    missing_refs = 0

    # 1. Load all original Phase 3 incidents as ground truth
    all_incidents = {}
    for f in glob.glob(str(INCIDENT_DIR / "*_incidents.json")):
        with open(f) as fp:
            for inc in json.load(fp):
                all_incidents[inc['incident_id']] = inc

    seen_ids = set()

    # 2. Iterate through all Phase 4 episodes and verify constraints
    for f in glob.glob(str(EPISODE_DIR / "*_episodes.json")):
        with open(f) as fp:
            episodes = json.load(fp)
            total_episodes += len(episodes)

            for ep in episodes:
                c_ids = ep.get('constituent_incident_ids', [])
                if not c_ids:
                    continue
                
                # Check A: Peak Risk Traceability
                ep_peak = ep['risk_profile']['peak_risk_score']
                actual_peak = max([all_incidents[i_id]['risk']['score'] for i_id in c_ids if i_id in all_incidents])
                if abs(ep_peak - actual_peak) > 0.01:
                    peak_mismatches += 1

                # Check B: Temporal Gap Violations (Max 60 seconds between consecutive incidents)
                for i in range(1, len(c_ids)):
                    if c_ids[i-1] in all_incidents and c_ids[i] in all_incidents:
                        t1 = datetime.strptime(all_incidents[c_ids[i-1]]['timestamp'], "%Y-%m-%d %H:%M:%S")
                        t2 = datetime.strptime(all_incidents[c_ids[i]]['timestamp'], "%Y-%m-%d %H:%M:%S")
                        if (t2 - t1).total_seconds() > 60:
                            gap_violations += 1

                # Check C: Duplicates & Orphans
                for i_id in c_ids:
                    if i_id not in all_incidents:
                        missing_refs += 1
                    if i_id in seen_ids:
                        duplicate_incidents += 1
                    seen_ids.add(i_id)

    # 3. Output Expected vs. Got Results
    print("TEST 1: Global Episode Count")
    print("  Expected: 24")
    print(f"  Got:      {total_episodes}")
    print(f"  Result:   {'[PASS]' if total_episodes == 24 else '[FAIL]'}\n")

    print("TEST 2: Temporal Gap Violations (Invariant 1)")
    print("  Expected: 0 (No episode spans unobserved missing data)")
    print(f"  Got:      {gap_violations}")
    print(f"  Result:   {'[PASS]' if gap_violations == 0 else '[FAIL]'}\n")

    print("TEST 3: Peak Risk Traceability")
    print("  Expected: 0 mismatches (Episode narrative exactly matches raw Phase 3 JSON)")
    print(f"  Got:      {peak_mismatches}")
    print(f"  Result:   {'[PASS]' if peak_mismatches == 0 else '[FAIL]'}\n")

    print("TEST 4: Incident Deduplication")
    print("  Expected: 0 duplicates (No incident belongs to multiple episodes)")
    print(f"  Got:      {duplicate_incidents}")
    print(f"  Result:   {'[PASS]' if duplicate_incidents == 0 else '[FAIL]'}\n")

    print("TEST 5: Orphaned Source References")
    print("  Expected: 0 (All episode claims map to existing Phase 3 incidents)")
    print(f"  Got:      {missing_refs}")
    print(f"  Result:   {'[PASS]' if missing_refs == 0 else '[FAIL]'}\n")

    if total_episodes == 24 and gap_violations == 0 and peak_mismatches == 0 and duplicate_incidents == 0 and missing_refs == 0:
        print("=================================================================")
        print("[✓] PHASE 4 FULLY VALIDATED & SCIENTIFICALLY SOUND.")
        print("=================================================================")
    else:
        print("[x] PHASE 4 VALIDATION FAILED. Investigate constraint violations.")

if __name__ == "__main__":
    run_validation()
