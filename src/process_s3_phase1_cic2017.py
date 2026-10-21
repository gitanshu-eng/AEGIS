import io
from pathlib import Path
import boto3
import numpy as np
import pandas as pd
from src.adapters.cic_ids2017 import CICIDS2017Adapter

BUCKET = "aegis-cic-training-2026-model.v1"
RAW_PREFIX = "datasets/cic-ids2017/raw/"
OUTPUT_DIR = Path("data/processed/cic-ids2017")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 100_000

s3 = boto3.client("s3")
adapter = CICIDS2017Adapter()


def get_s3_files():
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=RAW_PREFIX)
    files = [
        obj for obj in response.get("Contents", [])
        if obj["Key"].lower().endswith(".csv")
    ]
    return sorted(files, key=lambda x: x["Key"])


def aggregate_chunk(df_chunk, adapter):
    cleaned_df, _, _ = adapter.clean_raw(df_chunk)
    if cleaned_df.empty:
        return None
    norm_df = adapter.normalize(cleaned_df)
    if norm_df.empty:
        return None

    norm_df["time_window"] = norm_df["timestamp"].dt.floor("1min")
    norm_df["is_attack"] = norm_df["label"].apply(adapter.is_attack).astype(int)
    norm_df["is_benign"] = 1 - norm_df["is_attack"]

    grouped = norm_df.groupby("time_window").agg(
        attack_flows=("is_attack", "sum"),
        benign_flows=("is_benign", "sum"),
        total_flows=("label", "count"),
        flow_duration_sum=("flow_duration", "sum"),
        flow_bytes_sum=("flow_bytes", "sum"),
        flow_packets_sum=("flow_packets", "sum"),
    ).reset_index()

    return grouped


def process_s3_file(key):
    filename = Path(key).name
    stem = Path(key).stem
    out_path = OUTPUT_DIR / f"{stem}_continuous_1min.csv"

    print(f"\n[Processing] {filename}")
    s3_path = f"s3://{BUCKET}/{key}"

    chunk_aggs = []
    chunk_iter = pd.read_csv(s3_path, chunksize=CHUNK_SIZE, low_memory=False, encoding="cp1252")

    for i, chunk in enumerate(chunk_iter):
        agg = aggregate_chunk(chunk, adapter)
        if agg is not None and not agg.empty:
            chunk_aggs.append(agg)
        if (i + 1) % 5 == 0:
            print(f"  Processed { (i + 1) * CHUNK_SIZE :,} rows...")

    if not chunk_aggs:
        print(f"  [Warning] No valid data extracted for {filename}")
        return

    # Combine partial chunk aggregates
    full_agg = pd.concat(chunk_aggs, ignore_index=True)
    day_temporal = full_agg.groupby("time_window").agg(
        attack_flows=("attack_flows", "sum"),
        benign_flows=("benign_flows", "sum"),
        total_flows=("total_flows", "sum"),
        flow_duration_sum=("flow_duration_sum", "sum"),
        flow_bytes_sum=("flow_bytes_sum", "sum"),
        flow_packets_sum=("flow_packets_sum", "sum"),
    ).reset_index()

    # Derived mean flow duration
    day_temporal["flow_duration_mean"] = (
        day_temporal["flow_duration_sum"] / day_temporal["total_flows"]
    ).fillna(0.0)
    day_temporal.drop(columns=["flow_duration_sum"], inplace=True)

    # Build continuous 1-minute timeline
    start_time = day_temporal["time_window"].min()
    end_time = day_temporal["time_window"].max()

    timeline = pd.DataFrame(
        {"time_window": pd.date_range(start=start_time, end=end_time, freq="1min")}
    )

    continuous = timeline.merge(day_temporal, on="time_window", how="left")
    continuous["observed"] = continuous["total_flows"].notna().astype(int)

    # Fill missing temporal slots
    continuous["attack_flows"] = continuous["attack_flows"].fillna(0).astype(int)
    continuous["benign_flows"] = continuous["benign_flows"].fillna(0).astype(int)
    continuous["total_flows"] = continuous["total_flows"].fillna(0).astype(int)
    continuous["flow_duration_mean"] = continuous["flow_duration_mean"].fillna(0.0)
    continuous["flow_bytes_sum"] = continuous["flow_bytes_sum"].fillna(0.0)
    continuous["flow_packets_sum"] = continuous["flow_packets_sum"].fillna(0.0)

    continuous.to_csv(out_path, index=False)
    print(f"  [Saved] {out_path} ({len(continuous)} 1-min windows)")


if __name__ == "__main__":
    files = get_s3_files()
    print(f"Found {len(files)} files to process in S3:")
    for f in files:
        print(" -", f["Key"])

    for obj in files:
        process_s3_file(obj["Key"])

    print("\nPhase 1 processing complete.")
