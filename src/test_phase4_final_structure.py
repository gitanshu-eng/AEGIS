import json
import glob
from pathlib import Path

EPISODE_DIR = Path("outputs/phase4_investigations")

def validate_episodes():
    print("=================================================================")
    print("      4.6 FINAL VALIDATION: PHASE 4 EPISODE SCHEMA")
    print("=================================================================")
    
    files = glob.glob(str(EPISODE_DIR / "*_episodes.json"))
    if not files:
        print("[FAIL] No episode JSON files found.")
        return

    total_episodes = 0
    errors = 0
    
    for file in files:
        with open(file, 'r') as f:
            episodes = json.load(f)
            
        for ep in episodes:
            total_episodes += 1
            ep_id = ep.get('episode_id', 'UNKNOWN')
            
            # 1. Root Keys Check
            expected_keys = [
                'episode_id', 'dataset', 'investigation_state', 'temporal_bounds',
                'risk_profile', 'dominant_signal_at_peak', 'forecast_behavior',
                'candidate_mitre_summary', 'raw_evidence_at_peak', 'investigation_summary',
                'constituent_incident_ids'
            ]
            for k in expected_keys:
                if k not in ep:
                    print(f"[FAIL] {ep_id} missing key: {k}")
                    errors += 1
                    
            # 2. Hardcoded State Check
            if ep.get('investigation_state') != 'NEW':
                print(f"[FAIL] {ep_id} state is not 'NEW'")
                errors += 1
                
            # 3. Narrative String Check
            summary = ep.get('investigation_summary', '')
            if not isinstance(summary, str) or len(summary) < 20:
                print(f"[FAIL] {ep_id} narrative is invalid or missing: {summary}")
                errors += 1
                
            # 4. Lead/Lag Type Check
            ll = ep.get('forecast_behavior', {})
            if 'classification' not in ll or not isinstance(ll.get('lead_time_minutes'), int):
                print(f"[FAIL] {ep_id} lead/lag structure is malformed: {ll}")
                errors += 1
                
            # 5. MITRE Type Check
            mitre = ep.get('candidate_mitre_summary', {})
            if not isinstance(mitre.get('sustained_tactics'), list):
                print(f"[FAIL] {ep_id} MITRE tactics is not a list")
                errors += 1
                
            # 6. Dominant Signal Domain Check
            valid_signals = ['Forecast', 'Activity', 'Velocity/Delta', 'Persistence']
            if ep.get('dominant_signal_at_peak') not in valid_signals:
                print(f"[FAIL] {ep_id} has invalid dominant signal: {ep.get('dominant_signal_at_peak')}")
                errors += 1

    print(f"\nTotal Episodes Checked: {total_episodes}")
    if total_episodes != 24:
        print(f"[FAIL] Expected 24 episodes, found {total_episodes}")
        errors += 1
        
    if errors == 0:
        print("[PASS] All 24 episodes structurally perfect and valid.")
        print("\n[✓] PHASE 4 IS OFFICIALLY LOCKED.")
    else:
        print(f"\n[FAIL] Found {errors} structural errors. Do not proceed to Phase 5.")

if __name__ == "__main__":
    validate_episodes()
