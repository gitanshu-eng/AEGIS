# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAG_COLS = ["attack_rate", "total_flows", "benign_flows", "attack_flows",
            "avg_flow_duration", "avg_flow_bytes", "avg_flow_packets"]
LAG_WINDOWS = [1, 2, 3, 5]

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["segment_id"] = 0
    seg = 0
    for i in range(len(df)):
        if i == 0:
            df.at[i, "segment_id"] = seg
            continue
        prev_ts = pd.Timestamp(df.at[i-1, "timestamp"])
        curr_ts = pd.Timestamp(df.at[i,   "timestamp"])
        if (curr_ts - prev_ts) != pd.Timedelta(minutes=1):
            seg += 1
        df.at[i, "segment_id"] = seg

    for col in LAG_COLS:
        if col not in df.columns:
            continue
        for lag in LAG_WINDOWS:
            df[f"{col}_lag_{lag}"] = df.groupby("segment_id")[col].shift(lag)

    feature_cols = [f"{c}_lag_{l}" for c in LAG_COLS for l in LAG_WINDOWS
                    if f"{c}_lag_{l}" in df.columns]
    df = df.dropna(subset=feature_cols).copy()
    return df

if __name__ == "__main__":
    from src.pcap_to_flows import extract_flows
    pcap_path = os.path.join(BASE_DIR, "data", "pcap_synthetic", "cic_ids2018_mar02_synthetic.pcap")
    flows = extract_flows(pcap_path)
    features = compute_features(flows)
    print(f"Rows with full feature set: {len(features)}")
    print(features[["timestamp", "attack_rate", "attack_rate_lag_1", "attack_rate_lag_2"]].head(10).to_string(index=False))
