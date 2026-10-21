"""
AEGIS — CIC-IDS2017 Harmonization
Aligns CIC-IDS2017 Phase 1 output to the CIC-IDS2018 canonical schema
so Phase 2+ can consume both datasets identically.

Input:  data/processed/cic-ids2017/cic_ids2017_continuous_1min_master.csv
Output: data/processed/cic_ids2017_temporal_continuous.csv
"""

import pandas as pd
from pathlib import Path

INPUT  = Path("data/processed/cic-ids2017/cic_ids2017_continuous_1min_master.csv")
OUTPUT = Path("data/processed/cic_ids2017_temporal_continuous.csv")

# 1. Load
df = pd.read_csv(INPUT, parse_dates=["time_window"])
print(f"Loaded: {len(df)} rows")
print(f"Input columns: {df.columns.tolist()}")

# 2. Rename to match CIC-IDS2018 schema
df = df.rename(columns={
    "flow_duration_mean": "avg_flow_duration",
    "flow_bytes_sum":     "avg_flow_bytes",
    "flow_packets_sum":   "avg_flow_packets",
})

# 3. Derive attack_rate
df["attack_rate"] = df.apply(
    lambda r: r["attack_flows"] / r["total_flows"] if r["total_flows"] > 0 else 0.0,
    axis=1
)

# 4. Reorder columns to match CIC-IDS2018 exactly
CANONICAL = [
    "time_window",
    "total_flows",
    "benign_flows",
    "attack_flows",
    "avg_flow_duration",
    "avg_flow_bytes",
    "avg_flow_packets",
    "attack_rate",
    "observed",
]
df = df[CANONICAL]

# 5. Save
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print(f"\nOutput columns: {df.columns.tolist()}")
print(f"Rows written:   {len(df)}")
print(f"Saved to:       {OUTPUT}")

# 6. Sanity check
print("\n=== Sanity Check ===")
print(f"attack_rate range: {df['attack_rate'].min():.4f} – {df['attack_rate'].max():.4f}")
print(f"observed windows:  {df['observed'].sum()} / {len(df)}")
print(f"date range:        {df['time_window'].min()} → {df['time_window'].max()}")
print(f"total attack flows: {df['attack_flows'].sum():,}")
print(f"total benign flows: {df['benign_flows'].sum():,}")

# 7. Confirm schema matches 2018
import glob
files_2018 = sorted(glob.glob("data/processed/*-2018_temporal_continuous.csv"))
if files_2018:
    df18 = pd.read_csv(files_2018[0])
    match = df.columns.tolist() == df18.columns.tolist()
    print(f"\nSchema matches CIC-IDS2018: {match}")
    if not match:
        print(f"  2017: {df.columns.tolist()}")
        print(f"  2018: {df18.columns.tolist()}")
