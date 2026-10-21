# AEGIS Phase 2 — Lead-Time Metric Correction

**Status:** Addendum to frozen Phase 2 documentation.
**Date added:** Post Phase 4 audit.
**Affects:** Section 49-51 of AWS_AEGIS_Phase_2_Documentation.pdf
             ("Operational Lead-Time & Event-Level Audit").

---

## Original documented claim

```
67.8% Episode Hit Rate (40 of 59 caught)
3.0 Min Strict Causal Median Lead Time
```

These numbers are real and were produced by `src/operational_episode_audit.py`.
They are NOT retracted. However, Phase 4's independent lead/lag audit revealed
that they measure something different from what "lead time" intuitively implies,
and the original documentation did not make this distinction clear.

---

## What the Phase 2 audit actually measured

`operational_episode_audit.py` defines a "true escalation episode" as a
contiguous run of `actual_escalation == 1` in the forecast CSV, where
`actual_escalation` = `Y_t`, the Phase 2 training label:

```
Y_t = 1 if max(attack_rate[t+1 .. t+5]) > mu_10(t) + 0.10
```

Because `Y_t` looks 5 minutes forward, it goes true **up to 4 minutes before
the actual physical attack_rate breach** — by construction of the label, not
because of any model prediction.

"Lead time" in that audit = distance between the first model alert and the
first minute `Y_t = 1`, capped at 0. So a model alert firing 1 minute before
`Y_t` goes true is recorded as 1 minute of lead time — even though `Y_t` itself
was already 4 minutes ahead of the physical event, meaning the real lead time
against the actual network state is approximately 5 minutes. Conversely, a
model alert firing 2 minutes AFTER `Y_t` first goes true (but still before the
physical breach) records as 0 minutes of lead time, even though the model was
still 3 minutes ahead of reality.

**In short: the 3.0-minute median is measured against a reference point that
is itself 0-4 minutes ahead of the physical event. It is a label-relative
measure, not a physical-event-relative measure.**

---

## What Phase 4's independent audit measured

`src/lead_lag_full_audit.py` (validated via synthetic fixtures and the
breach-position-in-segment diagnostic) measured lead time against the PHYSICAL
EVENT: the first minute `attack_rate` itself actually exceeded `mu_10(t) + tau`,
with a gap-safe trailing baseline (min_periods=W, computed on the full per-day
series, never spanning a sensor gap).

Result across all 24 Phase 4 episodes:

```
SIMULTANEOUS (F and physical breach same minute):  11 / 24  (46%)
INDETERMINATE (no clean bidirectional signal):       5 / 24
LAGGING (breach preceded forecast):                 4 / 24
F_ONLY_NO_PHYSICAL_BREACH:                          2 / 24
BREACH_ONLY_NO_FORECAST:                            1 / 24
LEADING (genuine physical-event lead time):         1 / 24  (4.2%)
  — that 1 episode: 7-minute lead time
```

A padded-window check (searching 10 minutes before each episode's recorded
start) confirmed this is not an episode-boundary artifact: only 2/24 episodes
changed classification at all, and the LEADING count stayed at 1.

---

## Reconciliation — both numbers are valid, measuring different things

| Metric | Reference point | Result |
|---|---|---|
| Phase 2 audit lead time | First minute `Y_t = 1` (label-defined, up to 4 min ahead of physical event) | 3.0 min median |
| Phase 4 audit lead time | First minute physical `attack_rate` breach | ~0 min for 46% of episodes; 7 min for 1 episode |

Neither is wrong. The difference arises because `Y_t`'s own H=5 lookahead
contributes systematic apparent lead time to the Phase 2 measurement.

---

## Correct language going forward

**Do not say:**
> "AEGIS provides 3 minutes of advance warning before an attack."

**Say instead:**
> "AEGIS alerts a median of 3 minutes before the model's own escalation label
> window opens (W=10, H=5, tau=0.10). At the 1-minute temporal resolution of
> the sensor data, the model's forecast and the physical network breach
> typically co-occur in the same window. On one of 24 audited operational
> episodes, genuine 7-minute physical-event lead time was observed."

---

## What does NOT change

- The PR-AUC of 0.4608, the ablation results, the sensitivity analysis, the
  per-day LODO results — none of these are affected. This correction is
  specific to the operational lead-time interpretation only.
- Phase 2 is still frozen. This document is an addendum, not a rerun.
- The Phase 2 model itself is unchanged. The escalation formulation
  (W=10, H=5, tau=0.10, XGBoost, scale-invariant features) is still the
  correct, validated final formulation.

---

## Files involved

| File | Role |
|---|---|
| `src/operational_episode_audit.py` | Original Phase 2 audit — label-relative lead time |
| `src/lead_lag_full_audit.py` | Phase 4 independent audit — physical-event lead time |
| `src/test_critical_lead_lag_v3.py` | Per-episode diagnostic with warm-up-artifact check |
| `src/lead_lag_padded_audit.py` | Boundary-padding robustness check |
| `outputs/lead_lag_audit/lead_lag_full_audit_detail.csv` | Per-episode results |

