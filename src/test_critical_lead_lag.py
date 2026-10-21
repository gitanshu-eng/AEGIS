import json
import pandas as pd
from datetime import datetime
from pathlib import Path

EPISODE_DIR = Path("outputs/phase4_investigations")
INCIDENT_DIR = Path("outputs/incident_records")
PHASE1_DIR = Path("data/processed")

def parse_time(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

def calculate_lead_lag(ep_start, ep_end, dataset_incidents, dataset_name):
    f_threshold = 0.50
    f_time = None
    b_time = None
    
    st = parse_time(ep_start)
    et = parse_time(ep_end)
    
    # 1. Find f_time from Phase 3 JSON (Frozen operating threshold)
    episode_incidents = [inc for inc in dataset_incidents if st <= parse_time(inc['timestamp']) <= et]
    for inc in episode_incidents:
        if inc['risk_signals']['forecast'] >= f_threshold:
            f_time = parse_time(inc['timestamp'])
            break

    # 2. Find b_time by recreating Phase 2 Ground Truth (Y_t) from Phase 1 CSV
    p1_file = PHASE1_DIR / f"{dataset_name}_temporal_continuous.csv"
    if p1_file.exists():
        df = pd.read_csv(p1_file)
        df['timestamp'] = pd.to_datetime(df['time_window'])
        
        # Recreate Phase 2 Target Logic: W=10, H=5, tau=0.10
        df['mu_10'] = df['attack_rate'].rolling(window=10, min_periods=1).mean()
        df['max_future_5'] = df['attack_rate'].shift(-1).rolling(window=5, min_periods=1).max()
        df['Y_t'] = df['max_future_5'] > (df['mu_10'] + 0.10)
        
        # Filter to episode bounds and find first Y_t == True
        ep_df = df[(df['timestamp'] >= st) & (df['timestamp'] <= et)]
        b_events = ep_df[ep_df['Y_t'] == True]
        
        if not b_events.empty:
            b_time = b_events.iloc[0]['timestamp']

    # 3. Classify
    if f_time and b_time:
        lead_time = int((b_time - f_time).total_seconds() / 60)
        if lead_time > 0:
            classification = "LEADING"
        elif lead_time < 0:
            classification = "LAGGING"
        else:
            classification = "SIMULTANEOUS"
    elif f_time and not b_time:
        classification = "LEADING_NO_BEHAVIOR"
        lead_time = 0
    elif b_time and not f_time:
        classification = "LAGGING_NO_FORECAST"
        lead_time = 0
    else:
        classification = "INDETERMINATE"
        lead_time = 0

    return {
        "classification": classification,
        "first_forecast_elevation": str(f_time) if f_time else None,
        "first_behavioral_elevation": str(b_time) if b_time else None,
        "lead_time_minutes": lead_time
    }

def test_target(dataset, target_timestamps):
    ep_file = EPISODE_DIR / f"{dataset}_episodes.json"
    inc_file = INCIDENT_DIR / f"{dataset}_incidents.json"
    
    if not ep_file.exists() or not inc_file.exists():
        print(f"Files for {dataset} not found.")
        return
        
    with open(ep_file, 'r') as f: episodes = json.load(f)
    with open(inc_file, 'r') as f: incidents = json.load(f)
    
    print(f"\n--- Testing Dataset: {dataset} ---")
    
    for target_ts in target_timestamps:
        target_ep = None
        t_obj = parse_time(target_ts)
        for ep in episodes:
            st = parse_time(ep['temporal_bounds']['start_time'])
            et = parse_time(ep['temporal_bounds']['end_time'])
            if st <= t_obj <= et:
                target_ep = ep
                break
                
        if target_ep:
            print(f"\nTarget CRITICAL Incident: {target_ts}")
            print(f"Episode ID: {target_ep['episode_id']}")
            result = calculate_lead_lag(
                target_ep['temporal_bounds']['start_time'], 
                target_ep['temporal_bounds']['end_time'], 
                incidents,
                dataset
            )
            print(f"Classification: {result['classification']}")
            print(f"First F>=0.50:  {result['first_forecast_elevation']}")
            print(f"First Y_t=True: {result['first_behavioral_elevation']}")
            print(f"Lead Time (mins): {result['lead_time_minutes']}")
        else:
            print(f"\nTarget CRITICAL Incident: {target_ts} -> NO MATCHING EPISODE FOUND")

def run():
    print("=================================================================")
    print("      4.4 LEAD/LAG DIAGNOSTIC: V2 GROUND TRUTH LOGIC")
    print("=================================================================")
    
    test_target("Thursday-01-03-2018", ["2018-03-01 02:04:00", "2018-03-01 02:20:00"])
    test_target("Wednesday-21-02-2018", ["2018-02-21 10:23:00", "2018-02-21 10:31:00"])

if __name__ == "__main__":
    run()
