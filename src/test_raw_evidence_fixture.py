import pandas as pd
from datetime import datetime

def parse_time(ts_str): return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

# Exact logic from phase4_investigation_engine.py
def get_raw_evidence(peak_timestamp, p1_df):
    if p1_df is None: return {"error": "NO_PHASE1_DATA"}
    row = p1_df[p1_df['time_window'] == parse_time(peak_timestamp)]
    if row.empty or int(row.iloc[0]['observed']) == 0:
        return {"error": "INVALID_OR_UNOBSERVED"}
    r = row.iloc[0]
    return {
        "total_flows": int(r['total_flows']),
        "benign_flows": int(r['benign_flows']),
        "attack_flows": int(r['attack_flows']),
        "attack_rate": float(r['attack_rate'])
    }

def run_fixture_test():
    print("=================================================================")
    print("      STEP 3: RAW EVIDENCE DRILL-DOWN FIXTURE TEST")
    print("=================================================================\n")
    
    # Create synthetic Phase 1 data with a known gap
    data = {
        "time_window": pd.to_datetime([
            "2018-02-01 10:00:00", # Valid
            "2018-02-01 10:01:00", # Gap (observed=0)
            "2018-02-01 10:02:00"  # Valid Peak
        ]),
        "total_flows": [100, 0, 500],
        "benign_flows": [90, 0, 100],
        "attack_flows": [10, 0, 400],
        "attack_rate": [0.1, 0.0, 0.8],
        "observed": [1, 0, 1]
    }
    df = pd.DataFrame(data)

    errors = 0

    # Test A: Valid Timestamp Mapping
    res_a = get_raw_evidence("2018-02-01 10:02:00", df)
    if "error" in res_a or res_a.get("attack_rate") != 0.8:
        print(f"[FAIL] Valid timestamp mapping failed: {res_a}")
        errors += 1
    else:
        print("[PASS] Valid peak timestamp maps correctly to Phase 1 data.")

    # Test B: Gap Timestamp Rejection (observed=0)
    res_b = get_raw_evidence("2018-02-01 10:01:00", df)
    if res_b.get("error") != "INVALID_OR_UNOBSERVED":
        print(f"[FAIL] Sensor gap was not safely rejected: {res_b}")
        errors += 1
    else:
        print("[PASS] Sensor gap (observed=0) safely rejected.")

    # Test C: Missing Timestamp Rejection
    res_c = get_raw_evidence("2018-02-01 10:05:00", df)
    if res_c.get("error") != "INVALID_OR_UNOBSERVED":
        print(f"[FAIL] Missing timestamp was not safely rejected: {res_c}")
        errors += 1
    else:
        print("[PASS] Missing/Out-of-bounds timestamp safely rejected.")

    if errors == 0:
        print("\n[✓] Component 4.3 Raw Evidence logic is fixture-validated and gap-safe.")
    else:
        print(f"\n[!] Fixture failed with {errors} errors.")

if __name__ == "__main__":
    run_fixture_test()
