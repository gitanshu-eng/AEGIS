"""
AEGIS — 4.4 Lead/Lag FULL AUDIT — V2: PADDED WINDOW
=====================================================

WHY THIS VERSION EXISTS
------------------------
The strict-bounds full audit (lead_lag_full_audit.py) found only 1/24
episodes (4.2%) showing genuine multi-minute LEADING lead time, with
8/24 (33%) landing in an ambiguous no-clean-signal bucket
(INDETERMINATE / F_ONLY_NO_PHYSICAL_BREACH / BREACH_ONLY_NO_FORECAST).

A real methodological gap can explain part of that: an episode's
start_time is triggered by risk_score >= 30, where
risk = 0.35F + 0.35A + 0.15D + 0.15P. F alone crossing 0.50 does NOT
by itself guarantee risk_score >= 30 (that also depends on A/D/P at
that same minute) — so F could genuinely have crossed 0.50 BEFORE the
episode's own recorded start_time, and the strict-bounds search would
never see it, silently underCounting real lead time.

THE FIX — SYMMETRIC, NOT ONE-SIDED
-------------------------------------
This script searches BOTH first_forecast_elevation (F) AND
first_physical_breach (the realized event) in a window starting
W = 10 minutes (Phase 2's own frozen baseline window — not a new,
invented number) before episode start, through episode end.

Padding is applied to BOTH signals symmetrically, not just F. Padding
only F would bias the result toward finding more LEADING episodes,
which would be the same "tune until the metric looks good" pattern
this project has explicitly tried to avoid throughout. If a physical
breach genuinely happened just before the episode's recorded start
too, that is equally real information and must be visible on both
sides of the comparison.

CROSS-EPISODE CONTAMINATION GUARD
------------------------------------
Padding backward risks attributing a PREVIOUS episode's own breach or
forecast crossing to the current episode. To prevent this, the padded
start is capped at max(episode_start - W minutes, previous_episode_end
+ 1 minute) for episodes after the first one in a dataset. The very
first episode in a dataset pads the full W minutes (or less, if it
would go before the data itself begins — compute_physical_breach's
own `valid` column already handles that boundary correctly since a
baseline can't exist before W history points).

WHAT THIS SCRIPT REPORTS
---------------------------
Both the STRICT (original, unpadded) and PADDED classification for
every episode, side by side — never replacing one with the other —
so the padding's actual effect is visible and auditable, not just
asserted.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

EPISODE_DIR = Path("outputs/phase4_investigations")
INCIDENT_DIR = Path("outputs/incident_records")
PHASE1_DIR = Path("data/processed")
OUTPUT_DIR = Path("outputs/lead_lag_audit")

DETAIL_CSV_PATH = OUTPUT_DIR / "lead_lag_padded_audit_detail.csv"
REPORT_MD_PATH = OUTPUT_DIR / "lead_lag_padded_audit_report.md"

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
TAU = 0.10
F_THRESHOLD = 0.50
PAD_MINUTES = W  # deliberately reuse Phase 2's own frozen W, not a new number

pd.set_option("display.width", 140)


def parse_time(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


def assign_segment_ids(df):
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


def find_first_forecast(st, et, dataset_incidents):
    episode_incidents = [
        inc for inc in dataset_incidents
        if st <= parse_time(inc["timestamp"]) <= et
    ]
    for inc in sorted(episode_incidents, key=lambda x: x["timestamp"]):
        if inc["risk_signals"]["forecast"] >= F_THRESHOLD:
            return parse_time(inc["timestamp"])
    return None


def find_first_breach(st, et, physical_breach_df):
    if physical_breach_df is None:
        return None, None
    ep_df = physical_breach_df[
        (physical_breach_df["time_window"] >= st)
        & (physical_breach_df["time_window"] <= et)
    ]
    breach_events = ep_df[ep_df["physical_breach"]]
    if not breach_events.empty:
        return breach_events.iloc[0]["time_window"].to_pydatetime(), None
    n_valid = int(ep_df["valid"].sum())
    note = (
        "NO_VALID_BASELINE_ROWS" if n_valid == 0
        else f"NO_BREACH_IN_{n_valid}_VALID_ROWS"
    )
    return None, note


def classify(f_time, b_time):
    if f_time and b_time:
        lead_time = int((b_time - f_time).total_seconds() / 60)
        if lead_time > 0:
            return "LEADING", lead_time
        elif lead_time < 0:
            return "LAGGING", lead_time
        else:
            return "SIMULTANEOUS", 0
    elif f_time and not b_time:
        return "F_ONLY_NO_PHYSICAL_BREACH", None
    elif b_time and not f_time:
        return "BREACH_ONLY_NO_FORECAST", None
    else:
        return "INDETERMINATE", None


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

        # Sort episodes chronologically so we can cap backward padding
        # at the previous episode's end (contamination guard).
        episodes_sorted = sorted(
            episodes, key=lambda e: parse_time(e["temporal_bounds"]["start_time"])
        )

        print(f"Processing {dataset_name}: {len(episodes_sorted)} episode(s)...")

        prev_end = None
        for ep in episodes_sorted:
            st = parse_time(ep["temporal_bounds"]["start_time"])
            et = parse_time(ep["temporal_bounds"]["end_time"])

            # --- STRICT (unpadded) ---
            f_time_strict = find_first_forecast(st, et, incidents)
            b_time_strict, b_note_strict = find_first_breach(st, et, physical_breach_df)
            strict_class, strict_lead = classify(f_time_strict, b_time_strict)

            # --- PADDED (symmetric, capped at previous episode's end) ---
            padded_start = st - timedelta(minutes=PAD_MINUTES)
            if prev_end is not None and padded_start < prev_end:
                padded_start = prev_end + timedelta(minutes=1)

            f_time_padded = find_first_forecast(padded_start, et, incidents)
            b_time_padded, b_note_padded = find_first_breach(padded_start, et, physical_breach_df)
            padded_class, padded_lead = classify(f_time_padded, b_time_padded)

            rows.append({
                "dataset": dataset_name,
                "episode_id": ep.get("episode_id"),
                "start_time": ep["temporal_bounds"]["start_time"],
                "end_time": ep["temporal_bounds"]["end_time"],
                "padded_start_used": padded_start.strftime("%Y-%m-%d %H:%M:%S"),
                "strict_classification": strict_class,
                "strict_lead_time_minutes": strict_lead,
                "strict_first_forecast": str(f_time_strict) if f_time_strict else None,
                "strict_first_breach": str(b_time_strict) if b_time_strict else None,
                "padded_classification": padded_class,
                "padded_lead_time_minutes": padded_lead,
                "padded_first_forecast": str(f_time_padded) if f_time_padded else None,
                "padded_first_breach": str(b_time_padded) if b_time_padded else None,
                "changed_by_padding": strict_class != padded_class,
            })

            prev_end = et

    return pd.DataFrame(rows)


def write_report(detail_df):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail_df.to_csv(DETAIL_CSV_PATH, index=False)

    lines = []
    lines.append("# AEGIS — 4.4 Lead/Lag Audit — Strict vs. Padded Window")
    lines.append("")
    lines.append(
        "Both windows use the SAME underlying corrected logic "
        "(gap-safe segments, min_periods=W baseline, realized-event "
        "breach detector). The only difference is whether the search "
        "for F>=0.50 and the physical breach is allowed to look back "
        f"{PAD_MINUTES} minutes before the episode's recorded start "
        "(capped at the previous episode's end, so episodes never "
        "borrow each other's signal)."
    )
    lines.append("")
    lines.append(f"Total episodes evaluated: {len(detail_df)}")
    lines.append("")

    lines.append("## STRICT classification distribution")
    lines.append("```")
    lines.append(detail_df["strict_classification"].value_counts().to_string())
    lines.append("```")
    lines.append("")

    lines.append("## PADDED classification distribution")
    lines.append("```")
    lines.append(detail_df["padded_classification"].value_counts().to_string())
    lines.append("```")
    lines.append("")

    changed = detail_df[detail_df["changed_by_padding"]]
    lines.append(f"## Episodes whose classification changed with padding: {len(changed)} / {len(detail_df)}")
    lines.append("")
    if len(changed) > 0:
        lines.append("```")
        lines.append(
            changed[[
                "dataset", "episode_id", "strict_classification",
                "padded_classification", "padded_lead_time_minutes"
            ]].to_string(index=False)
        )
        lines.append("```")
    lines.append("")

    padded_leading = detail_df[detail_df["padded_classification"] == "LEADING"]
    if len(padded_leading) > 0:
        lines.append("## Lead-time statistics — PADDED, LEADING episodes only")
        lines.append(f"N = {len(padded_leading)}")
        lines.append(f"Mean:   {padded_leading['padded_lead_time_minutes'].mean():.2f} min")
        lines.append(f"Median: {padded_leading['padded_lead_time_minutes'].median():.2f} min")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDetail CSV written to: {DETAIL_CSV_PATH}")
    print(f"Report written to:     {REPORT_MD_PATH}")


def main():
    print("=================================================================")
    print("   4.4 LEAD/LAG AUDIT V2 — STRICT vs. PADDED (symmetric, capped)")
    print("=================================================================")
    print(f"Pad window: {PAD_MINUTES} min before episode start "
          f"(capped at previous episode's end)")
    print()

    detail_df = run_full_audit()

    if len(detail_df) == 0:
        print("\n[ERROR] No episodes could be processed.")
        return

    print("\n--- STRICT DISTRIBUTION ---")
    print(detail_df["strict_classification"].value_counts().to_string())

    print("\n--- PADDED DISTRIBUTION ---")
    print(detail_df["padded_classification"].value_counts().to_string())

    changed = detail_df[detail_df["changed_by_padding"]]
    print(f"\nEpisodes changed by padding: {len(changed)} / {len(detail_df)}")

    write_report(detail_df)


if __name__ == "__main__":
    main()
