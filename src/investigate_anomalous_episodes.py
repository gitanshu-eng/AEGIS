import json
import glob
from pathlib import Path

EPISODE_DIR = Path("outputs/phase4_investigations")

def run_investigation():
    print("=================================================================")
    print("      STEP 4: ANOMALOUS EPISODE DEEP-DIVE")
    print("=================================================================\n")
    
    files = sorted(glob.glob(str(EPISODE_DIR / "*_episodes.json")))
    target_classes = ["INDETERMINATE", "F_ONLY_NO_PHYSICAL_BREACH", "BREACH_ONLY_NO_FORECAST"]
    
    anomalous_episodes = []
    
    for file in files:
        with open(file, 'r') as f:
            episodes = json.load(f)
            for ep in episodes:
                ll_class = ep.get("forecast_behavior", {}).get("classification")
                if ll_class in target_classes:
                    anomalous_episodes.append(ep)
                    
    print(f"Found {len(anomalous_episodes)} anomalous episodes.\n")
    
    for i, ep in enumerate(anomalous_episodes, 1):
        bounds = ep["temporal_bounds"]
        risk = ep["risk_profile"]
        fb = ep["forecast_behavior"]
        raw = ep["raw_evidence_at_peak"]
        
        print(f"--- Episode {i}: {ep['episode_id']} ({ep['dataset']}) ---")
        print(f"Classification : {fb['classification']}")
        print(f"Duration       : {bounds['duration_minutes']} minutes ({bounds['start_time']} to {bounds['end_time']})")
        print(f"Peak Risk      : {risk['peak_risk_score']} ({risk['peak_risk_level']}) - Driver: {ep['dominant_signal_at_peak']}")
        print(f"Forecast Time  : {fb.get('f_time', 'NONE')}")
        print(f"Breach Time    : {fb.get('b_time', 'NONE')}")
        print(f"Raw Peak Attack: {raw.get('attack_rate', 0)*100:.1f}% ({raw.get('attack_flows', 0)} flows)")
        print(f"Narrative      : {ep['investigation_summary']}\n")

if __name__ == "__main__":
    run_investigation()
