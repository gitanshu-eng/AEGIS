import pandas as pd
from datetime import datetime
import json

def parse_time(ts_str): return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

def compute_physical_breach(df, W=10, TAU=0.10):
    # Reviewer Patch: Drop unobserved rows explicitly, strictly prior baseline
    obs = df[df["observed"] == 1].sort_values("time_window").copy()
    obs["segment_id"] = (obs["time_window"].diff().dt.total_seconds() > 60).cumsum()
    
    # strictly prior baseline, per segment
    obs["baseline"] = obs.groupby("segment_id")["attack_rate"].transform(
        lambda s: s.shift(1).rolling(W, min_periods=W).mean()
    )
    obs["valid"] = obs["baseline"].notna()
    obs["physical_breach"] = obs["valid"] & (obs["attack_rate"] > obs["baseline"] + TAU)
    return obs

def calc_lead_lag(st, et, incidents, p1_df, F_THR=0.50, PAD=15, H=5):
    # Reviewer Patch: Windowed scoping, handling H=5 constraint
    lo, hi = st - pd.Timedelta(minutes=PAD), et + pd.Timedelta(minutes=H)
    f = [parse_time(i["timestamp"]) for i in incidents 
         if lo <= parse_time(i["timestamp"]) <= et 
         and i["risk_signals"]["forecast"] >= F_THR]
         
    w = p1_df[(p1_df.time_window >= lo) & (p1_df.time_window <= hi) & p1_df.physical_breach]
    
    if not f or w.empty:
        return {"classification": "INDETERMINATE", "lead_time_minutes": 0}
        
    lt = int((w.time_window.iloc[0] - min(f)).total_seconds() // 60)
    cls = "LEADING" if lt > 0 else "LAGGING" if lt < 0 else "SIMULTANEOUS"
    
    if lt > H:
        cls = "EARLY_UNMATCHED"  # Forecast fired earlier than horizon can explain
        
    return {"classification": cls, "lead_time_minutes": lt}

print("[✓] Causal leakage and H=5 scoping patched for Phase 4.")
