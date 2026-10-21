"""
AEGIS -- Cross-check: engine-embedded forecast_behavior vs. independent audit
==============================================================================

Compares the forecast_behavior field already embedded in each of the 24
*_episodes.json files against the results produced by lead_lag_full_audit.py.
If both scripts computed the same thing, every episode's classification and
lead_time_minutes must match exactly. Any disagreement is printed explicitly.

REQUIRES
--------
outputs/lead_lag_audit/lead_lag_full_audit_detail.csv
    (produced by running lead_lag_full_audit.py)
outputs/phase4_investigations/{dataset}_episodes.json
    (produced by phase4_investigation_engine.py)
"""

import json
import glob
from pathlib import Path

import pandas as pd

AUDIT_CSV = Path("outputs/lead_lag_audit/lead_lag_full_audit_detail.csv")
EPISODE_DIR = Path("outputs/phase4_investigations")


def load_engine_forecast_behavior():
    rows = []
    for file in sorted(glob.glob(str(EPISODE_DIR / "*_episodes.json"))):
        dataset = Path(file).name.replace("_episodes.json", "")
        with open(file, "r") as f:
            episodes = json.load(f)
        for ep in episodes:
            fb = ep.get("forecast_behavior", {})
            rows.append({
                "dataset": dataset,
                "episode_id": ep["episode_id"],
                "start_time": ep["temporal_bounds"]["start_time"],
                "end_time": ep["temporal_bounds"]["end_time"],
                "engine_classification": fb.get("classification"),
                "engine_lead_time_minutes": fb.get("lead_time_minutes"),
                "engine_f_time": fb.get("f_time"),
                "engine_b_time": fb.get("b_time"),
            })
    return pd.DataFrame(rows)


def main():
    if not AUDIT_CSV.exists():
        print(f"[ERROR] {AUDIT_CSV} not found. Run lead_lag_full_audit.py first.")
        return

    audit_df = pd.read_csv(AUDIT_CSV)
    engine_df = load_engine_forecast_behavior()

    print(f"Independent audit episodes: {len(audit_df)}")
    print(f"Engine-embedded episodes:   {len(engine_df)}")

    merged = pd.merge(
        audit_df[[
            "dataset", "start_time", "end_time",
            "classification", "lead_time_minutes",
            "first_forecast_elevation", "first_physical_breach"
        ]],
        engine_df[[
            "dataset", "start_time", "end_time",
            "engine_classification", "engine_lead_time_minutes",
            "engine_f_time", "engine_b_time"
        ]],
        on=["dataset", "start_time", "end_time"],
        how="outer",
        indicator=True,
    )

    unmatched = merged[merged["_merge"] != "both"]
    if len(unmatched) > 0:
        print(f"\n[WARN] {len(unmatched)} episode(s) could not be matched "
              f"by (dataset, start_time, end_time):")
        print(unmatched[["dataset", "start_time", "end_time", "_merge"]].to_string(index=False))

    matched = merged[merged["_merge"] == "both"].copy()

    matched["classification_match"] = (
        matched["classification"] == matched["engine_classification"]
    )
    matched["lead_time_match"] = (
        matched["lead_time_minutes"] == matched["engine_lead_time_minutes"]
    ) | (
        matched["lead_time_minutes"].isna() & matched["engine_lead_time_minutes"].isna()
    )

    n_class_mismatch = int((~matched["classification_match"]).sum())
    n_lt_mismatch = int((~matched["lead_time_match"]).sum())

    print(f"\nMatched episodes compared: {len(matched)}")
    print(f"Classification mismatches: {n_class_mismatch}")
    print(f"Lead-time mismatches:      {n_lt_mismatch}")

    if n_class_mismatch == 0 and n_lt_mismatch == 0 and len(unmatched) == 0:
        print("\n[CONFIRMED] Engine-embedded forecast_behavior EXACTLY matches "
              "the independent lead_lag_full_audit.py results for all "
              "episodes. The engine lead/lag logic is trustworthy.")
    else:
        print("\n[ATTENTION] Disagreement found. Do not assume either side "
              "is correct. Inspect the rows below.")
        bad = matched[~matched["classification_match"] | ~matched["lead_time_match"]]
        print(bad[[
            "dataset", "start_time", "end_time",
            "classification", "engine_classification",
            "lead_time_minutes", "engine_lead_time_minutes",
            "first_forecast_elevation", "engine_f_time",
            "first_physical_breach", "engine_b_time",
        ]].to_string(index=False))


if __name__ == "__main__":
    main()
