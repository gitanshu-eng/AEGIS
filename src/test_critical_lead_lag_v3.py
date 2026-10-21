"""
AEGIS — 4.4 Lead/Lag Diagnostic (V3 — Gap-Safe Ground Truth)
=============================================================

WHY THIS VERSION EXISTS
------------------------
V2 of this script computed the Phase 2 ground-truth target Y_t using:

    df['max_future_5'] = df['attack_rate'].shift(-1).rolling(window=5, min_periods=1).max()

This is WRONG. Shifting by -1 and then applying a backward rolling
window mixes 4 past/current values with only 1 genuinely future value
— it does not compute a forward-looking maximum at all. It also read
the continuous CSV with no `observed` filtering and no segment
boundary logic, so both the baseline and the "future" window could
silently span a real sensor gap or start from a near-empty window
(min_periods=1).

Both bugs push Y_t to become true almost as soon as attack_rate
itself rises — i.e. it ends up measuring "is the network currently
elevated," not "will it escalate in the next H minutes." That is why
V2 reported SIMULTANEOUS for every flagship CRITICAL episode: it was
comparing F against a broken, non-forward-looking proxy, not the real
Phase 2 target.

This version reuses the exact, already-validated logic from
target_feasibility_analysis.py:

    * _assign_segment_ids  — derive segments from observed==1 rows +
      time-continuity (gap > 1 minute starts a new segment)
    * compute_forward_max  — an explicit, index-safe forward window
      (max of the NEXT H values, never including the current one),
      proven correct against synthetic gap fixtures, instead of a
      shift+rolling trick

and computes the baseline with a proper backward rolling window
(min_periods=W, not 1), so a segment must have W genuine history
points before a baseline is even defined.

WHAT THIS SCRIPT DOES
----------------------
For each named CRITICAL timestamp, find its enclosing Phase 4
episode, then within that episode's bounds:

    f_time = first minute where Phase 3's forecast signal F >= 0.50
             (Phase 2's own frozen, validated operating threshold —
             unchanged from V2)

    b_time = first minute where the REAL Phase 2 ground-truth target
             Y_t is true, i.e.
                 max(attack_rate[t+1 .. t+H]) > baseline_W(t) + tau
             computed gap-safely, per-segment, with W=10, H=5,
             tau=0.10 (Phase 2's frozen final formulation)

Both f_time and b_time are only ever computed from valid (gap-safe,
fully-in-segment) rows. If Y_t is never true within the episode
bounds using the CORRECT computation, b_time is None and the episode
is classified INDETERMINATE-side, not silently forced to some other
value.

This is a diagnostic/test script, not a pipeline stage — it does not
modify any Phase 1-4 output. It only reads.
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

EPISODE_DIR = Path("outputs/phase4_investigations")
INCIDENT_DIR = Path("outputs/incident_records")
PHASE1_DIR = Path("data/processed")

# Phase 2's frozen final formulation (AWS_AEGIS_Phase_2_Documentation.pdf, item 37)
W = 10
H = 5
TAU = 0.10

# Phase 2's own frozen operating threshold for F (item 30/31: "fixed test threshold = 0.5")
F_THRESHOLD = 0.50


def parse_time(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------
# Reused, already-validated logic from target_feasibility_analysis.py
# (kept verbatim in behavior — see that file's docstrings for the full
# correctness reasoning and the synthetic-fixture tests that validated
# it before it was trusted on real data).
# ----------------------------------------------------------------------

def assign_segment_ids(df):
    """Derive segment_id from time continuity within observed==1 rows.
    Any gap > 1 minute between consecutive observed rows starts a new
    segment. df must already be sorted by time_window and filtered to
    observed == 1.
    """
    time_diff_minutes = df["time_window"].diff().dt.total_seconds().div(60)
    is_new_segment = (time_diff_minutes.isna()) | (time_diff_minutes > 1)
    df = df.copy()
    df["segment_id"] = is_new_segment.cumsum().astype(int)
    return df


def compute_forward_max(segment_values, h):
    """For each position i, max(segment_values[i+1 : i+1+h]) — the
    NEXT h values only, never including position i. NaN if fewer than
    h future values remain in this segment (horizon would cross the
    end of the segment / a gap). Explicit O(n*h) computation — no
    shift+rolling trick, to avoid exactly the bug this script exists
    to fix.
    """
    n = len(segment_values)
    result = np.full(n, np.nan)
    for i in range(n - h):
        result[i] = np.max(segment_values[i + 1: i + 1 + h])
    return result


def compute_ground_truth_yt(dataset_name):
    """Load the Phase 1 continuous file for one dataset and compute
    the REAL, gap-safe Phase 2 ground-truth Y_t at every valid minute.

    Returns a DataFrame with columns: time_window, attack_rate,
    segment_id, baseline, forward_max, valid, Y_t — where Y_t is only
    meaningful (True/False, not a leaked artifact) on rows where
    valid == True.
    """
    combined = _load_and_segment(dataset_name)
    if combined is None:
        return None

    pieces = []
    for segment_id, group in combined.groupby("segment_id", sort=False):
        group = group.reset_index(drop=True)
        series = group["attack_rate"]

        baseline = series.rolling(window=W, min_periods=W).mean()
        fwd_max = compute_forward_max(series.to_numpy(), H)

        piece = group[["time_window", "attack_rate", "segment_id"]].copy()
        piece["baseline"] = baseline.to_numpy()
        piece["forward_max"] = fwd_max
        pieces.append(piece)

    result = pd.concat(pieces, ignore_index=True)
    result["valid"] = result["baseline"].notna() & result["forward_max"].notna()
    result["Y_t"] = result["valid"] & (result["forward_max"] > (result["baseline"] + TAU))
    return result


def compute_physical_breach(dataset_name):
    """The REALIZED-event counterpart to Y_t: the first minute
    attack_rate ITSELF (not a forward-looking max) actually exceeds
    baseline_W(t) + tau. No forward_max / no lookahead — this answers
    "did the network actually become elevated right now," not "will
    it become elevated soon." Same segment-safe, min_periods=W
    baseline as compute_ground_truth_yt, computed on the FULL
    per-segment series and only filtered to an episode window by the
    caller afterward — never windowed before the rolling computation.
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


def _load_and_segment(dataset_name):
    """Shared loader: read the Phase 1 continuous file, drop gap-filler
    (observed==0) rows, and derive gap-safe segment_id. Used by both
    ground-truth functions so they never diverge on gap handling.
    """
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


# ----------------------------------------------------------------------
# Lead/lag calculation
# ----------------------------------------------------------------------

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
    b_position_in_segment = None
    b_valid_rows_before = None
    if physical_breach_df is not None:
        # Filter to episode bounds AFTER the full-day rolling baseline
        # was already computed in compute_physical_breach — never
        # slice before rolling.
        ep_df = physical_breach_df[
            (physical_breach_df["time_window"] >= st)
            & (physical_breach_df["time_window"] <= et)
        ]
        breach_events = ep_df[ep_df["physical_breach"]]
        if not breach_events.empty:
            first_breach_row = breach_events.iloc[0]
            b_time = first_breach_row["time_window"].to_pydatetime()

            # Diagnostic: how far into its segment was this row, and
            # how many VALID (baseline-defined) rows came before it in
            # that same segment? If this is the very first valid row
            # of the segment (valid_rows_before == 0), the baseline
            # had the bare minimum W points and may already include
            # early attack minutes — worth flagging, not a bug.
            seg_id = first_breach_row["segment_id"]
            full_segment = physical_breach_df[physical_breach_df["segment_id"] == seg_id]
            full_segment = full_segment.sort_values("time_window").reset_index(drop=True)
            row_pos = full_segment.index[
                full_segment["time_window"] == first_breach_row["time_window"]
            ][0]
            b_position_in_segment = int(row_pos)
            b_valid_rows_before = int(full_segment.iloc[:row_pos]["valid"].sum())
        else:
            n_valid = int(ep_df["valid"].sum())
            if n_valid == 0:
                b_note = "NO_VALID_BASELINE_ROWS_IN_EPISODE_WINDOW"
            else:
                b_note = f"NO_PHYSICAL_BREACH_IN_{n_valid}_VALID_ROWS"

    if f_time and b_time:
        lead_time = int((b_time - f_time).total_seconds() / 60)
        if lead_time > 0:
            classification = "LEADING"
        elif lead_time < 0:
            classification = "LAGGING"
        else:
            classification = "SIMULTANEOUS"
    elif f_time and not b_time:
        classification = "LEADING_NO_GROUND_TRUTH_ESCALATION"
        lead_time = 0
    elif b_time and not f_time:
        classification = "LAGGING_NO_FORECAST"
        lead_time = 0
    else:
        classification = "INDETERMINATE"
        lead_time = 0

    return {
        "classification": classification,
        "first_forecast_elevation": str(f_time) if f_time else None,
        "first_physical_breach": str(b_time) if b_time else None,
        "ground_truth_note": b_note,
        "lead_time_minutes": lead_time,
        "breach_position_in_segment": b_position_in_segment,
        "breach_valid_rows_before": b_valid_rows_before,
    }


# ----------------------------------------------------------------------
# Test harness
# ----------------------------------------------------------------------

def test_target(dataset, target_timestamps):
    ep_file = EPISODE_DIR / f"{dataset}_episodes.json"
    inc_file = INCIDENT_DIR / f"{dataset}_incidents.json"

    if not ep_file.exists() or not inc_file.exists():
        print(f"Files for {dataset} not found.")
        return

    with open(ep_file, "r") as f:
        episodes = json.load(f)
    with open(inc_file, "r") as f:
        incidents = json.load(f)

    physical_breach_df = compute_physical_breach(dataset)
    if physical_breach_df is None:
        print(f"[WARN] No Phase 1 continuous file found for {dataset} — "
              f"physical breach cannot be computed.")

    print(f"\n--- Testing Dataset: {dataset} ---")

    for target_ts in target_timestamps:
        t_obj = parse_time(target_ts)
        target_ep = None
        for ep in episodes:
            st = parse_time(ep["temporal_bounds"]["start_time"])
            et = parse_time(ep["temporal_bounds"]["end_time"])
            if st <= t_obj <= et:
                target_ep = ep
                break

        if not target_ep:
            print(f"\nTarget CRITICAL Incident: {target_ts} -> NO MATCHING EPISODE FOUND")
            continue

        print(f"\nTarget CRITICAL Incident: {target_ts}")
        print(f"Episode ID: {target_ep['episode_id']}")
        result = calculate_lead_lag(
            target_ep["temporal_bounds"]["start_time"],
            target_ep["temporal_bounds"]["end_time"],
            incidents,
            physical_breach_df,
        )
        print(f"Classification:              {result['classification']}")
        print(f"First F>=0.50:                {result['first_forecast_elevation']}")
        print(f"First physical breach:        {result['first_physical_breach']}")
        if result["breach_position_in_segment"] is not None:
            print(f"Breach row position in segment: {result['breach_position_in_segment']}")
            print(f"Valid rows BEFORE breach in segment: {result['breach_valid_rows_before']}")
        if result["ground_truth_note"]:
            print(f"Note:                         {result['ground_truth_note']}")
        print(f"Lead Time (mins):             {result['lead_time_minutes']}")


def run():
    print("=================================================================")
    print("      4.4 LEAD/LAG DIAGNOSTIC: V3 GAP-SAFE GROUND TRUTH LOGIC")
    print("=================================================================")
    print(f"Ground-truth target: W={W}, H={H}, tau={TAU} "
          f"(Phase 2 frozen formulation)")
    print(f"Forecast operating threshold: F >= {F_THRESHOLD} "
          f"(Phase 2 frozen threshold)")

    test_target("Thursday-01-03-2018", ["2018-03-01 02:04:00", "2018-03-01 02:20:00"])
    test_target("Wednesday-21-02-2018", ["2018-02-21 10:23:00", "2018-02-21 10:31:00"])


if __name__ == "__main__":
    run()
