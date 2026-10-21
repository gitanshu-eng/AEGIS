# AEGIS — 4.4 Lead/Lag Full Audit

Every episode across all datasets, evaluated with the corrected (gap-safe, min_periods=W, realized-event) lead/lag logic — not just the 2 flagship CRITICAL episodes previously spot-checked.

Total episodes evaluated: 24

## Classification distribution

```
classification
SIMULTANEOUS                 11
INDETERMINATE                 5
LAGGING                       4
F_ONLY_NO_PHYSICAL_BREACH     2
LEADING                       1
BREACH_ONLY_NO_FORECAST       1
```

## Lead-time statistics (LEADING episodes only)

N = 1
Mean lead time:   7.00 min
Median lead time: 7.00 min
Max lead time:    7 min

## Simultaneous-onset episodes

11 / 24 episodes showed zero lead time — forecast and physical breach crossed threshold in the same 1-minute window.

**4 episode(s) classified LAGGING** — the physical breach preceded the forecast crossing 0.50. These deserve individual review; a lagging classification on a CRITICAL-adjacent episode would mean AEGIS confirmed escalation only after it was already underway.

## Per-dataset breakdown

```
classification        BREACH_ONLY_NO_FORECAST  F_ONLY_NO_PHYSICAL_BREACH  INDETERMINATE  LAGGING  LEADING  SIMULTANEOUS
dataset                                                                                                                
Friday-02-03-2018                           0                          0              2        1        1             0
Friday-16-02-2018                           0                          1              0        0        0             0
Thuesday-20-02-2018                         0                          0              0        0        0             1
Thursday-01-03-2018                         0                          0              0        0        0             2
Thursday-15-02-2018                         0                          1              1        0        0             5
Wednesday-14-02-2018                        1                          0              2        2        0             0
Wednesday-21-02-2018                        0                          0              0        1        0             1
Wednesday-28-02-2018                        0                          0              0        0        0             2
```

## Episodes with no clean comparison

8 episode(s) had no forecast crossing 0.50, no physical breach, or no valid baseline history at all within the episode window. See the detail CSV's `note` column for specifics on each.
