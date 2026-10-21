# AEGIS — COMPLETE TECHNICAL HANDOFF FOR CLAUDE CODE

## IMPORTANT

You are taking over an existing project called **AEGIS**.

Do NOT treat this as a new project.

The previous development work has already established the architecture, AWS environment, dataset pipeline, validation methodology, forecasting feature pipeline, and several experiments.

Your job is to:

1. Understand the project from first principles.
2. Understand exactly what has already been built.
3. Understand why each architectural decision was made.
4. Understand the exact datasets, outputs, commands, and results.
5. Do NOT redo completed work unnecessarily.
6. Do NOT silently redesign the architecture.
7. Do NOT assume older experimental code is still authoritative.
8. Preserve scientific validity.
9. Continue from the exact current state described below.

The current implementation is an **offline predictive cyber-defense research prototype** using CIC-IDS2018.

The eventual goal is to make AEGIS capable of ingesting network telemetry continuously and forecasting emerging malicious network behavior, explaining why the model believes risk is increasing, simulating possible interventions, defending, verifying the result, and remembering incidents.

---

# 1. WHAT IS AEGIS?

## Project name

**AEGIS — Predictive Cyber Defense Platform**

The core idea is:

> Move cybersecurity operations from purely reactive alerting toward proactive prediction and intervention.

Traditional SOC workflow:

```text
Network traffic
      ↓
Detection
      ↓
Alert
      ↓
Human investigates
      ↓
Response
```

AEGIS is intended to move toward:

```text
Observe
   ↓
Predict
   ↓
Explain
   ↓
Investigate
   ↓
Simulate
   ↓
Decide
   ↓
Defend
   ↓
Verify
   ↓
Remember
```

The important conceptual distinction is:

AEGIS does NOT claim:

> "The attacker will attack at exactly 11:42."

That would be scientifically unjustified.

Instead, AEGIS should say things conceptually like:

> "Given the recent temporal behavior of the network, the probability/severity of malicious activity is increasing."

or:

> "The observed network trajectory is becoming more consistent with a previously observed attack pattern."

The model is forecasting **future network behavior / attack-related state**, not magically predicting the exact time a human attacker will act.

---

# 2. WHAT PROBLEM ARE WE SOLVING?

Cybersecurity systems often generate alerts after suspicious activity is already happening.

The problem is therefore:

```text
Reactive detection tells us:
"Something suspicious is happening now."

AEGIS wants to additionally answer:
"What is the network trajectory likely to look like next?"
```

The project therefore needs a temporal forecasting layer.

Instead of looking at one network-flow record independently, we aggregate network activity into temporal network states.

For example:

```text
01:00 → network state
01:01 → network state
01:02 → network state
01:03 → network state
...
```

Each network state contains quantities such as:

```text
total flows
benign flows
attack flows
attack rate
average flow duration
average flow bytes
average flow packets
```

Then we ask:

```text
Given recent network states:

t-5
t-3
t-2
t-1

can we forecast:

t
```

The initial target is:

```text
future attack_rate
```

Eventually this becomes one component of a larger cyber-risk system.

---

# 3. HIGH-LEVEL AEGIS ARCHITECTURE

The intended architecture is:

```text
                ┌──────────────────┐
                │ Network Telemetry│
                └────────┬─────────┘
                         ↓
                    OBSERVE
                         ↓
                  Temporal State
                         ↓
                    PREDICT
                         ↓
               Forecast / trajectory
                         ↓
                    EXPLAIN
                         ↓
             Evidence + feature impact
                         ↓
                  INVESTIGATE
                         ↓
             Historical/context analysis
                         ↓
                   SIMULATE
                         ↓
            Counterfactual intervention
                         ↓
                    DECIDE
                         ↓
              Defensive action selection
                         ↓
                    DEFEND
                         ↓
              Apply/represent action
                         ↓
                    VERIFY
                         ↓
              Did risk actually decrease?
                         ↓
                   REMEMBER
                         ↓
              Store incident knowledge
```

The current work is primarily focused on the **Observe → Predict** foundation.

---

# 4. IMPORTANT ARCHITECTURAL DECISION: NEMOTRON WAS DROPPED

An earlier architecture included:

* NVIDIA Nemotron
* Nebius Token Factory
* agentic investigation
* tool-calling

That approach has been explicitly abandoned.

Reason:

The required payment/card setup for the relevant Nebius service could not be completed.

Therefore:

## DO NOT REINTRODUCE NEMOTRON.

Do not assume the project currently has:

```text
Nemotron agent
Token Factory
LLM investigation agent
```

Those are no longer part of the current implementation unless the project owner explicitly reintroduces them.

The current project direction is focused on:

* temporal network data
* forecasting
* evidence
* deterministic cyber intelligence
* risk
* simulation
* defensive logic
* memory
* product/dashboard

The project should remain useful even without Nemotron.

---

# 5. CURRENT DEVELOPMENT PHILOSOPHY

There is a strong requirement for scientific validity.

Do not optimize only for:

```text
"hackathon demo looks impressive"
```

Instead optimize for:

```text
correct data
+
correct temporal semantics
+
no leakage
+
proper held-out evaluation
+
generalization
+
clear limitations
+
reproducibility
```

The user specifically wants AEGIS to eventually be useful/sellable/presentable even if the hackathon result does not go as expected.

Therefore:

DO NOT fabricate impressive model metrics.

If the model performs badly, report that and investigate why.

---

# 6. LOCAL DEVELOPMENT ENVIRONMENT

Local project path:

```text
D:\AEGIS
```

Environment:

```text
Python 3.13.13
Git 2.53.0.windows.1
VS Code 1.137.0
AWS CLI 2.36.48
```

Virtual environment:

```text
.venv
```

Project structure includes:

```text
AEGIS/
│
├── .venv/
├── code/
├── configuration/
├── data/
├── notebooks/
├── outputs/
├── src/
├── tests/
├── requirements.txt
└── .gitignore
```

The project was also connected to Git.

---

# 7. AWS ENVIRONMENT

The project was moved toward AWS for larger-scale data processing/training.

S3 bucket:

```text
aegis-cic-training-2026-model.v1
```

Raw CIC-IDS2018 data:

```text
s3://aegis-cic-training-2026-model.v1/datasets/cic-ids2018/raw/
```

Processed/feature destination:

```text
s3://aegis-cic-training-2026-model.v1/features/cic-ids2018/
```

EC2 instance:

```text
AEGIS-Preprocessing
```

Ubuntu environment.

Project directory:

```text
/home/ubuntu/AEGIS
```

Python virtual environment:

```text
(.venv)
```

S3 access works through an IAM role.

---

# 8. IMPORTANT AWS DATA DESIGN

Raw datasets should remain in S3.

DO NOT unnecessarily download huge raw CSVs from S3 to EC2.

The preferred architecture is:

```text
S3 raw dataset
      ↓
EC2
      ↓
stream/chunk process
      ↓
processed temporal representation
```

For large raw CSV validation, use:

```python
boto3
```

and:

```python
get_object(...)[Body]
```

with chunked pandas processing where appropriate.

Temporary compact artifacts may be created when necessary, but should be deleted afterward.

The raw S3 datasets should not be modified.

---

# 9. CIC-IDS2018 DATASETS

There are currently 10 CIC-IDS2018 raw CSV datasets being used.

Files:

```text
Friday-02-03-2018
Friday-16-02-2018
Friday-23-02-2018
Thuesday-20-02-2018
Thursday-01-03-2018
Thursday-15-02-2018
Thursday-22-02-2018
Wednesday-14-02-2018
Wednesday-21-02-2018
Wednesday-28-02-2018
```

IMPORTANT:

The spelling:

```text
Thuesday-20-02-2018
```

is the actual filename spelling and should NOT be silently changed.

---

# 10. PHASE 1 — DATA PIPELINE

Phase 1 transforms raw flow-level traffic into temporal network states.

The pipeline is:

```text
RAW CSV
   ↓
Dataset Adapter
   ↓
Common Cleaning
   ↓
Timestamp Normalization
   ↓
Duplicate Removal
   ↓
Temporal Feature Generation
   ↓
Continuous Timeline
   ↓
Validation
   ↓
Temporal Dataset
```

The objective is NOT forecasting yet.

The objective is:

> Turn raw flow records into scientifically valid temporal network-state sequences.

---

# 11. COMMON AEGIS TEMPORAL SCHEMA

All 10 processed datasets use the same 9-column temporal schema:

```text
time_window
total_flows
benign_flows
attack_flows
avg_flow_duration
avg_flow_bytes
avg_flow_packets
attack_rate
observed
```

Meaning:

### time_window

One-minute temporal bucket.

### total_flows

Number of network flows in that minute.

### benign_flows

Number of benign flows.

### attack_flows

Number of attack flows.

### avg_flow_duration

Average flow duration.

### avg_flow_bytes

Average flow bytes.

### avg_flow_packets

Average flow packets.

### attack_rate

Defined as:

```text
attack_flows / total_flows
```

and therefore should remain in:

```text
0 ≤ attack_rate ≤ 1
```

### observed

Critical semantic field.

```text
observed = 1
```

means actual traffic was recorded in that temporal window.

```text
observed = 0
```

means there was no recorded traffic/window.

DO NOT interpret:

```text
observed = 0
```

as:

```text
attack_rate = 0
```

That would introduce false information.

Unobserved windows retain missing values for the network-state variables.

---

# 12. IMPORTANT TIMELINE DECISION

There was an architectural question about whether every dataset should be forced to exactly:

```text
01:00 → 12:59
```

with 720 rows.

That approach was rejected.

Why?

Because forcing a fixed timeline outside the dataset's real recording boundaries would introduce artificial unobserved periods.

Current correct behavior:

```python
full_timeline = pd.date_range(
    start=df["time_window"].min(),
    end=df["time_window"].max(),
    freq=TEMPORAL_FREQUENCY
)
```

Therefore:

> Each dataset's continuous timeline follows its actual first and last observed temporal window.

DO NOT reintroduce fixed 720-minute padding without explicit scientific justification.

---

# 13. CONFIGURATION

Current:

```text
configuration/dataset_config.py
```

contains:

```python
DATASET_NAME = "CIC-IDS2018"
RAW_DATA_DIR = "data/raw/CIC-IDS2018"
INTERIM_DATA_DIR = "data/interim"
PROCESSED_DATA_DIR = "data/processed"
TIMESTAMP_COLUMN = "Timestamp"
LABEL_COLUMN = "Label"
TEMPORAL_FREQUENCY = "1min"
```

---

# 14. INITIAL FRIDAY-02-03-2018 CLEANING

The first dataset worked on locally was:

```text
Friday-02-03-2018_TrafficForML_CICFlowMeter.csv
```

Size:

```text
352,368,373 bytes
```

Columns:

```text
80
```

Initial inspection of first 10,000 rows:

```text
Bot       8520
Benign    1480
```

Missing:

```text
Flow Byts/s = 21
```

Duplicate rows:

```text
15
```

Raw rows:

```text
1,048,575
```

After cleaning:

```text
Duplicates removed: 5,459
Missing Flow Byts/s handled: 2,558
Final rows: 1,043,116
```

Validation:

```text
Missing values: 0
Duplicates: 0
Timestamp:
2018-03-02 01:00:00
to
2018-03-02 12:59:59
```

Final labels:

```text
Benign = 760,806
Bot    = 282,310
```

The cleaned output was:

```text
data/interim/Friday-02-03-2018_cleaned.csv
```

---

# 15. FIRST TEMPORAL TRANSFORMATION

The first Friday temporal dataset originally produced:

```text
525 observed minute windows
```

Expected natural range:

```text
01:00–12:59
```

which is:

```text
720 possible minutes
```

There was a gap:

```text
05:31–08:45
```

containing:

```text
195 missing minutes
```

Therefore:

```text
720 total timeline rows
525 observed
195 unobserved
```

The continuous temporal dataset was created with:

```text
9 columns
720 rows
```

The unobserved 195 rows have:

```text
observed = 0
```

and missing network-state values.

---

# 16. PHASE 1 VALIDATION OF ALL 10 DATASETS

All 10 datasets eventually passed all defined structural Phase 1 validation checks.

Important wording:

Say:

> "10/10 datasets passed all defined Phase 1 validation checks."

Do NOT claim:

> "100% data accuracy."

The validation checks included:

* expected row counts
* observed/unobserved counts
* 9-column schema
* no duplicate time windows
* chronological ordering
* observed rows have no missing network-state values
* attack rate remains in [0,1]
* benign + attack = total
* flow consistency
* unobserved rows retain appropriate missing temporal features

---

# 17. EXACT PHASE 1 RESULTS — ALL 10 DATASETS

## 1. Friday-02-03-2018

```text
Temporal rows: 525
Continuous rows: 720
Observed: 525
Unobserved: 195
```

Attack rate:

```text
max ≈ 0.805718
```

---

## 2. Friday-16-02-2018

```text
Temporal rows: 191
Continuous rows: 719
Observed: 191
Unobserved: 528
```

Raw coverage:

```text
first: 01:00:32
last:  12:58:24
```

The continuous timeline is 719 rows because it follows actual min/max timestamps.

This is intentional.

---

## 3. Friday-23-02-2018

```text
Temporal rows: 556
Continuous rows: 720
Observed: 556
Unobserved: 164
```

Attack rate maximum:

```text
≈ 0.008606
```

This dataset has extremely low attack-rate magnitude compared with some other days.

---

# 18. THUESDAY-20-02-2018 SPECIAL VALIDATION

```text
Temporal rows: 720
Continuous rows: 720
Observed: 720
Unobserved: 0
```

Raw rows:

```text
7,948,748
```

A naive full-row duplicate set was attempted.

It consumed too much RAM and was killed after approximately:

```text
2.8 million rows
```

We did NOT continue with that approach.

Instead, exact duplicate checking was done using a:

```text
256-bucket SHA-256 fingerprinting approach
```

Result:

```text
exactly 2 duplicate rows
```

Both were:

```text
benign
```

The raw S3 dataset was left untouched.

Temporary files were deleted.

---

# 19. THURSDAY-01-03-2018

```text
Temporal rows: 570
Continuous rows: 720
Observed: 570
Unobserved: 150
```

---

# 20. WEDNESDAY-14-02-2018

```text
Temporal rows: 543
Continuous rows: 720
Observed: 543
Unobserved: 177
```

---

# 21. THURSDAY-15-02-2018

```text
Temporal rows: 572
Continuous rows: 720
Observed: 572
Unobserved: 148
```

Attack-rate maximum:

```text
≈ 0.704566
```

---

# 22. THURSDAY-22-02-2018 SPECIAL TIMESTAMP ISSUE

Normal temporal result:

```text
Temporal rows: 549
Continuous rows: 720
Observed: 549
Unobserved: 171
```

However, 9 anomalous timestamps were found around January 1970:

```text
10/01/1970 03:04:26
11/01/1970 12:05:36
11/01/1970 05:12:30
11/01/1970 03:51:32
12/01/1970 06:40:49
12/01/1970 01:09:53
12/01/1970 09:18:52
12/01/1970 09:30:03
12/01/1970 09:30:26
```

They were isolated.

Remaining valid timestamps:

```text
1,048,566
```

Valid range:

```text
first: 01:00:00
last:  12:59:59
```

Unique observed minutes:

```text
549
```

The raw S3 dataset was NOT modified.

Attack-rate maximum:

```text
≈ 0.005838
```

---

# 23. WEDNESDAY-21-02-2018

This dataset has significantly less temporal coverage.

```text
Temporal rows: 170
Continuous rows: 529
Observed: 170
Unobserved: 359
```

Raw temporal coverage:

```text
first: 01:55:46
last: 10:43:21
```

Attack-rate maximum:

```text
≈ 0.999937
```

---

# 24. WEDNESDAY-28-02-2018

Raw rows:

```text
613,071
```

Temporal:

```text
570 observed
720 continuous
150 unobserved
```

Timestamp range:

```text
01:00:00 → 12:59:59
```

Attack-rate maximum:

```text
≈ 0.474082
```

---

# 25. CROSS-DATASET PROFILE

The continuous temporal datasets produced:

```text
Dataset                  Total   Observed   Unobserved   Usable lag
--------------------------------------------------------------------
Friday-02-03-2018          720       525         195          515
Friday-16-02-2018          719       191         528           47
Friday-23-02-2018          720       556         164          546
Thuesday-20-02-2018        720       720           0          715
Thursday-01-03-2018        720       570         150          560
Thursday-15-02-2018        720       572         148          562
Thursday-22-02-2018        720       549         171          539
Wednesday-14-02-2018       720       543         177          533
Wednesday-21-02-2018       529       170         359          155
Wednesday-28-02-2018       720       570         150          560
--------------------------------------------------------------------
TOTAL                     7008      4966        2042         4732
```

Important:

```text
7008 continuous rows
4966 observed rows
2042 unobserved rows
4732 usable forecasting rows
```

---

# 26. ATTACK-RATE DISTRIBUTION VARIATION

This is now an important scientific finding.

Examples:

```text
Friday-23-02-2018       max ≈ 0.008606
Thursday-22-02-2018     max ≈ 0.005838
Friday-02-03-2018       max ≈ 0.805718
Wednesday-21-02-2018    max ≈ 0.999937
Friday-16-02-2018       max = 1.0
```

Therefore, different days have very different traffic/attack regimes.

This becomes important when interpreting cross-day machine-learning performance.

---

# 27. PHASE 2 — FORECASTING

After Phase 1, the next task was to transform each temporal sequence into supervised forecasting samples.

Conceptually:

```text
t-5
t-3
t-2
t-1
 ↓
predict t
```

But gaps must never be crossed.

For example:

```text
observed
observed
observed
GAP
GAP
observed
```

The first observation after the gap must NOT use observations before the gap as lag history.

---

# 28. SEGMENT LOGIC

`src/forecasting_features.py`

uses:

```python
observed = df["observed"].eq(1)

time_diff = df["time_window"].diff()

new_segment = (
    observed
    & (
        ~observed.shift(fill_value=False)
        | (time_diff != pd.Timedelta(minutes=1))
    )
)
```

Then:

```python
df["segment_id"] = new_segment.cumsum()
```

Lags are generated using:

```python
df.groupby("segment_id")[feature].shift(lag)
```

This is extremely important.

It prevents leakage across missing/unobserved time periods.

---

# 29. ORIGINAL FORECASTING FEATURES

Initially only:

```text
attack_rate
```

was lagged.

Lag windows:

```text
1
2
3
5
```

Therefore:

```text
attack_rate_lag_1
attack_rate_lag_2
attack_rate_lag_3
attack_rate_lag_5
```

were used.

---

# 30. FORECASTING DATASET GENERATION

Script:

```text
src/forecasting_features.py
```

was generalized to process all:

```text
*_temporal_continuous.csv
```

instead of assuming a single dataset.

Command:

```bash
python src/forecasting_features.py
```

Output:

```text
Datasets processed: 10
Total usable forecasting rows: 4732
```

Per dataset:

```text
Friday-02-03-2018       515
Friday-16-02-2018        47
Friday-23-02-2018       546
Thuesday-20-02-2018     715
Thursday-01-03-2018     560
Thursday-15-02-2018     562
Thursday-22-02-2018     539
Wednesday-14-02-2018    533
Wednesday-21-02-2018    155
Wednesday-28-02-2018    560
```

Total:

```text
4732
```

There was previously an arithmetic mistake where 5232 was mistakenly stated.

That was corrected.

The correct number is:

```text
4732
```

Do not repeat the 5232 value.

---

# 31. MANUAL LAG VERIFICATION

Friday-02-03-2018 was manually inspected.

Example first forecasting rows:

```text
01:05
lag5 = 0.351511
lag3 = 0.281035
lag2 = 0.235740
lag1 = 0.355159
target = 0.394209
```

Next:

```text
01:06
lag5 = 0.327798
lag3 = 0.235740
lag2 = 0.355159
lag1 = 0.394209
target = 0.260785
```

Next:

```text
01:07
lag5 = 0.281035
lag3 = 0.355159
lag2 = 0.394209
lag1 = 0.260785
target = 0.356757
```

This verified that the lag alignment was correct and there was no obvious off-by-one error.

---

# 32. DAY-LEVEL SPLIT

Instead of random row splitting, the project uses **day-level separation**.

This is deliberate.

Random row splitting would cause temporal leakage and allow the model to see extremely similar temporal behavior from the same day in both training and testing.

Current split:

```text
TEST:
Friday-02-03-2018

VALIDATION:
Friday-16-02-2018

TRAIN:
Friday-23-02-2018
Thuesday-20-02-2018
Thursday-01-03-2018
Thursday-15-02-2018
Thursday-22-02-2018
Wednesday-14-02-2018
Wednesday-21-02-2018
Wednesday-28-02-2018
```

Counts:

```text
TRAIN       4170
VALIDATION    47
TEST         515
TOTAL       4732
```

Dataset overlap validation:

```text
PASS
```

---

# 33. RANDOM FOREST BASELINE

The initial RF experiment used:

```text
RandomForestRegressor
n_estimators = 200
random_state = 42
n_jobs = -1
```

Initial feature set:

```text
attack_rate_lag_1
attack_rate_lag_2
attack_rate_lag_3
attack_rate_lag_5
```

Target:

```text
attack_rate
```

A persistence baseline was also created.

Persistence means:

```text
prediction(t) = attack_rate(t-1)
```

This is an extremely important baseline because network states often exhibit temporal continuity.

---

# 34. FIRST FIXED SPLIT RF RESULTS

With:

```text
TRAIN = 4170
VALIDATION = 47
TEST = 515
```

results were:

```text
Persistence validation MAE = 0.024722
Persistence validation RMSE = 0.141321

Persistence test MAE = 0.054144
Persistence test RMSE = 0.090042

RF validation MAE = 0.204516
RF validation RMSE = 0.238737

RF test MAE = 0.057957
RF test RMSE = 0.092681
```

RF validation improvement:

```text
-727.28%
```

RF test improvement:

```text
-7.04%
```

---

# 35. VALIDATION-DAY PROBLEM

The validation day:

```text
Friday-16-02-2018
```

contains only:

```text
47 forecasting samples
```

Its target distribution was unusual:

```text
mean = 0.943952
std = 0.188147
min = 0
max = 1
median ≈ 0.997680
75th percentile = 1
```

Largest persistence error:

```text
2018-02-16 10:59
```

where:

```text
lag1 = 0.967213
target = 0
error = 0.967213
```

Therefore, the fixed validation day was judged unsuitable as the sole basis for model tuning.

This led to a stronger evaluation methodology.

---

# 36. LEAVE-ONE-DAY-OUT EVALUATION

Script:

```text
src/forecasting_leave_one_day_out.py
```

The experiment:

For each of the 10 days:

```text
1 day = test
other 9 days = training
```

No validation day is used in this experiment.

The purpose is:

> Test whether a model trained on other CIC-IDS2018 days can generalize to a completely unseen day.

This is much more useful for measuring cross-day generalization.

---

# 37. ORIGINAL 4-FEATURE RF LEAVE-ONE-DAY-OUT RESULTS

Initial RF used only four attack-rate lag features.

Results:

```text
TEST DAY                 Persistence MAE   RF MAE
-------------------------------------------------
Friday-02-03-2018            0.054144       0.057260
Friday-16-02-2018            0.024722       0.185262
Friday-23-02-2018            0.000292       0.002515
Thuesday-20-02-2018          0.003434       0.006755
Thursday-01-03-2018          0.043189       0.050773
Thursday-15-02-2018          0.011543       0.014893
Thursday-22-02-2018          0.000208       0.001586
Wednesday-14-02-2018         0.026814       0.030330
Wednesday-21-02-2018         0.081121       0.079090
Wednesday-28-02-2018         0.026163       0.024427
```

RF beat persistence only on:

```text
Wednesday-21-02-2018
+2.50%

Wednesday-28-02-2018
+6.63%
```

RF was worse on:

```text
8 / 10 days
```

Aggregate:

```text
Mean persistence MAE = 0.027163
Median persistence MAE = 0.025442

Mean RF MAE = 0.045289
Median RF MAE = 0.027379

Mean persistence RMSE = 0.073751
Mean RF RMSE = 0.082941

Mean RF MAE improvement = -222.73%
```

Therefore:

> The four-feature Random Forest did not generalize better than persistence across the 10 CIC-IDS2018 days.

---

# 38. IMPORTANT INTERPRETATION OF THAT RESULT

This does NOT mean:

```text
forecasting is impossible
```

It means:

```text
this particular RF formulation
+
these features
+
this cross-day generalization setup
```

did not outperform a persistence baseline.

That distinction is critical.

Persistence is very strong because if attack rate changes slowly:

```text
attack_rate(t) ≈ attack_rate(t-1)
```

then simply carrying forward the previous state can have very low error.

---

# 39. FEATURE EXPANSION EXPERIMENT

We then decided not to immediately jump to GRU/LSTM.

Instead we asked:

> Is the RF failing because four attack-rate lags do not contain enough information?

Therefore we expanded the feature set.

The seven temporal variables are:

```text
attack_rate
total_flows
benign_flows
attack_flows
avg_flow_duration
avg_flow_bytes
avg_flow_packets
```

Each receives:

```text
lag 1
lag 2
lag 3
lag 5
```

Therefore:

```text
7 variables × 4 lags = 28 lag features
```

---

# 40. FINAL FORECASTING FEATURE SCRIPT STATE

`src/forecasting_features.py`

now creates:

```text
attack_rate_lag_1
attack_rate_lag_2
attack_rate_lag_3
attack_rate_lag_5

total_flows_lag_1
total_flows_lag_2
total_flows_lag_3
total_flows_lag_5

benign_flows_lag_1
benign_flows_lag_2
benign_flows_lag_3
benign_flows_lag_5

attack_flows_lag_1
attack_flows_lag_2
attack_flows_lag_3
attack_flows_lag_5

avg_flow_duration_lag_1
avg_flow_duration_lag_2
avg_flow_duration_lag_3
avg_flow_duration_lag_5

avg_flow_bytes_lag_1
avg_flow_bytes_lag_2
avg_flow_bytes_lag_3
avg_flow_bytes_lag_5

avg_flow_packets_lag_1
avg_flow_packets_lag_2
avg_flow_packets_lag_3
avg_flow_packets_lag_5
```

The current forecasting file therefore has:

```text
10 non-lag columns
+
28 lag columns
=
38 total columns
```

The 10 non-lag columns are:

```text
time_window
total_flows
benign_flows
attack_flows
avg_flow_duration
avg_flow_bytes
avg_flow_packets
attack_rate
observed
segment_id
```

---

# 41. FEATURE GENERATION COMMAND

Command used:

```bash
python src/forecasting_features.py
```

Result:

```text
Datasets processed: 10
Total usable forecasting rows: 4732
```

This is correct.

---

# 42. FEATURE COLUMN VERIFICATION

Command used:

```bash
python -c "import pandas as pd; df=pd.read_csv('data/processed/Friday-02-03-2018_forecasting.csv'); print(len(df.columns)); print(df.columns.tolist())"
```

Output began with:

```text
38
```

and contained all expected columns.

This verified that the expanded feature generation was actually implemented rather than accidentally regenerating the old four-feature dataset.

---

# 43. SECOND RF EXPERIMENT — 28 FEATURES

We updated:

```text
src/forecasting_leave_one_day_out.py
```

to use all 28 lag features.

Command:

```bash
python src/forecasting_leave_one_day_out.py
```

The output confirmed:

```text
Datasets found: 10
Forecasting features: 28
```

---

# 44. CURRENT 28-FEATURE RF RESULTS

These are the most recent results and are the current state of the forecasting experiment.

```text
TEST DAY                 Persistence MAE    RF MAE
--------------------------------------------------
Friday-02-03-2018             0.054144       0.056804
Friday-16-02-2018             0.024722       0.193021
Friday-23-02-2018             0.000292       0.000709
Thuesday-20-02-2018           0.003434       0.018013
Thursday-01-03-2018           0.043189       0.092942
Thursday-15-02-2018           0.011543       0.017190
Thursday-22-02-2018           0.000208       0.001138
Wednesday-14-02-2018          0.026814       0.042271
Wednesday-21-02-2018          0.081121       0.094045
Wednesday-28-02-2018          0.026163       0.029610
```

RF improvement:

```text
Friday-02-03-2018        -4.91%
Friday-16-02-2018      -680.78%
Friday-23-02-2018      -142.95%
Thuesday-20-02-2018    -424.56%
Thursday-01-03-2018    -115.20%
Thursday-15-02-2018     -48.92%
Thursday-22-02-2018    -447.65%
Wednesday-14-02-2018    -57.65%
Wednesday-21-02-2018    -15.93%
Wednesday-28-02-2018    -13.17%
```

Therefore:

```text
RF beats persistence:
0 / 10 days
```

Aggregate:

```text
Mean persistence MAE = 0.027163
Median persistence MAE = 0.025442

Mean RF MAE = 0.054574
Median RF MAE = 0.035941

Mean persistence RMSE = 0.073751
Mean RF RMSE = 0.092220

Mean RF MAE improvement = -195.17%
```

---

# 45. CURRENT SCIENTIFIC CONCLUSION

This is the current most important result:

> The current Random Forest formulation, even after expanding from four attack-rate lag features to 28 lagged network-state features, does not outperform the persistence baseline on unseen CIC-IDS2018 days.

More specifically:

```text
4-feature RF:
Mean MAE = 0.045289

28-feature RF:
Mean MAE = 0.054574

Persistence:
Mean MAE = 0.027163
```

So simply adding more lagged aggregate network features did not solve the cross-day generalization problem.

DO NOT hide this result.

DO NOT tune random hyperparameters until the problem is understood.

DO NOT claim that RF is the final AEGIS forecasting model.

---

# 46. WHY THIS RESULT IS IMPORTANT

The data itself strongly suggests different network regimes.

For example:

```text
Friday-23-02-2018:
attack_rate max ≈ 0.008606

Thursday-22-02-2018:
attack_rate max ≈ 0.005838

Friday-02-03-2018:
attack_rate max ≈ 0.805718

Wednesday-21-02-2018:
attack_rate max ≈ 0.999937

Friday-16-02-2018:
attack_rate max = 1.0
```

A model trained on nine days is therefore being asked to learn a single transferable mapping across very different distributions.

Persistence does not have that problem to the same degree because it simply carries the current state forward.

---

# 47. NEXT SCIENTIFIC QUESTION

Before jumping to GRU/LSTM, the next thing to investigate is:

> How temporally autocorrelated is attack_rate?

Specifically measure:

```text
corr(
attack_rate(t),
attack_rate(t-1)
)

corr(
attack_rate(t),
attack_rate(t-2)
)

corr(
attack_rate(t),
attack_rate(t-3)
)

corr(
attack_rate(t),
attack_rate(t-5)
)
```

across the 10 datasets.

Why?

Because this will tell us whether persistence performs well because the target is inherently highly autocorrelated.

If:

```text
attack_rate(t) ≈ attack_rate(t-1)
```

then persistence is expected to be strong.

The next investigation may therefore involve forecasting:

```text
Δ attack_rate
```

rather than directly predicting absolute attack rate.

Conceptually:

```text
Past network state
       ↓
predict Δ attack_rate
       ↓
current attack_rate + predicted Δ
       ↓
future attack_rate
```

But DO NOT implement this blindly.

First measure temporal autocorrelation and inspect the target dynamics.

---

# 48. WHY WE HAVE NOT MOVED TO GRU/LSTM YET

The eventual intended model family is:

```text
GRU / LSTM
```

because AEGIS is fundamentally temporal.

But moving to a more sophisticated model before understanding the baseline would be bad methodology.

Current sequence of reasoning is:

```text
Simple baseline
      ↓
Random Forest
      ↓
More informative features
      ↓
Cross-day evaluation
      ↓
Understand why baseline wins
      ↓
Improve target/representation
      ↓
GRU/LSTM
```

This makes the final model comparison scientifically defensible.

Do NOT skip the baseline analysis.

---

# 49. EVENTUAL MODELING DIRECTION

The eventual forecasting model may use sequences rather than flattened lag columns.

Conceptually:

```text
t-5
 ↓
network state vector

t-4
 ↓
network state vector

t-3
 ↓
network state vector

t-2
 ↓
network state vector

t-1
 ↓
network state vector

        ↓

      GRU/LSTM

        ↓

forecast t
```

The exact sequence length has NOT yet been finalized.

Do not invent a sequence length without testing.

---

# 50. LIVE FORECASTING CONCEPT

AEGIS is ultimately intended to operate on live/streaming network telemetry.

The model should eventually see:

```text
current network state
+
recent history
```

and produce:

```text
forecast
```

But the current model is NOT yet live-ready.

Current state is:

```text
offline CIC-IDS2018 research/evaluation
```

Do not claim live attack prediction yet.

The eventual architecture should maintain the same feature/data contract between:

```text
training
```

and:

```text
live inference
```

This is important.

---

# 51. MULTI-DATASET PLAN

The current work is focused on the 10 CIC-IDS2018 files.

After the CIC-IDS2018 forecasting pipeline is stable, compatible external datasets can be added.

Possible future datasets discussed:

```text
CTU-13
IoT-23
```

The architecture should use dataset adapters.

Conceptually:

```text
CIC-IDS2018 adapter
       ↓
Common AEGIS temporal schema

CTU-13 adapter
       ↓
Common AEGIS temporal schema

IoT-23 adapter
       ↓
Common AEGIS temporal schema
```

Do NOT rebuild the entire common pipeline for every new dataset.

The dataset-specific adapter should normalize the raw schema into the common AEGIS representation.

---

# 52. TRAINING DATA PLAN

The intended future training direction is:

```text
Multiple compatible datasets
        ↓
common schema
        ↓
temporal representation
        ↓
forecasting model
        ↓
cross-dataset/generalization testing
```

However, the exact external-dataset integration has NOT been completed yet.

Do not pretend it has.

---

# 53. PHASE 3 — CYBER INTELLIGENCE / RISK

There was earlier Phase 3 work using the Friday reference model.

The risk formula used was:

```text
risk =
(
    0.45 * forecast_signal
    +
    0.40 * activity_signal
    +
    0.15 * error_signal
) * 100
```

Risk thresholds:

```text
LOW       0–30
MEDIUM   30–60
HIGH     60–80
CRITICAL 80–100
```

Earlier Friday reference output:

```text
risk scores approximately 21.53–44.50
```

with:

```text
LOW = 29
MEDIUM = 49
```

Top window:

```text
2018-03-02 11:42:00
```

Earlier outputs included:

```text
Friday-02-03-2018_risk_signals.csv
Friday-02-03-2018_risk.csv
Friday-02-03-2018_evidence.csv
```

That Phase 3 work was based on the earlier Friday reference experiment.

Therefore:

IMPORTANT:

Do not interpret those Friday-only numbers as generalized final AEGIS performance.

The generalized forecasting evaluation is now showing that the current RF formulation does not generalize well across all days.

Therefore Phase 3 risk logic eventually needs to be connected to a scientifically stronger forecasting layer.

---

# 54. EVIDENCE PHILOSOPHY

AEGIS should not say:

```text
"The model proves an attack will happen."
```

Instead:

```text
"The forecast indicates elevated future attack-related activity."
```

Evidence should include things such as:

```text
forecast signal
recent activity
historical behavior
feature importance
temporal trend
attack context
```

The system should distinguish:

```text
model prediction
```

from:

```text
deterministic observation
```

and:

```text
hypothetical simulation
```

---

# 55. COUNTERFACTUAL SIMULATION — FUTURE PHASE

The planned simulation concept is:

```text
Current network state
        ↓
Forecast baseline
        ↓
Hypothetical intervention
        ↓
Modify/cloned state
        ↓
Run forecast again
        ↓
Compare outcomes
```

Example conceptual action:

```text
Block traffic from Host A toward Host B
```

Then compare:

```text
risk before intervention
vs
risk after hypothetical intervention
```

This must be labeled:

> Model-based hypothetical simulation

It must NOT be presented as guaranteed real-world causality.

---

# 56. DEFENSIVE MODE — FUTURE

The eventual defensive workflow is intended to be:

```text
Observe
↓
Predict
↓
Explain
↓
Investigate
↓
Simulate
↓
Decide
↓
Defend
↓
Verify
↓
Remember
```

The user wants the system to eventually support autonomous defensive behavior.

However, this is a future stage.

Do not pretend that actual network blocking has already been implemented.

---

# 57. MEMORY / INCIDENT MEMORY — FUTURE

The intended memory layer includes structured incident information such as:

```text
incident_id
timestamp
hosts
forecast
evidence
risk
attack_context
action
resolution
```

Potential implementation discussed:

```text
PostgreSQL
pgvector
SQLAlchemy
```

The purpose:

```text
Have we seen something similar before?
```

Historical context should eventually help AEGIS understand repeated patterns.

Again:

This is planned architecture, not the current completed forecasting implementation.

---

# 58. DASHBOARD / PRODUCT — FUTURE

The eventual product should be a cybersecurity command center rather than a notebook.

Previously discussed API concepts included:

```text
/forecast
/network/state
/host/{id}/history
/incident/{id}
/agent/chat
/simulation
/risk
/defense/action
/defense/status
```

Potential stack:

```text
FastAPI
React / Next.js
```

But the current immediate work is still model/data validation.

Do not start building the dashboard just because it is visually attractive if the forecasting foundation is still being scientifically investigated.

---

# 59. IMPORTANT DEVELOPMENT RULES

When continuing this project:

## Rule 1 — Do not restart Phase 1

Phase 1 has already been completed for the current 10 CIC-IDS2018 datasets.

All 10 passed defined structural validation.

---

## Rule 2 — Do not destroy the raw data

Raw S3 data is authoritative.

Do not modify it.

---

## Rule 3 — Do not cross temporal gaps

Never create lag history across:

```text
observed = 0
```

or non-contiguous timestamps.

---

## Rule 4 — Do not random-split temporal data

Avoid:

```python
train_test_split(...)
```

for this forecasting evaluation unless there is a strong methodological reason.

Day-level/generalization evaluation is preferred.

---

## Rule 5 — Always compare against persistence

Persistence:

```text
prediction(t) = attack_rate(t-1)
```

is currently the strongest baseline.

Any new model should be compared against it.

---

## Rule 6 — Do not hide bad results

Current RF results are poor.

That is a finding.

Do not tune until metrics look good and then present only the good version.

---

## Rule 7 — Verify arithmetic

There have already been mistakes in manually reporting row totals.

The correct total forecasting rows is:

```text
4732
```

Always calculate from actual outputs.

---

## Rule 8 — Do not claim live prediction yet

Current system:

```text
offline CIC-IDS2018
```

Future system:

```text
live telemetry
```

These are different stages.

---

## Rule 9 — Do not claim exact attacker timing

AEGIS forecasts network behavior/attack-related trajectory.

It does not know the exact future action time of an attacker.

---

## Rule 10 — Do not blindly jump to deep learning

GRU/LSTM is an eventual direction.

First understand:

```text
why persistence is strong
```

and:

```text
why RF generalizes poorly.
```

---

# 60. CURRENT FILES OF PARTICULAR IMPORTANCE

Important scripts:

```text
configuration/dataset_config.py

src/forecasting_features.py

src/forecasting_split.py

src/forecasting_baseline.py

src/forecasting_model.py

src/forecasting_leave_one_day_out.py
```

Some older scripts were written for the original single-dataset experiment and may contain outdated assumptions.

In particular:

```text
forecasting_baseline.py
forecasting_model.py
forecasting_split.py
```

were originally based on older/single-file assumptions.

The generalized workflow now primarily revolves around:

```text
forecasting_features.py
forecasting_leave_one_day_out.py
```

Do not assume every old script reflects the latest architecture.

---

# 61. CURRENT PROCESSED DATA

The important generated files are:

```text
data/processed/*_temporal_continuous.csv
```

and:

```text
data/processed/*_forecasting.csv
```

There are 10 forecasting files.

Each forecasting file currently has:

```text
38 columns
```

and the total across all files is:

```text
4732 rows
```

---

# 62. EXACT CURRENT STATE

At the moment:

```text
Phase 1:
COMPLETE for 10 CIC-IDS2018 datasets

Temporal schema:
VALIDATED

Gap handling:
VALIDATED

Forecasting feature generation:
COMPLETE

4-feature RF baseline:
EVALUATED

28-feature RF experiment:
EVALUATED

Cross-day leave-one-day-out:
EVALUATED

Persistence baseline:
ESTABLISHED

Current RF:
DOES NOT BEAT persistence
```

---

# 63. CURRENT PROBLEM

The central current problem is:

```text
Why is persistence substantially outperforming our RF forecasting model?
```

The current numbers are:

```text
Persistence mean MAE = 0.027163

4-feature RF mean MAE = 0.045289

28-feature RF mean MAE = 0.054574
```

Therefore, simply adding more lagged network-state features made RF worse rather than better.

This means the next step should be **analysis**, not arbitrary tuning.

---

# 64. NEXT EXPERIMENT

The immediate next experiment should be a temporal autocorrelation analysis.

Calculate, per dataset:

```text
lag 1 autocorrelation
lag 2 autocorrelation
lag 3 autocorrelation
lag 5 autocorrelation
```

for:

```text
attack_rate
```

Potentially also inspect:

```text
attack_rate differences
```

such as:

```text
Δattack_rate(t)
=
attack_rate(t)
-
attack_rate(t-1)
```

The purpose is to determine whether the target is highly persistent.

---

# 65. POSSIBLE NEXT MODEL FORMULATION

If the analysis confirms strong persistence, investigate whether predicting the change is more appropriate:

Instead of:

```text
X_history → attack_rate(t)
```

test:

```text
X_history → Δattack_rate(t)
```

Then reconstruct:

```text
predicted_attack_rate(t)
=
attack_rate(t-1)
+
predicted_delta(t)
```

But this is only a candidate.

Do not implement it until the temporal analysis supports the decision.

---

# 66. EVENTUAL GRU/LSTM EXPERIMENT

Once the target formulation is understood, build a sequence model.

Potential architecture:

```text
sequence of network states
        ↓
GRU/LSTM
        ↓
forecast
```

The exact:

```text
sequence length
hidden size
layers
dropout
learning rate
loss
```

must be selected based on controlled experiments.

Do not invent final hyperparameters prematurely.

---

# 67. EVALUATION PHILOSOPHY FOR GRU/LSTM

The same held-out-day principle should remain.

For example:

```text
train on several days
test on an unseen day
```

Eventually, a stronger evaluation could involve:

```text
leave-one-day-out
+
external dataset testing
```

This would provide evidence of temporal and cross-dataset generalization.

---

# 68. FUTURE MULTI-DATASET GENERALIZATION

The eventual goal is not:

```text
model works on Friday-02-03-2018
```

The goal is:

```text
model learns transferable temporal patterns
across network-security datasets
```

Therefore future evaluation should distinguish:

```text
within-dataset performance
```

from:

```text
cross-day generalization
```

and eventually:

```text
cross-dataset generalization
```

These should not be mixed together.

---

# 69. WHAT HAS NOT BEEN DONE YET

Do NOT assume the following are complete:

```text
Final GRU/LSTM
Live traffic ingestion
Live network prediction
CTU-13 integration
IoT-23 integration
Final multi-dataset training
Production deployment
Actual autonomous blocking
Final dashboard
Final memory/RAG system
Final simulation engine
```

These are future stages.

---

# 70. WHAT CLAUDE CODE SHOULD DO FIRST

When taking over the repository:

### Step 1

Inspect the current repository.

Do not rewrite anything immediately.

Check:

```bash
pwd
find src -maxdepth 2 -type f
find configuration -maxdepth 2 -type f
find data/processed -maxdepth 1 -type f
```

Also inspect:

```text
src/forecasting_features.py
src/forecasting_leave_one_day_out.py
configuration/dataset_config.py
```

---

### Step 2

Verify the current forecasting files.

Confirm:

```text
10 forecasting datasets
4732 total rows
38 columns per current forecasting file
28 lag features
```

---

### Step 3

Do NOT regenerate Phase 1 unnecessarily.

The temporal datasets are already validated.

---

### Step 4

Run the autocorrelation analysis.

Do not modify the forecasting pipeline yet.

Produce a table similar to:

```text
dataset | lag1_corr | lag2_corr | lag3_corr | lag5_corr
```

---

### Step 5

Analyze why persistence is so strong.

Look at:

```text
attack_rate distribution
attack_rate autocorrelation
attack_rate change distribution
large sudden transitions
```

especially on:

```text
Friday-16-02-2018
Wednesday-21-02-2018
Friday-02-03-2018
```

because these contain substantially different behavior.

---

### Step 6

Only after that decide whether to:

```text
A. predict absolute attack_rate
B. predict Δattack_rate
C. use another target formulation
D. move to GRU/LSTM
```

---

# 71. DO NOT MAKE THIS COMMON MISTAKE

Do not say:

> "RF failed, therefore we need LSTM."

That is not enough evidence.

The correct reasoning is:

```text
RF failed to outperform persistence
        ↓
Understand target temporal structure
        ↓
Understand why persistence works
        ↓
Choose better representation/target
        ↓
Test stronger temporal model
```

---

# 72. THE BIGGER AEGIS VISION

Eventually the whole system should look like:

```text
                   LIVE NETWORK
                        │
                        ▼
                 ┌─────────────┐
                 │   OBSERVE   │
                 └──────┬──────┘
                        │
                        ▼
             Temporal Network State
                        │
                        ▼
                 ┌─────────────┐
                 │   PREDICT   │
                 └──────┬──────┘
                        │
                        ▼
               Future trajectory
                        │
                        ▼
                 ┌─────────────┐
                 │   EXPLAIN   │
                 └──────┬──────┘
                        │
                        ▼
            Evidence / feature signals
                        │
                        ▼
                ┌──────────────┐
                │ INVESTIGATE  │
                └──────┬───────┘
                       │
              Historical memory
                       │
                       ▼
                 ┌─────────────┐
                 │  SIMULATE   │
                 └──────┬──────┘
                        │
               Hypothetical action
                        │
                        ▼
                 ┌─────────────┐
                 │   DECIDE    │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   DEFEND    │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   VERIFY    │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  REMEMBER   │
                 └─────────────┘
```

The current project is still building the foundation of this system.

---

# 73. THE MOST IMPORTANT CONTEXT TO REMEMBER

If you remember only the following, remember these:

### AEGIS is:

```text
Predictive cyber defense.
```

### Current data:

```text
10 CIC-IDS2018 datasets.
```

### Phase 1:

```text
COMPLETE
```

### Phase 1 result:

```text
10/10 datasets passed all defined structural validation checks.
```

### Temporal output:

```text
7008 continuous rows
4966 observed
2042 unobserved
```

### Forecasting rows:

```text
4732
```

### Current features:

```text
28 lag features
```

### Current baseline:

```text
Persistence
```

### Current ML model:

```text
Random Forest
```

### Current RF result:

```text
Mean MAE = 0.054574
```

### Persistence:

```text
Mean MAE = 0.027163
```

### Therefore:

```text
Current RF does NOT beat persistence.
```

### Current scientific question:

```text
Why is persistence so strong,
and what temporal representation/target
will allow AEGIS to learn meaningful future behavior?
```

### Immediate next step:

```text
Temporal autocorrelation analysis.
```

### Eventual model:

```text
GRU/LSTM or another appropriate temporal model.
```

### Eventual goal:

```text
Offline research prototype
        ↓
multi-dataset forecasting
        ↓
live telemetry
        ↓
risk/evidence
        ↓
simulation
        ↓
defense
        ↓
verification
        ↓
memory
        ↓
complete AEGIS cyber-defense platform
```

---

# 74. FINAL INSTRUCTION TO CLAUDE CODE

You are taking over from another AI that has already worked extensively on this project.

Do not respond by giving a generic explanation of how to build a cybersecurity project.

You need to continue the existing implementation.

First inspect the repository and verify that the current files match this handoff.

Then report:

```text
1. What currently exists
2. What is confirmed complete
3. What is currently failing/underperforming
4. What the next experiment should be
5. Exactly which file you intend to modify
```

Do NOT modify code until the current state has been verified.

Do NOT restart Phase 1.

Do NOT introduce Nemotron.

Do NOT introduce Nebius Token Factory.

Do NOT redesign the architecture.

Do NOT fabricate model performance.

Do NOT cross temporal gaps.

Do NOT random-split the time series.

Do NOT claim live prediction.

Do NOT claim exact attacker timing.

The immediate objective is:

```text
UNDERSTAND WHY PERSISTENCE BEATS THE CURRENT RF
        ↓
ANALYZE TEMPORAL STRUCTURE
        ↓
DESIGN A BETTER FORECASTING FORMULATION
        ↓
THEN MOVE TOWARD GRU/LSTM
```

Continue from this exact state.
