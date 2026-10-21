# AEGIS — 4.4 Lead/Lag Audit — Strict vs. Padded Window

Both windows use the SAME underlying corrected logic (gap-safe segments, min_periods=W baseline, realized-event breach detector). The only difference is whether the search for F>=0.50 and the physical breach is allowed to look back 10 minutes before the episode's recorded start (capped at the previous episode's end, so episodes never borrow each other's signal).

Total episodes evaluated: 24

## STRICT classification distribution
```
strict_classification
SIMULTANEOUS                 11
INDETERMINATE                 5
LAGGING                       4
F_ONLY_NO_PHYSICAL_BREACH     2
LEADING                       1
BREACH_ONLY_NO_FORECAST       1
```

## PADDED classification distribution
```
padded_classification
SIMULTANEOUS                 11
LAGGING                       4
INDETERMINATE                 3
F_ONLY_NO_PHYSICAL_BREACH     3
BREACH_ONLY_NO_FORECAST       2
LEADING                       1
```

## Episodes whose classification changed with padding: 2 / 24

```
            dataset                    episode_id strict_classification     padded_classification  padded_lead_time_minutes
  Friday-02-03-2018   EP-Friday-02-03-2018-6652f2         INDETERMINATE   BREACH_ONLY_NO_FORECAST                       NaN
Thursday-15-02-2018 EP-Thursday-15-02-2018-5caa2f         INDETERMINATE F_ONLY_NO_PHYSICAL_BREACH                       NaN
```

## Lead-time statistics — PADDED, LEADING episodes only
N = 1
Mean:   7.00 min
Median: 7.00 min
