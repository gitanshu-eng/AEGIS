import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC  = PROJECT_ROOT / "data" / "processed" / "cic-iot-diad-2024" / "cic_iot_diad_2024_continuous_1min_master.csv"
DEST = PROJECT_ROOT / "data" / "processed" / "cic_iot_diad_2024_temporal_continuous.csv"

CANONICAL_COLS = [
    "time_window", "total_flows", "benign_flows", "attack_flows",
    "avg_flow_duration", "avg_flow_bytes", "avg_flow_packets",
    "attack_rate", "observed",
]

RENAME_MAP = {
    "flow_duration_mean": "avg_flow_duration",
    "flow_bytes_sum":     "avg_flow_bytes",
    "flow_packets_sum":   "avg_flow_packets",
}

def main():
    if not SRC.exists():
        print(f"[ERROR] Not found: {SRC}")
        sys.exit(1)

    print(f"Reading: {SRC}")
    df = pd.read_csv(SRC, parse_dates=["time_window"])
    print(f"  Raw columns : {df.columns.tolist()}")
    print(f"  Rows        : {len(df):,}")

    rename = {k: v for k, v in RENAME_MAP.items() if k in df.columns and k != v}
    if rename:
        print(f"  Renaming    : {rename}")
        df = df.rename(columns=rename)

    if "attack_rate" not in df.columns:
        print("  Deriving attack_rate")
        df["attack_rate"] = np.where(
            df["total_flows"] > 0,
            df["attack_flows"] / df["total_flows"],
            0.0,
        )

    missing = [c for c in CANONICAL_COLS if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing after rename: {missing}")
        print(f"  Available: {df.columns.tolist()}")
        sys.exit(1)

    df = df[CANONICAL_COLS].copy()
    df["time_window"]       = pd.to_datetime(df["time_window"])
    df["total_flows"]       = df["total_flows"].astype(int)
    df["benign_flows"]      = df["benign_flows"].astype(int)
    df["attack_flows"]      = df["attack_flows"].astype(int)
    df["observed"]          = df["observed"].astype(int)
    df["attack_rate"]       = df["attack_rate"].astype(float).clip(0.0, 1.0)
    df["avg_flow_duration"] = df["avg_flow_duration"].astype(float)
    df["avg_flow_bytes"]    = df["avg_flow_bytes"].astype(float)
    df["avg_flow_packets"]  = df["avg_flow_packets"].astype(float)

    df = df.sort_values("time_window").reset_index(drop=True)

    null_count = df.isnull().sum().sum()
    if null_count > 0:
        print(f"  [WARN] {null_count} nulls — filling zeros")
        df = df.fillna(0)

    assert (df["attack_rate"] >= 0).all() and (df["attack_rate"] <= 1).all()
    assert (df["total_flows"] >= 0).all()

    DEST.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DEST, index=False)

    print(f"\nOutput : {DEST}")
    print(f"  Rows           : {len(df):,}")
    print(f"  Observed       : {int(df['observed'].sum()):,}")
    print(f"  Date range     : {df['time_window'].min()} → {df['time_window'].max()}")
    print(f"  Attack windows : {int((df['attack_flows'] > 0).sum()):,}")
    print(f"  Columns        : {list(df.columns)}")
    print(f"  Null count     : {df.isnull().sum().sum()}")
    print("\n✅ Harmonization complete — Phase 2 will auto-pick up this file.")

if __name__ == "__main__":
    main()
