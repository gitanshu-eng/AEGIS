"""
AEGIS — 4.4 Lead/Lag FULL AUDIT (all episodes, all datasets)
==============================================================

WHY THIS SCRIPT EXISTS
------------------------
test_critical_lead_lag_v3.py validated the corrected (gap-safe,
min_periods=W, no forward-max-on-current-behavior) lead/lag logic
against exactly 2 named flagship CRITICAL episodes. Both came back
SIMULTANEOUS — a genuine finding (confirmed via the
breach-position-in-segment diagnostic: 51 and 38 valid history rows
preceded each breach, ruling out a warm-up artifact).

But 2 episodes is not evidence about AEGIS's early-warning behavior
in general. Phase 2's own operational audit reports a 3.0-minute
MEDIAN lead time across 59 episodes — meaning the two SIMULTANEOUS
findings could be the norm, or could be atypical outliers. This
script runs the same corrected logic across EVERY episode in EVERY
dataset's outputs/phase4_investigations/{dataset}_episodes.json, and
reports the full distribution of classifications and lead times.

This reuses the exact same corrected functions as
test_critical_lead_lag_v3.py (assign_segment_ids, compute_physical_breach,
calculate_lead_lag core logic) — no new ground-truth computation
methodology is introduced here.

WHAT THIS SCRIPT DOES NOT DO
------------------------------
It does not modify any Phase 1-4 output. It only reads existing
episode JSONs, incident JSONs, and Phase 1 continuous CSVs, and
writes its own diagnostic report files.

OUTPUT
------
outputs/lead_lag_audit/lead_lag_full_audit_detail.csv
    One row per episode: dataset, episode_id, bounds, f_time, b_time,
    classification, lead_time_minutes.

outputs/lead_lag_audit/lead_lag_full_audit_report.md
    Distribution summary: count per classification, lead-time stats
    for LEADING episodes, per-dataset breakdown.
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

EPISODE_DIR = Path("outputs/phase4_investigations")
INCIDENT_DIR = Path("outputs/incident_records")
PHASE1_DIR = Path("data/processed")
OUTPUT_DIR = Path("outputs/lead_lag_audit")

DETAIL_CSV_PATH = OUTPUT_DIR / "lead_lag_full_audit_detail.csv"
REPORT_MD_PATH = OUTPUT_DIR / "lead_lag_full_audit_report.md"

DATASET_NAMES = [
    "Friday-02-03-2018",
    "Friday-16-02-2018",
    "Friday-23-02-2018",
    "Thuesday-20-02-2018",
    "Thursday-01-03-2018",
    "Thursday-15-02-2018",
    "Thursday-22-02-2018",
    "Wednesday-14-02-2018",
    "Wednesday-21-02-2018",
    "Wednesday-28-02-2018",
]

W = 10
H = 5
TAU = 0.10
F_THRESHOLD = 0.50

pd.set_option("display.width", 140)


def parse_time(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


def assign_segment_ids(df):
    """Derive segment_id from time continuity within observed==1 rows.
    Any gap > 1 minute between consecutive observed rows starts a new
    segment. (Identical logic to target_feasibility_analysis.py and
    test_critical_lead_lag_v3.py.)
    """
    time_diff_minutes = df["time_window"].diff().dt.total_seconds().div(60)
    is_new_segment = (time_diff_minutes.isna()) | (time_diff_minutes > 1)
    df = df.copy()
    df["segment_id"] = is_new_segment.cumsum().astype(int)
    return df


def _load_and_segment(dataset_name):
    file_path = PHASE1_DIR / f"{dataset_name}_temporal_continuous.csv"
    if not file_path.exists():
        return None

    df = pd.read_csv(file_path)
    df["time_window"] = pd.to_datetime(df["time_window"], errors="coerce")
    df = df.sort_values("time_window").reset_index(drop=True)

    df = df[df["observed"] == 1].reset_index(drop=True)
    df = df.dropna(subset=["attack_rate"]).reset_index(drop=True)

    df = assign_segment_ids(df)
    return df


def compute_physical_breach(dataset_name):
    """Realized-event detector: first minute attack_rate ITSELF exceeds
    baseline_W(t) + tau. Segment-safe, min_periods=W (not 1), computed
    on the FULL per-segment series. Identical logic to
    test_critical_lead_lag_v3.py.
    """
    combined = _load_and_segment(dataset_name)
    if combined is None:
        return None

    pieces = []
    for segment_id, group in combined.groupby("segment_id", sort=False):
        group = group.reset_index(drop=True)
        series = group["attack_rate"]

        baseline = series.rolling(window=W, min_periods=W).mean()

        piece = group[["time_window", "attack_rate", "segment_id"]].copy()
        piece["baseline"] = baseline.to_numpy()
        pieces.append(piece)

    result = pd.concat(pieces, ignore_index=True)
    result["valid"] = result["baseline"].notna()
    result["physical_breach"] = result["valid"] & (
        result["attack_rate"] > (result["baseline"] + TAU)
    )
    return result


def calculate_lead_lag(ep_start, ep_end, dataset_incidents, physical_breach_df):
    st = parse_time(ep_start)
    et = parse_time(ep_end)

    f_time = None
    episode_incidents = [
        inc for inc in dataset_incidents
        if st <= parse_time(inc["timestamp"]) <= et
    ]
    for inc in sorted(episode_incidents, key=lambda x: x["timestamp"]):
        if inc["risk_signals"]["forecast"] >= F_THRESHOLD:
            f_time = parse_time(inc["timestamp"])
            break

    b_time = None
    b_note = None
    if physical_breach_df is not None:
        ep_df = physical_breach_df[
            (physical_breach_df["time_window"] >= st)
            & (physical_breach_df["time_window"] <= et)
        ]
        breach_events = ep_df[ep_df["physical_breach"]]
        if not breach_events.empty:
            b_time = breach_events.iloc[0]["time_window"].to_pydatetime()
        else:
            n_valid = int(ep_df["valid"].sum())
            b_note = (
                "NO_VALID_BASELINE_ROWS_IN_EPISODE_WINDOW"
                if n_valid == 0
                else f"NO_PHYSICAL_BREACH_IN_{n_valid}_VALID_ROWS"
            )

    if f_time and b_time:
        lead_time = int((b_time - f_time).total_seconds() / 60)
        if lead_time > 0:
            classification = "LEADING"
        elif lead_time < 0:
            classification = "LAGGING"
        else:
            classification = "SIMULTANEOUS"
    elif f_time and not b_time:
        classification = "F_ONLY_NO_PHYSICAL_BREACH"
        lead_time = None
    elif b_time and not f_time:
        classification = "BREACH_ONLY_NO_FORECAST"
        lead_time = None
    else:
        classification = "INDETERMINATE"
        lead_time = None

    return {
        "classification": classification,
        "first_forecast_elevation": str(f_time) if f_time else None,
        "first_physical_breach": str(b_time) if b_time else None,
        "note": b_note,
        "lead_time_minutes": lead_time,
    }


def run_full_audit():
    rows = []

    for dataset_name in DATASET_NAMES:
        ep_file = EPISODE_DIR / f"{dataset_name}_episodes.json"
        inc_file = INCIDENT_DIR / f"{dataset_name}_incidents.json"

        if not ep_file.exists() or not inc_file.exists():
            print(f"[WARN] Missing episode or incident file for {dataset_name}, skipping.")
            continue

        with open(ep_file, "r") as f:
            episodes = json.load(f)
        with open(inc_file, "r") as f:
            incidents = json.load(f)

        physical_breach_df = compute_physical_breach(dataset_name)
        if physical_breach_df is None:
            print(f"[WARN] No Phase 1 continuous file for {dataset_name}, "
                  f"skipping its {len(episodes)} episode(s).")
            continue

        print(f"Processing {dataset_name}: {len(episodes)} episode(s)...")

        for ep in episodes:
            result = calculate_lead_lag(
                ep["temporal_bounds"]["start_time"],
                ep["temporal_bounds"]["end_time"],
                incidents,
                physical_breach_df,
            )
            rows.append({
                "dataset": dataset_name,
                "episode_id": ep.get("episode_id"),
                "start_time": ep["temporal_bounds"]["start_time"],
                "end_time": ep["temporal_bounds"]["end_time"],
                **result,
            })

    return pd.DataFrame(rows)


def write_report(detail_df):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail_df.to_csv(DETAIL_CSV_PATH, index=False)

    lines = []
    lines.append("# AEGIS — 4.4 Lead/Lag Full Audit")
    lines.append("")
    lines.append(
        "Every episode across all datasets, evaluated with the "
        "corrected (gap-safe, min_periods=W, realized-event) lead/lag "
        "logic — not just the 2 flagship CRITICAL episodes previously "
        "spot-checked."
    )
    lines.append("")
    lines.append(f"Total episodes evaluated: {len(detail_df)}")
    lines.append("")

    lines.append("## Classification distribution")
    lines.append("")
    counts = detail_df["classification"].value_counts()
    lines.append("```")
    lines.append(counts.to_string())
    lines.append("```")
    lines.append("")

    leading = detail_df[detail_df["classification"] == "LEADING"]
    if len(leading) > 0:
        lines.append("## Lead-time statistics (LEADING episodes only)")
        lines.append("")
        lines.append(f"N = {len(leading)}")
        lines.append(f"Mean lead time:   {leading['lead_time_minutes'].mean():.2f} min")
        lines.append(f"Median lead time: {leading['lead_time_minutes'].median():.2f} min")
        lines.append(f"Max lead time:    {leading['lead_time_minutes'].max():.0f} min")
        lines.append("")

    simultaneous = detail_df[detail_df["classification"] == "SIMULTANEOUS"]
    lines.append("## Simultaneous-onset episodes")
    lines.append("")
    lines.append(
        f"{len(simultaneous)} / {len(detail_df)} episodes showed zero lead "
        f"time — forecast and physical breach crossed threshold in the "
        f"same 1-minute window."
    )
    lines.append("")

    lagging = detail_df[detail_df["classification"] == "LAGGING"]
    if len(lagging) > 0:
        lines.append(
            f"**{len(lagging)} episode(s) classified LAGGING** — the "
            f"physical breach preceded the forecast crossing 0.50. "
            f"These deserve individual review; a lagging classification "
            f"on a CRITICAL-adjacent episode would mean AEGIS confirmed "
            f"escalation only after it was already underway."
        )
        lines.append("")

    lines.append("## Per-dataset breakdown")
    lines.append("")
    lines.append("```")
    pivot = detail_df.groupby(["dataset", "classification"]).size().unstack(fill_value=0)
    lines.append(pivot.to_string())
    lines.append("```")
    lines.append("")

    other = detail_df[~detail_df["classification"].isin(
        ["LEADING", "LAGGING", "SIMULTANEOUS"]
    )]
    if len(other) > 0:
        lines.append("## Episodes with no clean comparison")
        lines.append("")
        lines.append(
            f"{len(other)} episode(s) had no forecast crossing 0.50, no "
            f"physical breach, or no valid baseline history at all within "
            f"the episode window. See the detail CSV's `note` column for "
            f"specifics on each."
        )
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDetail CSV written to: {DETAIL_CSV_PATH}")
    print(f"Report written to:     {REPORT_MD_PATH}")


def main():
    print("=================================================================")
    print("      4.4 LEAD/LAG FULL AUDIT — ALL EPISODES, ALL DATASETS")
    print("=================================================================")
    print(f"Ground truth: physical breach, W={W}, tau={TAU} (segment-safe, min_periods=W)")
    print(f"Forecast threshold: F >= {F_THRESHOLD}")
    print()

    detail_df = run_full_audit()

    if len(detail_df) == 0:
        print("\n[ERROR] No episodes could be processed. Check that "
              f"{EPISODE_DIR}, {INCIDENT_DIR}, and {PHASE1_DIR} exist "
              "and contain the expected files.")
        return

    print("\n--- CLASSIFICATION DISTRIBUTION ---")
    print(detail_df["classification"].value_counts().to_string())

    leading = detail_df[detail_df["classification"] == "LEADING"]
    if len(leading) > 0:
        print(f"\nLEADING episodes: N={len(leading)}, "
              f"mean={leading['lead_time_minutes'].mean():.2f} min, "
              f"median={leading['lead_time_minutes'].median():.2f} min")

    write_report(detail_df)


if __name__ == "__main__":
    main()
