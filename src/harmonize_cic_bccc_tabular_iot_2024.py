"""
Harmonizer: CIC-BCCC-NRC TabularIoTAttack-2024
Input : data/processed/cic-bccc-tabular-iot-2024/cic_bccc_tabular_iot_2024_continuous_1min_master.csv
Output: data/processed/cic_bccc_tabular_iot_2024_temporal_continuous.csv
"""
import pandas as pd
from pathlib import Path

MASTER   = Path("data/processed/cic_bccc_tabular_iot_2024_continuous_1min_master.csv")
OUT      = Path("data/processed/cic_bccc_tabular_iot_2024_temporal_continuous.csv")

CANONICAL_COLS = [
    "time_window","total_flows","benign_flows","attack_flows",
    "avg_flow_duration","avg_flow_bytes","avg_flow_packets","attack_rate","observed"
]

RENAME_MAP = {
    "flow_duration_mean": "avg_flow_duration",
    "flow_bytes_sum":     "avg_flow_bytes",
    "flow_packets_sum":   "avg_flow_packets"
}

def harmonize():
    print(f"Reading: {MASTER}")
    df = pd.read_csv(MASTER, parse_dates=["time_window"])
    print(f"  Raw columns : {df.columns.tolist()}")

    rename = {k: v for k, v in RENAME_MAP.items() if k in df.columns and k != v}
    if rename:
        df = df.rename(columns=rename)

    if "attack_rate" not in df.columns:
        df["attack_rate"] = df["attack_flows"] / df["total_flows"].replace(0, 1)

    missing = [c for c in CANONICAL_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing canonical columns: {missing}")

    df = df[CANONICAL_COLS]
    df["avg_flow_duration"] = df["avg_flow_duration"].astype(float)
    df["avg_flow_bytes"]    = df["avg_flow_bytes"].astype(float)
    df["avg_flow_packets"]  = df["avg_flow_packets"].astype(float)

    df.to_csv(OUT, index=False)
    print(f"\nOutput : {OUT}")
    print(f"  Rows           : {len(df):,}")
    print(f"  Observed       : {df['observed'].sum():,}")
    print(f"  Date range     : {df['time_window'].min()} → {df['time_window'].max()}")
    print(f"  Attack windows : {(df['attack_flows'] > 0).sum():,}")
    print(f"  Columns        : {list(df.columns)}")
    print(f"  Null count     : {df.isnull().sum().sum()}")
    print("\n✅ Harmonization complete — Phase 2 will auto-pick up this file.")

if __name__ == "__main__":
    harmonize()
