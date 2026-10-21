# AEGIS — Escalation Target Feasibility Analysis

This report contains ONLY descriptive statistics about candidate escalation-label definitions. No model was trained. No configuration was selected as a winner — each row below is checked against the stated acceptance criteria (Q5) and reported as-is.

Configurations tested: 144. Configurations meeting ALL stated criteria: 25.

## Configurations meeting all stated criteria

```
 H  W baseline_stat tau_method  tau_value  positive_rate  days_with_events  days_total  total_events
 1  5          mean      fixed       0.02         0.0953                 8          10           234
 1  5          mean      fixed       0.05         0.0672                 8          10           182
 1  5        median      fixed       0.02         0.0898                 8          10           236
 1  5        median      fixed       0.05         0.0600                 8          10           168
 1 10          mean      fixed       0.02         0.1025                 8          10           210
 1 10          mean      fixed       0.05         0.0762                 8          10           171
 1 15          mean      fixed       0.02         0.1113                 8          10           199
 1 15          mean      fixed       0.05         0.0833                 8          10           160
 5  5          mean      fixed       0.02         0.1874                 8          10            77
 5  5          mean      fixed       0.05         0.1524                 8          10            98
 5  5          mean      fixed       0.10         0.0984                 8          10            83
 5  5          mean      fixed       0.15         0.0582                 8          10            55
 5 10          mean      fixed       0.02         0.1970                 8          10            53
 5 10          mean      fixed       0.05         0.1630                 8          10            72
 5 10          mean      fixed       0.10         0.1062                 8          10            59
 5 15          mean      fixed       0.02         0.1994                 8          10            44
 5 15          mean      fixed       0.05         0.1696                 8          10            60
10  5          mean      fixed       0.02         0.2196                 8          10            43
10  5          mean      fixed       0.05         0.1935                 8          10            63
10  5          mean      fixed       0.10         0.1413                 8          10            65
10  5          mean      fixed       0.15         0.0884                 8          10            51
10  5          mean      fixed       0.20         0.0612                 8          10            35
10 10          mean      fixed       0.05         0.2010                 8          10            44
10 10          mean      fixed       0.10         0.1481                 8          10            41
10 15          mean      fixed       0.05         0.2056                 8          10            38
```

## Ceiling-effect diagnostic (label structurally unreachable)

Per (H, W, baseline_stat, tau) configuration, the % of valid timestamps where baseline + tau > 1 — meaning Y_t = 1 was mathematically impossible regardless of what happened next. High values are expected to concentrate on saturated days (e.g. a day whose mean attack_rate is already near 1).

```
 H  W baseline_stat tau_method  tau_value  max_ceiling_effect_pct
 1 15          mean   adaptive       2.00                   100.0
 1 15          mean   adaptive       3.00                   100.0
 1 15          mean      fixed       0.15                   100.0
 1 15          mean      fixed       0.10                   100.0
 1 15          mean      fixed       0.20                   100.0
 1 10        median      fixed       0.20                   100.0
 1 10        median      fixed       0.10                   100.0
 1 10        median      fixed       0.15                   100.0
 1 10        median   adaptive       2.00                   100.0
 1 10        median   adaptive       3.00                   100.0
```

## Per-day degeneracy check

For the configuration(s) meeting all stated criteria (or, if none, the configuration with the highest total_events, shown for reference only — NOT a recommendation), per-dataset positive rate and event count, to identify any day that would produce a degenerate LODO fold (zero or near-zero events).

**H=1, W=5, baseline=mean, tau_method=fixed, tau_value=0.02**
```
             dataset  total_valid  positive_count  positive_pct  event_count_raw  ceiling_effect_pct  regime_conflation_pct
   Friday-02-03-2018          515             149        28.932               79               0.000                 14.094
   Friday-16-02-2018           47               4         8.511                2              91.489                 25.000
   Friday-23-02-2018          546               0         0.000                0               0.000                    NaN
 Thuesday-20-02-2018          715              22         3.077                9               0.000                  0.000
 Thursday-01-03-2018          560              75        13.393               41               0.000                 88.000
 Thursday-15-02-2018          562              27         4.804               15               0.000                  0.000
 Thursday-22-02-2018          539               0         0.000                0               0.000                    NaN
Wednesday-14-02-2018          533              83        15.572               38               0.000                 45.783
Wednesday-21-02-2018          155              24        15.484               16               1.935                 12.500
Wednesday-28-02-2018          560              67        11.964               34               0.000                  0.000
```

## Notes / open items

- Input file path/schema is an ASSUMPTION (see module docstring) and must be confirmed against the current AWS repo before this script is trusted.
- `positive_rate`, `days_with_events`, and `total_events` are pooled across all 10 datasets for the summary table; the detail CSV retains full per-dataset granularity for closer inspection.
- No configuration is recommended by this script. The 'passing' list and the per-day degeneracy check are inputs to a human decision, not a selection.