"""
AEGIS — CIC IoT-DIAD 2024 Phase 1 Pipeline
Reads raw files from S3, builds per-file 1-minute temporal grids,
aggregates to canonical schema, produces master CSV and manifest.

Label strategy: derived from filename, not Label column.
Skip strategy: DoS-TCP_Flood files are near-empty and skipped.
Temporal strategy: per-file grids concatenated into master.
                   Cross-file gaps are expected and correct.
"""

import io
import json
import re
import sys
from pathlib import Path

import boto3
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.adapters.cic_iot_diad_2024 import CICIoTDIAD2024Adapter

# ── Config ────────────────────────────────────────────────────────────────
BUCKET     = "aegis-cic-training-2026-model.v1"
S3_PREFIX  = "datasets/cic-iot-diad-2024/raw/"
S3_OUT     = "features/cic-iot-diad-2024/"

LOCAL_OUT  = Path("data/processed/cic-iot-diad-2024")
MANIFEST_F = Path("data/manifests/cic_iot_diad_2024_manifest.json")

LOCAL_OUT.mkdir(parents=True, exist_ok=True)
MANIFEST_F.parent.mkdir(parents=True, exist_ok=True)

MIN_FILE_BYTES = 1_000   # skip near-empty files
FREQ           = "1min"

adapter = CICIoTDIAD2024Adapter()
s3      = boto3.client("s3")


def list_raw_files():
    """List all valid raw CSVs on S3, skipping near-empty and TCP_Flood files."""
    paginator = s3.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=S3_PREFIX):
        for obj in page.get("Contents", []):
            key  = obj["Key"]
            size = obj["Size"]
            name = key.split("/")[-1]
            if not name.endswith(".csv"):
                continue
            if size < MIN_FILE_BYTES:
                print(f"  [SKIP] {name} ({size} bytes — near-empty)")
                continue
            if adapter.should_skip(name):
                print(f"  [SKIP] {name} — DoS-TCP_Flood")
                continue
            files.append((key, name, size))
    return sorted(files)


def stream_aggregate_from_s3(key: str, label: str) -> pd.DataFrame:
    """
    Stream file from S3 in 200k-row chunks.
    Aggregate each chunk immediately and discard raw rows.
    Never holds full file in RAM.
    Returns aggregated per-minute DataFrame.
    """
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    body = obj["Body"].read()
    
    agg_frames = []
    for chunk in pd.read_csv(io.BytesIO(body), low_memory=False,
                              chunksize=200_000):
        chunk.columns = chunk.columns.str.strip()
        
        # Parse timestamps
        parsed = pd.to_datetime(
            chunk[adapter.TIMESTAMP_COLUMN],
            format="mixed", dayfirst=True, errors="coerce"
        )
        valid = parsed.notna() & (parsed >= adapter.VALID_TIMESTAMP_START)
        chunk = chunk[valid].copy()
        if chunk.empty:
            continue
        
        chunk["timestamp"] = parsed[valid].values
        chunk["time_window"] = chunk["timestamp"].dt.floor("1min")
        chunk["is_attack"] = (label.lower() != "benign")
        
        # Replace inf
        import numpy as np
        for col in [adapter.FLOW_DURATION_COLUMN,
                    adapter.FLOW_BYTES_COLUMN,
                    adapter.FLOW_PACKETS_COLUMN]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
            chunk[col] = chunk[col].replace([np.inf, -np.inf], np.nan).fillna(0)
        
        agg = chunk.groupby("time_window").agg(
            total_flows       =("timestamp",                    "count"),
            attack_flows      =("is_attack",                    "sum"),
            flow_bytes_sum    =(adapter.FLOW_BYTES_COLUMN,      "sum"),
            flow_packets_sum  =(adapter.FLOW_PACKETS_COLUMN,    "sum"),
            flow_duration_mean=(adapter.FLOW_DURATION_COLUMN,   "mean"),
        ).reset_index()
        agg_frames.append(agg)
        del chunk
    
    if not agg_frames:
        return pd.DataFrame()
    
    # Merge chunk aggregations
    combined = pd.concat(agg_frames, ignore_index=True)
    final = combined.groupby("time_window").agg(
        total_flows       =("total_flows",        "sum"),
        attack_flows      =("attack_flows",        "sum"),
        flow_bytes_sum    =("flow_bytes_sum",      "sum"),
        flow_packets_sum  =("flow_packets_sum",    "sum"),
        flow_duration_mean=("flow_duration_mean",  "mean"),
    ).reset_index()
    return final


def build_grid_from_agg(agg: pd.DataFrame, label: str) -> pd.DataFrame:
    """
    Takes a pre-aggregated per-minute DataFrame and builds
    a continuous 1-min grid with zero-filled gaps.
    """
    agg["benign_flows"] = agg["total_flows"] - agg["attack_flows"]

    t_min = agg["time_window"].min()
    t_max = agg["time_window"].max()
    full_grid = pd.DataFrame(
        {"time_window": pd.date_range(start=t_min, end=t_max, freq=FREQ)}
    )
    merged = full_grid.merge(agg, on="time_window", how="left")
    merged["observed"] = merged["total_flows"].notna().astype(int)

    for col in ["total_flows","attack_flows","benign_flows",
                "flow_bytes_sum","flow_packets_sum"]:
        merged[col] = merged[col].fillna(0).astype(int)
    merged["flow_duration_mean"] = merged["flow_duration_mean"].fillna(0.0)
    merged["label"] = label
    return merged


def build_1min_grid(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """
    Assigns filename-derived label, normalizes, builds 1-min temporal grid.
    Returns canonical aggregated DataFrame for this file.
    """
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Inject filename label before normalize
    df["label"] = label

    # Clean and normalize
    df, missing, invalid = adapter.clean_raw(df)
    df = adapter.normalize(df)

    if df.empty:
        return pd.DataFrame()

    # Floor to minute
    df["time_window"] = df["timestamp"].dt.floor(FREQ)

    df["is_attack"] = df["label"].apply(adapter.is_attack).astype(int)

    # Aggregate per minute
    agg = df.groupby("time_window").agg(
        total_flows       =("timestamp",    "count"),
        attack_flows      =("is_attack",    "sum"),
        flow_bytes_sum    =("flow_bytes",   "sum"),
        flow_packets_sum  =("flow_packets", "sum"),
        flow_duration_mean=("flow_duration","mean"),
    ).reset_index()

    agg["benign_flows"] = agg["total_flows"] - agg["attack_flows"]

    # Build continuous 1-min grid for this file's time span
    t_min = agg["time_window"].min()
    t_max = agg["time_window"].max()
    full_grid = pd.DataFrame(
        {"time_window": pd.date_range(start=t_min, end=t_max, freq=FREQ)}
    )

    merged = full_grid.merge(agg, on="time_window", how="left")
    merged["observed"] = merged["total_flows"].notna().astype(int)

    # Zero-fill unobserved windows
    for col in ["total_flows","attack_flows","benign_flows",
                "flow_bytes_sum","flow_packets_sum"]:
        merged[col] = merged[col].fillna(0).astype(int)
    merged["flow_duration_mean"] = merged["flow_duration_mean"].fillna(0.0)

    merged["label"] = label
    return merged


def run():
    print("=" * 65)
    print("  AEGIS PHASE 1 — CIC IoT-DIAD 2024")
    print("=" * 65 + "\n")

    files = list_raw_files()
    print(f"\nFiles to process: {len(files)}\n")

    all_grids    = []
    file_summaries = {}
    total_attack = 0
    total_benign = 0
    total_flows  = 0

    for key, name, size in files:
        label = CICIoTDIAD2024Adapter.label_from_filename(name)
        print(f"  Processing: {name}")
        print(f"    Label   : {label}  |  Size: {size/1e6:.1f} MB")

        try:
            agg_df = stream_aggregate_from_s3(key, label)
            if agg_df.empty:
                print(f"    [WARN] Empty after aggregation — skipped.")
                continue
            grid = build_grid_from_agg(agg_df, label)
        except Exception as e:
            print(f"    [ERROR] {e}")
            continue

        if grid.empty:
            print(f"    [WARN] Empty grid after processing — skipped.")
            continue

        # Save per-file grid
        out_name = name.replace(".pcap_Flow.csv", "_continuous_1min.csv")
        out_path = LOCAL_OUT / out_name
        grid.to_csv(out_path, index=False)

        atk = int(grid["attack_flows"].sum())
        ben = int(grid["benign_flows"].sum())
        tot = int(grid["total_flows"].sum())

        file_summaries[name] = {
            "label":            label,
            "start_window":     str(grid["time_window"].min()),
            "end_window":       str(grid["time_window"].max()),
            "total_windows":    len(grid),
            "observed_windows": int(grid["observed"].sum()),
            "attack_flows":     atk,
            "benign_flows":     ben,
            "total_flows":      tot,
        }

        total_attack += atk
        total_benign += ben
        total_flows  += tot
        all_grids.append(grid)

        print(f"    Windows : {len(grid)} total / "
              f"{int(grid['observed'].sum())} observed")
        print(f"    Flows   : {tot:,} total / "
              f"{atk:,} attack / {ben:,} benign")

    # ── Master consolidation ───────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  Building master timeline...")

    master = pd.concat(all_grids, ignore_index=True)
    master = master.sort_values("time_window").reset_index(drop=True)

    master_path = LOCAL_OUT / "cic_iot_diad_2024_continuous_1min_master.csv"
    master.to_csv(master_path, index=False)

    # ── Manifest ──────────────────────────────────────────────────────
    manifest = {
        "dataset_name":       "CIC-IoT-DIAD-2024",
        "temporal_resolution":"1min",
        "total_windows":      len(master),
        "total_flows":        total_flows,
        "total_attack_flows": total_attack,
        "total_benign_flows": total_benign,
        "attack_ratio":       round(total_attack / total_flows, 6) if total_flows else 0,
        "time_range": {
            "start": str(master["time_window"].min()),
            "end":   str(master["time_window"].max()),
        },
        "canonical_columns":  master.columns.tolist(),
        "files":              file_summaries,
    }

    with open(MANIFEST_F, "w") as f:
        json.dump(manifest, f, indent=2)

    # ── Sync to S3 ────────────────────────────────────────────────────
    print("  Syncing to S3...")
    s3.upload_file(
        str(master_path), BUCKET,
        S3_OUT + "cic_iot_diad_2024_continuous_1min_master.csv"
    )
    s3.upload_file(
        str(MANIFEST_F), BUCKET,
        S3_OUT + "manifest.json"
    )

    print("\n" + "=" * 65)
    print("  PHASE 1 COMPLETE")
    print("=" * 65)
    print(f"  Files processed : {len(file_summaries)}")
    print(f"  Total windows   : {len(master):,}")
    print(f"  Total flows     : {total_flows:,}")
    print(f"  Attack flows    : {total_attack:,}")
    print(f"  Benign flows    : {total_benign:,}")
    print(f"  Attack ratio    : {manifest['attack_ratio']:.4f}")
    print(f"  Date range      : {manifest['time_range']['start']} → "
          f"{manifest['time_range']['end']}")
    print(f"  Master saved    : {master_path}")
    print(f"  Manifest saved  : {MANIFEST_F}")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).resolve().parents[1])
    run()
