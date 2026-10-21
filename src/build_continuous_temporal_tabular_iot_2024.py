"""
Phase 1 — CIC-BCCC-NRC TabularIoTAttack-2024
Chunked streaming (200k rows/chunk) for large files.
Outputs per-file CSVs + master continuous temporal grid.
"""

import boto3, io, json, gc
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timezone

# ── Config ────────────────────────────────────────────────────────────────────
BUCKET      = "aegis-cic-training-2026-model.v1"
S3_PREFIX   = "datasets/tabular-iot-attack-2024/raw/"
OUT_DIR     = Path("data/processed/cic-bccc-tabular-iot-2024")
MASTER_OUT  = Path("data/processed/cic_bccc_tabular_iot_2024_continuous_1min_master.csv")
MANIFEST    = Path("data/manifests/cic_bccc_tabular_iot_2024_manifest.json")
S3_OUT_PFX  = "tabular-iot-attack-2024/processed/"
S3_MAN_PFX  = "tabular-iot-attack-2024/manifests/"
CHUNK_SIZE  = 200_000
FREQ        = "1min"

TIMESTAMP_COL = "Timestamp"
LABEL_COL     = "Label"
DURATION_COL  = "Flow Duration"
FWD_BYTES     = "Total Length of Fwd Packet"
BWD_BYTES     = "Total Length of Bwd Packet"
FWD_PKTS      = "Total Fwd Packet"
BWD_PKTS      = "Total Bwd packets"

OUT_COLS = [
    "time_window","total_flows","attack_flows","benign_flows",
    "flow_duration_mean","flow_bytes_sum","flow_packets_sum",
    "attack_rate","observed"
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def floor_minute(ts: pd.Series) -> pd.Series:
    return ts.dt.floor(FREQ)

def aggregate_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.copy()
    chunk["ts_parsed"] = pd.to_datetime(
        chunk[TIMESTAMP_COL], format="mixed", dayfirst=False, errors="coerce"
    )
    chunk.dropna(subset=["ts_parsed"], inplace=True)
    chunk["time_window"] = floor_minute(chunk["ts_parsed"])
    chunk["label"]       = pd.to_numeric(chunk[LABEL_COL], errors="coerce").fillna(0).astype(int)
    chunk["duration"]    = pd.to_numeric(chunk[DURATION_COL], errors="coerce").fillna(0.0)
    chunk["bytes"]       = (
        pd.to_numeric(chunk[FWD_BYTES], errors="coerce").fillna(0.0) +
        pd.to_numeric(chunk[BWD_BYTES], errors="coerce").fillna(0.0)
    )
    chunk["packets"]     = (
        pd.to_numeric(chunk[FWD_PKTS], errors="coerce").fillna(0.0) +
        pd.to_numeric(chunk[BWD_PKTS], errors="coerce").fillna(0.0)
    )

    grp = chunk.groupby("time_window").agg(
        total_flows       = ("label", "count"),
        attack_flows      = ("label", "sum"),
        flow_duration_sum = ("duration", "sum"),
        flow_bytes_sum    = ("bytes", "sum"),
        flow_packets_sum  = ("packets", "sum"),
    ).reset_index()
    grp["benign_flows"] = grp["total_flows"] - grp["attack_flows"]
    return grp

def merge_buckets(acc: dict, grp: pd.DataFrame):
    for _, row in grp.iterrows():
        tw = row["time_window"]
        if tw not in acc:
            acc[tw] = {
                "total_flows": 0, "attack_flows": 0, "benign_flows": 0,
                "flow_duration_sum": 0.0, "flow_bytes_sum": 0.0, "flow_packets_sum": 0.0
            }
        acc[tw]["total_flows"]        += row["total_flows"]
        acc[tw]["attack_flows"]       += row["attack_flows"]
        acc[tw]["benign_flows"]       += row["benign_flows"]
        acc[tw]["flow_duration_sum"]  += row["flow_duration_sum"]
        acc[tw]["flow_bytes_sum"]     += row["flow_bytes_sum"]
        acc[tw]["flow_packets_sum"]   += row["flow_packets_sum"]

def buckets_to_df(acc: dict) -> pd.DataFrame:
    rows = []
    for tw, v in sorted(acc.items()):
        tf = v["total_flows"]
        rows.append({
            "time_window":       tw,
            "total_flows":       tf,
            "attack_flows":      v["attack_flows"],
            "benign_flows":      v["benign_flows"],
            "flow_duration_mean": v["flow_duration_sum"] / tf if tf > 0 else 0.0,
            "flow_bytes_sum":    v["flow_bytes_sum"],
            "flow_packets_sum":  v["flow_packets_sum"],
            "attack_rate":       v["attack_flows"] / tf if tf > 0 else 0.0,
            "observed":          1
        })
    return pd.DataFrame(rows)

def make_continuous(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    full_idx = pd.date_range(df["time_window"].min(), df["time_window"].max(), freq=FREQ)
    df = df.set_index("time_window").reindex(full_idx).reset_index()
    df.rename(columns={"index": "time_window"}, inplace=True)
    df["observed"] = df["observed"].fillna(0).astype(int)
    num_cols = ["total_flows","attack_flows","benign_flows",
                "flow_duration_mean","flow_bytes_sum","flow_packets_sum","attack_rate"]
    df[num_cols] = df[num_cols].fillna(0.0)
    return df[OUT_COLS]

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    s3     = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    pages  = paginator.paginate(Bucket=BUCKET, Prefix=S3_PREFIX)

    files  = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".csv"):
                files.append((key, obj["Size"]))

    files.sort(key=lambda x: x[1])   # smallest first
    print(f"Found {len(files)} CSV files in S3")

    master_buckets: dict = {}
    manifest_files = []
    total_flows_all = 0
    total_attacks_all = 0

    for key, size in files:
        fname = key.split("/")[-1]
        print(f"\n── {fname} ({size/1e6:.1f} MB) ──")

        obj      = s3.get_object(Bucket=BUCKET, Key=key)
        body     = obj["Body"]
        buckets  = {}
        chunk_n  = 0
        rows_read = 0

        # stream in chunks
        reader = pd.read_csv(
            io.BytesIO(body.read()),
            chunksize=CHUNK_SIZE,
            low_memory=False,
            on_bad_lines="skip"
        )

        for chunk in reader:
            chunk_n  += 1
            rows_read += len(chunk)
            grp = aggregate_chunk(chunk)
            merge_buckets(buckets, grp)
            if chunk_n % 5 == 0:
                print(f"  chunk {chunk_n} — {rows_read:,} rows processed")
            del chunk, grp
            gc.collect()

        print(f"  Total rows : {rows_read:,}")

        # per-file output
        df_file = buckets_to_df(buckets)
        df_file = make_continuous(df_file)
        af = int(df_file["attack_flows"].sum())
        tf = int(df_file["total_flows"].sum())
        print(f"  Windows    : {len(df_file):,} / observed: {df_file['observed'].sum():,}")
        print(f"  Flows      : {tf:,} / attacks: {af:,}")

        out_path = OUT_DIR / fname.replace(" ", "_").replace(".csv", "_1min.csv")
        df_file.to_csv(out_path, index=False)
        print(f"  Saved      : {out_path}")

        manifest_files.append({
            "file": fname, "s3_key": key, "size_bytes": size,
            "rows": rows_read, "windows": len(df_file),
            "observed": int(df_file["observed"].sum()),
            "total_flows": tf, "attack_flows": af
        })
        total_flows_all   += tf
        total_attacks_all += af

        # merge into master — direct dict merge
        for tw, v in buckets.items():
            if tw not in master_buckets:
                master_buckets[tw] = {
                    "total_flows": 0, "attack_flows": 0, "benign_flows": 0,
                    "flow_duration_sum": 0.0, "flow_bytes_sum": 0.0, "flow_packets_sum": 0.0
                }
            master_buckets[tw]["total_flows"]       += v["total_flows"]
            master_buckets[tw]["attack_flows"]      += v["attack_flows"]
            master_buckets[tw]["benign_flows"]      += v["benign_flows"]
            master_buckets[tw]["flow_duration_sum"] += v["flow_duration_sum"]
            master_buckets[tw]["flow_bytes_sum"]    += v["flow_bytes_sum"]
            master_buckets[tw]["flow_packets_sum"]  += v["flow_packets_sum"]

        del df_file, buckets
        gc.collect()

    # ── Master ────────────────────────────────────────────────────────────────
    print("\n── Building master continuous grid ──")
    master = buckets_to_df(master_buckets)
    master = make_continuous(master)
    master.to_csv(MASTER_OUT, index=False)
    print(f"  Total windows   : {len(master):,}")
    print(f"  Observed windows: {master['observed'].sum():,}")
    print(f"  Date range      : {master['time_window'].min()} → {master['time_window'].max()}")
    print(f"  Total flows     : {total_flows_all:,}")
    print(f"  Attack flows    : {total_attacks_all:,}")
    attack_ratio = total_attacks_all / total_flows_all if total_flows_all > 0 else 0
    print(f"  Attack ratio    : {attack_ratio:.6f}")
    print(f"  Master saved    : {MASTER_OUT}")

    # ── Manifest ──────────────────────────────────────────────────────────────
    manifest = {
        "dataset": "CIC-BCCC-NRC TabularIoTAttack-2024",
        "files_processed": len(files),
        "files": manifest_files,
        "total_flows": total_flows_all,
        "attack_flows": total_attacks_all,
        "attack_ratio": attack_ratio,
        "master_output": str(MASTER_OUT)
    }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest saved  : {MANIFEST}")

    # ── S3 sync ───────────────────────────────────────────────────────────────
    print("\nSyncing to S3...")
    import subprocess
    subprocess.run([
        "aws","s3","sync", str(OUT_DIR),
        f"s3://{BUCKET}/{S3_OUT_PFX}", "--quiet"
    ], check=True)
    subprocess.run([
        "aws","s3","cp", str(MANIFEST),
        f"s3://{BUCKET}/{S3_MAN_PFX}cic_bccc_tabular_iot_2024_manifest.json", "--quiet"
    ], check=True)
    print("  ✅ S3 sync complete")
    print("\n✅ Phase 1 complete.")

if __name__ == "__main__":
    main()
