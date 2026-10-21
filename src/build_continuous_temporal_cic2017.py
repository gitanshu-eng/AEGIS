import json
from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed/cic-ids2017")
OUTPUT_FILE = PROCESSED_DIR / "cic_ids2017_continuous_1min_master.csv"
MANIFEST_FILE = Path("data/manifests/cic_ids2017_manifest.json")
MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)

files = sorted(PROCESSED_DIR.glob("*_continuous_1min.csv"))
# Filter out any prior master files
day_files = [f for f in files if "master" not in f.name]

dfs = []
file_summaries = {}

total_flows = 0
total_attacks = 0
total_benign = 0

for f in day_files:
    df = pd.read_csv(f)
    df["time_window"] = pd.to_datetime(df["time_window"])
    dfs.append(df)
    
    file_summaries[f.name] = {
        "start_window": str(df["time_window"].min()),
        "end_window": str(df["time_window"].max()),
        "total_windows": len(df),
        "observed_windows": int(df["observed"].sum()),
        "attack_flows": int(df["attack_flows"].sum()),
        "benign_flows": int(df["benign_flows"].sum()),
    }
    total_flows += int(df["total_flows"].sum())
    total_attacks += int(df["attack_flows"].sum())
    total_benign += int(df["benign_flows"].sum())

master_df = pd.concat(dfs, ignore_index=True)
master_df = master_df.sort_values("time_window").reset_index(drop=True)

# Save master continuous dataset
master_df.to_csv(OUTPUT_FILE, index=False)

# Build manifest
manifest = {
    "dataset_name": "CIC-IDS2017",
    "temporal_resolution": "1min",
    "total_windows": len(master_df),
    "total_flows": total_flows,
    "total_attack_flows": total_attacks,
    "total_benign_flows": total_benign,
    "attack_ratio": round(total_attacks / total_flows, 6) if total_flows else 0,
    "time_range": {
        "start": str(master_df["time_window"].min()),
        "end": str(master_df["time_window"].max())
    },
    "canonical_columns": master_df.columns.tolist(),
    "files": file_summaries
}

with open(MANIFEST_FILE, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Master file saved: {OUTPUT_FILE} ({len(master_df)} rows)")
print(f"Manifest written: {MANIFEST_FILE}")
print(json.dumps(manifest, indent=2))
