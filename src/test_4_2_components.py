def get_dominant_signal(peak_inc):
    s = peak_inc['risk_signals']
    w = {
        'Forecast': s['forecast'] * 0.35, 
        'Activity': s['activity'] * 0.35, 
        'Velocity/Delta': s['delta'] * 0.15, 
        'Proximity': s['proximity'] * 0.15
    }
    return max(w, key=w.get)

def gen_narrative(ep_id, dur, peak_risk, dom_sig, tacs, raw, ll):
    mitre = ", ".join(tacs) if tacs else "No sustained tactics (>25%)"
    lt = ll.get('lead_time_minutes', 0)
    lc = ll.get('classification', 'INDETERMINATE')
    raw_str = f"{raw.get('attack_rate', 0)*100:.1f}% attack rate" if "error" not in raw else "Unobserved/Gap"
    
    return (f"Investigation Episode {ep_id} spans {dur} minutes, peaking at a {peak_risk['level']} risk state "
            f"(Score: {peak_risk['score']:.2f}). The dominant kinematic driver at peak was {dom_sig}. "
            f"Sustained MITRE ATT&CK behaviors: {mitre}. "
            f"Physical evidence at peak: {raw_str}. "
            f"Prediction vs. Reality: Forecast was {lc} (Lead time: {lt} min).")

def run_tests():
    print("=================================================================")
    print("      4.2 VALIDATION: DOMINANT SIGNAL & NARRATIVE TEMPLATE")
    print("=================================================================\n")
    
    # --- FIXTURE A: Dominant Signal Math ---
    # F * 0.35 = 0.315
    # A * 0.35 = 0.175
    # D * 0.15 = 0.150
    # P * 0.15 = 0.150
    # Expected dominant: 'Forecast'
    mock_peak = {'risk_signals': {'forecast': 0.90, 'activity': 0.50, 'delta': 1.0, 'proximity': 1.0}}
    dom = get_dominant_signal(mock_peak)
    
    print("TEST 1: Dominant Signal Weighting")
    print(f"  Expected: Forecast")
    print(f"  Got:      {dom}")
    print(f"  Result:   {'[PASS]' if dom == 'Forecast' else '[FAIL]'}\n")

    # --- FIXTURE B: Narrative Generation (Happy Path) ---
    narrative_1 = gen_narrative(
        ep_id="EP-TEST-123", dur=45, 
        peak_risk={'level': 'CRITICAL', 'score': 85.5}, dom_sig="Activity", 
        tacs=["TA0040", "TA0043"], raw={'attack_rate': 0.95}, 
        ll={'classification': 'LEADING', 'lead_time_minutes': 7}
    )
    
    print("TEST 2: Narrative Generation (Standard)")
    print(f"  Output: {narrative_1}")
    print(f"  Result: {'[PASS]' if '95.0% attack rate' in narrative_1 and 'TA0040, TA0043' in narrative_1 else '[FAIL]'}\n")

    # --- FIXTURE C: Narrative Generation (Edge Cases - Gap & No MITRE) ---
    narrative_2 = gen_narrative(
        ep_id="EP-TEST-999", dur=3, 
        peak_risk={'level': 'MEDIUM', 'score': 45.0}, dom_sig="Forecast", 
        tacs=[], raw={'error': 'INVALID_OR_UNOBSERVED'}, 
        ll={'classification': 'F_ONLY_NO_PHYSICAL_BREACH', 'lead_time_minutes': 0}
    )
    
    print("TEST 3: Narrative Generation (Edge Cases)")
    print(f"  Output: {narrative_2}")
    print(f"  Result: {'[PASS]' if 'Unobserved/Gap' in narrative_2 and 'No sustained tactics' in narrative_2 else '[FAIL]'}\n")

if __name__ == "__main__":
    run_tests()
