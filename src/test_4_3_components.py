import pandas as pd
from collections import Counter

# ---------------------------------------------------------
# 1. COMPONENT LOGIC (The actual 4.3 implementation)
# ---------------------------------------------------------

def extract_mitre_context(episode_incidents, frequency_threshold=0.25):
    """
    Extracts MITRE tactics/techniques, filtering out noise that 
    appears in less than X% of the episode's minutes.
    """
    total_minutes = len(episode_incidents)
    tactic_counts = Counter()
    technique_counts = Counter()
    
    for inc in episode_incidents:
        # We use a set here to avoid double-counting if a tactic 
        # is somehow listed twice in a single minute's raw data
        for tac in set(inc['candidate_attack_context']['candidate_tactics']):
            tactic_counts[tac] += 1
        for tech in set(inc['candidate_attack_context']['possible_techniques']):
            technique_counts[tech] += 1
            
    # Filter by frequency threshold
    valid_tactics = [t for t, count in tactic_counts.items() if (count / total_minutes) >= frequency_threshold]
    valid_techniques = [t for t, count in technique_counts.items() if (count / total_minutes) >= frequency_threshold]
    
    return sorted(valid_tactics), sorted(valid_techniques)

def get_raw_evidence(peak_timestamp, phase1_df):
    """
    Strictly maps a timestamp to the Phase 1 continuous file to extract 
    raw packet/flow metrics. Returns None if the timestamp falls in a gap.
    """
    # Exact match lookup
    row = phase1_df[phase1_df['time_window'] == peak_timestamp]
    
    if row.empty:
        return {"error": "TIMESTAMP_NOT_FOUND_IN_PHASE1"}
        
    r = row.iloc[0]
    
    # Gap-safety check: Ensure it's an actually observed row
    if int(r['observed']) == 0:
        return {"error": "TIMESTAMP_IS_UNOBSERVED_GAP"}
        
    return {
        "total_flows": int(r['total_flows']),
        "benign_flows": int(r['benign_flows']),
        "attack_flows": int(r['attack_flows']),
        "attack_rate": float(r['attack_rate'])
    }

# ---------------------------------------------------------
# 2. SYNTHETIC FIXTURES & VALIDATION TESTS
# ---------------------------------------------------------

def run_tests():
    print("=================================================================")
    print("      4.3 VALIDATION: MITRE & RAW EVIDENCE DRILL-DOWN")
    print("=================================================================\n")
    
    # --- FIXTURE A: MITRE Frequency Filter ---
    # 5-minute episode. 
    # TA0040 (Impact) happens all 5 minutes (100%)
    # TA0043 (Recon) happens only 1 minute (20%) -> Should be dropped at 25% threshold
    mock_incidents = []
    for i in range(5):
        tactics = ["TA0040"]
        if i == 0: tactics.append("TA0043") # Noise in the first minute only
        mock_incidents.append({"candidate_attack_context": {"candidate_tactics": tactics, "possible_techniques": []}})
        
    tactics, _ = extract_mitre_context(mock_incidents, frequency_threshold=0.25)
    
    print("TEST 1: MITRE Frequency Thresholding (25% cutoff)")
    print(f"  Expected Tactics: ['TA0040']")
    print(f"  Got Tactics:      {tactics}")
    print(f"  Result:           {'[PASS]' if tactics == ['TA0040'] else '[FAIL]'}\n")

    # --- FIXTURE B: Raw Evidence Gap-Safety ---
    # Synthetic Phase 1 CSV Data
    mock_phase1 = pd.DataFrame({
        "time_window": ["2018-03-01 10:00:00", "2018-03-01 10:01:00", "2018-03-01 10:02:00"],
        "total_flows": [1000, 0, 5000],
        "benign_flows": [900, 0, 100],
        "attack_flows": [100, 0, 4900],
        "attack_rate": [0.10, 0.0, 0.98],
        "observed": [1, 0, 1] # Note: 10:01 is an unobserved gap!
    })
    
    # Valid lookup (10:00:00)
    res_valid = get_raw_evidence("2018-03-01 10:00:00", mock_phase1)
    
    print("TEST 2: Raw Evidence Drill-Down (Valid Row)")
    print(f"  Expected Attack Rate: 0.1")
    print(f"  Got Attack Rate:      {res_valid.get('attack_rate')}")
    print(f"  Result:               {'[PASS]' if res_valid.get('attack_rate') == 0.1 else '[FAIL]'}\n")
    
    # Gap-safety lookup (10:01:00) - Should reject it, not return 0s
    res_gap = get_raw_evidence("2018-03-01 10:01:00", mock_phase1)
    
    print("TEST 3: Raw Evidence Drill-Down (Gap-Safety / Unobserved Row)")
    print(f"  Expected Error: TIMESTAMP_IS_UNOBSERVED_GAP")
    print(f"  Got Error:      {res_gap.get('error')}")
    print(f"  Result:         {'[PASS]' if res_gap.get('error') == 'TIMESTAMP_IS_UNOBSERVED_GAP' else '[FAIL]'}\n")

if __name__ == "__main__":
    run_tests()
