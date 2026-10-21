import pandas as pd

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_predictions.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"


def final_phase2_check():

    print("--- AEGIS FINAL PHASE 2 CHECK ---")

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

    no_missing_values = (
        df[required_columns]
        .isna()
        .sum()
        .sum() == 0
    )

    # 3. Timestamp validation

    print("\n--- TIMESTAMP VALIDATION ---")

    invalid_timestamps = (
        df["time_window"]
        .isna()
        .sum()
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

    # 4. Prediction validation

    print("\n--- PREDICTION VALIDATION ---")

    print(
        f"Actual attack rate range: "
        f"{df['attack_rate'].min():.6f} "
        f"to "
        f"{df['attack_rate'].max():.6f}"
    )

    print(
        f"Predicted attack rate range: "
        f"{df['predicted_attack_rate'].min():.6f} "
        f"to "
        f"{df['predicted_attack_rate'].max():.6f}"
    )

    print(
        f"Prediction error range: "
        f"{df['prediction_error'].min():.6f} "
        f"to "
        f"{df['prediction_error'].max():.6f}"
    )

    # 5. Prediction error consistency

    calculated_error = (
        df["attack_rate"]
        - df["predicted_attack_rate"]
    )

    error_consistent = (
        calculated_error
        .round(10)
        .equals(
            df["prediction_error"]
            .round(10)
        )
    )

    print(
        f"Prediction errors consistent: "
        f"{error_consistent}"
    )

    # 6. Segment validation

    print("\n--- SEGMENT VALIDATION ---")

    print(
        f"Unique segments: "
        f"{df['segment_id'].nunique()}"
    )

    print(
        f"Missing segment IDs: "
        f"{df['segment_id'].isna().sum()}"
    )

    # 7. Final status

    phase2_valid = (
        all_columns_present
        and no_missing_values
        and invalid_timestamps == 0
        and sorted_timestamps
        and error_consistent
        and df["segment_id"].isna().sum() == 0
    )

    print("\n--- PHASE 2 STATUS ---")

    if phase2_valid:
        print("PHASE 2: READY FOR PHASE 3")
    else:
        print("PHASE 2: VALIDATION FAILED")


if __name__ == "__main__":
    final_phase2_check()