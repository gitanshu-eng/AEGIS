"""
src/process_s3_phase1_apt_iiot_2024.py
"""

import io
import os
import json
import zipfile
import argparse
import numpy as np
import pandas as pd
import boto3
import kaggle
from pathlib import Path
from collections import defaultdict

KAGGLE_DATASET = "waqarkha/cicapt-iiot"
KAGGLE_FILES   = ["phase1_NetworkData.csv", "phase2_NetworkData.csv"]

S3_BUCKET  = "aegis-cic-training-2026-model.v1"
S3_OUT     = "tabular-iot-attack-2024/processed/"
S3_MANIFEST= "tabular-iot-attack-2024/manifests/"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR      = PROJECT_ROOT / "data" / "processed" / "cic-apt-iiot-2024"
MANIFEST_DIR = PROJECT_ROOT / "data" / "manifests"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CSV    = OUT_DIR / "cic_apt_iiot_2024_continuous_1min_master.csv"
MANIFEST_JSON = MANIFEST_DIR / "cic_apt_iiot_2024_manifest.json"

FREQ       = "1min"
CHUNK_SIZE = 200_000
USECOLS    = ["ts", "label", "flow_duration", "Tot size", "Number"]


def stream_and_aggregate(fname):
    print(f"\n  Downloading: {fname} from Kaggle...")
    kaggle.api.dataset_download_file(KAGGLE_DATASET, fname, path="/tmp", quiet=False, force=True)

    zip_path = f"/tmp/{fname}.zip"
    csv_path = f"/tmp/{fname}"

    if os.path.exists(zip_path):
        zf  = zipfile.ZipFile(zip_path, 'r')
        fh  = zf.open(fname)
        cleanup = [zip_path]
    elif os.path.exists(csv_path):
        fh  = open(csv_path, 'rb')
        zf  = None
        cleanup = [csv_path]
    else:
        raise FileNotFoundError(f"Could not find downloaded file for {fname}")

    agg_buckets = defaultdict(lambda: {
        "total_flows": 0, "attack_flows": 0, "benign_flows": 0,
        "flow_duration_sum": 0.0, "flow_bytes_sum": 0.0,
        "flow_packets_sum": 0.0, "flow_count": 0,
    })

    chunk_iter = pd.read_csv(
        fh,
        usecols=USECOLS,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        dtype={
            "ts":            "float64",
            "label":         "int8",
            "flow_duration": "float32",
            "Tot size":      "float32",
            "Number":        "float32",
        }
    )

    total_rows = 0
    for i, chunk in enumerate(chunk_iter):
        chunk["ts"] = pd.to_numeric(chunk["ts"], errors="coerce")
        chunk.dropna(subset=["ts"], inplace=True)
        chunk.replace([np.inf, -np.inf], np.nan, inplace=True)
        chunk.dropna(subset=["flow_duration", "Tot size", "Number"], inplace=True)
        chunk = chunk[chunk["ts"] > 1_577_836_800]

        chunk["time_window"] = pd.to_datetime(chunk["ts"], unit="s").dt.floor(FREQ)

        for tw, grp in chunk.groupby("time_window"):
            b = agg_buckets[tw]
            b["total_flows"]       += len(grp)
            b["attack_flows"]      += int((grp["label"] == 1).sum())
            b["benign_flows"]      += int((grp["label"] == 0).sum())
            b["flow_duration_sum"] += float(grp["flow_duration"].sum())
            b["flow_bytes_sum"]    += float(grp["Tot size"].sum())
            b["flow_packets_sum"]  += float(grp["Number"].sum())
            b["flow_count"]        += len(grp)

        total_rows += len(chunk)
        if (i + 1) % 10 == 0:
            print(f"    Chunk {i+1} — {total_rows:,} rows so far")

    fh.close()
    if zf: zf.close()
    for p in cleanup:
        if os.path.exists(p): os.remove(p)

    print(f"    Done — {total_rows:,} rows, {len(agg_buckets):,} windows")

    records = []
    for tw, b in agg_buckets.items():
        n = b["flow_count"]
        records.append({
            "time_window":        tw,
            "total_flows":        b["total_flows"],
            "attack_flows":       b["attack_flows"],
            "benign_flows":       b["benign_flows"],
            "flow_duration_mean": b["flow_duration_sum"] / n if n > 0 else 0.0,
            "flow_bytes_sum":     b["flow_bytes_sum"],
            "flow_packets_sum":   b["flow_packets_sum"],
        })
    return pd.DataFrame(records)


def build_grid(agg):
    agg = agg.sort_values("time_window").reset_index(drop=True)
    full_grid = pd.DataFrame({"time_window": pd.date_range(agg["time_window"].min(), agg["time_window"].max(), freq=FREQ)})
    merged = full_grid.merge(agg, on="time_window", how="left")
    merged["observed"] = merged["total_flows"].notna().astype(int)
    merged = merged.fillna(0)
    merged["attack_rate"] = np.where(merged["total_flows"] > 0, merged["attack_flows"] / merged["total_flows"], 0.0)
    return merged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-upload", action="store_true")
    args = parser.parse_args()

    kaggle.api.authenticate()

    all_aggs, file_metas = [], []

    for fname in KAGGLE_FILES:
        print(f"\n{'='*60}\nProcessing: {fname}\n{'='*60}")
        agg  = stream_and_aggregate(fname)
        grid = build_grid(agg)

        per_file_csv = OUT_DIR / f"{fname.replace('.csv','')}_1min.csv"
        grid.to_csv(per_file_csv, index=False)

        all_aggs.append(agg)
        total = int(agg["total_flows"].sum())
        atk   = int(agg["attack_flows"].sum())
        ben   = int(agg["benign_flows"].sum())
        file_metas.append({
            "filename": fname, "rows_raw": total, "windows": len(grid),
            "observed": int(grid["observed"].sum()), "attack_flows": atk,
            "benign_flows": ben, "date_min": str(grid["time_window"].min()),
            "date_max": str(grid["time_window"].max()),
            "attack_rate_mean": atk/total if total > 0 else 0.0,
        })
        print(f"    Windows: {len(grid):,} total / {int(grid['observed'].sum()):,} observed")
        print(f"    Flows  : {total:,} total / {atk:,} attack / {ben:,} benign")

    print(f"\n{'='*60}\nBuilding master CSV...")
    combined  = pd.concat(all_aggs, ignore_index=True)
    master_agg = combined.groupby("time_window").agg(
        total_flows       =("total_flows",        "sum"),
        attack_flows      =("attack_flows",        "sum"),
        benign_flows      =("benign_flows",        "sum"),
        flow_duration_mean=("flow_duration_mean",  "mean"),
        flow_bytes_sum    =("flow_bytes_sum",       "sum"),
        flow_packets_sum  =("flow_packets_sum",     "sum"),
    ).reset_index()

    master = build_grid(master_agg)
    col_order = ["time_window","total_flows","attack_flows","benign_flows",
                 "flow_duration_mean","flow_bytes_sum","flow_packets_sum","attack_rate","observed"]
    master = master[col_order].sort_values("time_window").reset_index(drop=True)
    master.to_csv(MASTER_CSV, index=False)

    total_flows  = int(master["total_flows"].sum())
    attack_flows = int(master["attack_flows"].sum())
    benign_flows = int(master["benign_flows"].sum())

    print(f"  Files processed : {len(KAGGLE_FILES)}")
    print(f"  Total windows   : {len(master):,}")
    print(f"  Observed windows: {int(master['observed'].sum()):,}")
    print(f"  Total flows     : {total_flows:,}")
    print(f"  Attack flows    : {attack_flows:,}")
    print(f"  Benign flows    : {benign_flows:,}")
    print(f"  Attack ratio    : {attack_flows/total_flows:.6f}" if total_flows > 0 else "  Attack ratio    : N/A")
    print(f"  Date range      : {master['time_window'].min()} → {master['time_window'].max()}")
    print(f"  Master saved    : {MASTER_CSV}")

    manifest = {
        "dataset": "cic_apt_iiot_2024", "freq": FREQ,
        "total_windows": len(master), "observed_windows": int(master["observed"].sum()),
        "total_flows": total_flows, "attack_flows": attack_flows, "benign_flows": benign_flows,
        "attack_ratio": attack_flows/total_flows if total_flows > 0 else 0.0,
        "date_min": str(master["time_window"].min()), "date_max": str(master["time_window"].max()),
        "files_processed": len(KAGGLE_FILES), "files": file_metas,
    }
    with open(MANIFEST_JSON, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest saved  : {MANIFEST_JSON}")

    if not args.skip_upload:
        print("\nSyncing to S3...")
        s3 = boto3.client("s3")
        s3.upload_file(str(MASTER_CSV),    S3_BUCKET, f"{S3_OUT}cic_apt_iiot_2024_continuous_1min_master.csv")
        s3.upload_file(str(MANIFEST_JSON), S3_BUCKET, f"{S3_MANIFEST}cic_apt_iiot_2024_manifest.json")
        print("  ✅ S3 sync complete")

    print("\n✅ Phase 1 complete.")

if __name__ == "__main__":
    main()
