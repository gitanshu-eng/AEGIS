import pandas as pd

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_evidence.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"


def final_phase3_check():

    print("--- AEGIS FINAL PHASE 3 CHECK ---")

    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"],
        errors="coerce"
    )

    required_columns = [
        "time_window",
        "attack_rate",
        "predicted_attack_rate",
        "prediction_error",
        "forecast_signal",
        "activity_signal",
        "error_signal",
        "risk_score",
        "risk_level",
        "risk_reason",
        "evidence",
        "segment_id",
    ]

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # 1. Required columns

    print("\n--- REQUIRED COLUMNS ---")

    all_columns_present = True

    for column in required_columns:

        exists = column in df.columns

        print(
            f"{column}: "
            f"{'OK' if exists else 'MISSING'}"
        )

        if not exists:
            all_columns_present = False

    # 2. Missing values

    print("\n--- MISSING VALUES ---")

    print(
        df[required_columns]
        .isna()
        .sum()
        .to_string()
    )

    # 3. Risk score range

    print("\n--- RISK SCORE RANGE ---")

    print(
        f"Minimum: {df['risk_score'].min():.2f}"
    )

    print(
        f"Maximum: {df['risk_score'].max():.2f}"
    )

    score_range_valid = (
        df["risk_score"]
        .between(0, 100)
        .all()
    )

    print(
        f"0-100 range valid: {score_range_valid}"
    )

    # 4. Risk levels

    print("\n--- RISK LEVELS ---")

    valid_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    actual_levels = set(
        df["risk_level"]
        .dropna()
        .astype(str)
        .str.upper()
    )

    invalid_levels = (
        actual_levels - valid_levels
    )

    print(
        df["risk_level"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(
        f"Risk levels valid: "
        f"{len(invalid_levels) == 0}"
    )

    # 5. Timestamp validation

    print("\n--- TIMESTAMP VALIDATION ---")

    invalid_timestamps = (
        df["time_window"].isna().sum()
    )

    sorted_timestamps = (
        df["time_window"]
        .is_monotonic_increasing
    )

    print(
        f"Invalid timestamps: "
        f"{invalid_timestamps}"
    )

    print(
        f"Sorted chronologically: "
        f"{sorted_timestamps}"
    )

    # 6. Evidence validation

    print("\n--- EVIDENCE VALIDATION ---")

    empty_evidence = (
        df["evidence"]
        .fillna("")
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        f"Empty evidence records: "
        f"{empty_evidence}"
    )

    # 7. Risk reason validation

    empty_reasons = (
        df["risk_reason"]
        .fillna("")
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        f"Empty risk reasons: "
        f"{empty_reasons}"
    )

    # 8. Final status

    phase3_valid = (
        all_columns_present
        and df[required_columns]
        .isna()
        .sum()
        .sum() == 0
        and score_range_valid
        and len(invalid_levels) == 0
        and invalid_timestamps == 0
        and sorted_timestamps
        and empty_evidence == 0
        and empty_reasons == 0
    )

    print("\n--- PHASE 3 STATUS ---")

    if phase3_valid:
        print("PHASE 3: READY FOR PHASE 4")
    else:
        print("PHASE 3: VALIDATION FAILED")


if __name__ == "__main__":
    final_phase3_check()