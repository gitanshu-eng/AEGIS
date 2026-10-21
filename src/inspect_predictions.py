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


def inspect_predictions():

    print("--- AEGIS PREDICTION INSPECTION ---")

    # 1. LOAD PREDICTIONS
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # 2. CHECK REQUIRED COLUMNS
    required_columns = [
        "time_window",
        "attack_rate",
        "predicted_attack_rate",
        "prediction_error",
        "segment_id",
    ]

    print("\nRequired columns:")

    for column in required_columns:
        print(
            f"{column}: "
            f"{'OK' if column in df.columns else 'MISSING'}"
        )

    # 3. CHECK MISSING VALUES
    print("\nMissing values:")

    print(
        df[required_columns]
        .isna()
        .sum()
        .to_string()
    )

    # 4. CHECK PREDICTION RANGE
    print("\nAttack rate range:")
    print(
        f"Actual minimum:    {df['attack_rate'].min():.6f}"
    )
    print(
        f"Actual maximum:    {df['attack_rate'].max():.6f}"
    )

    print("\nPrediction range:")
    print(
        f"Predicted minimum: {df['predicted_attack_rate'].min():.6f}"
    )
    print(
        f"Predicted maximum: {df['predicted_attack_rate'].max():.6f}"
    )

    # 5. CHECK TIMESTAMP ORDER
    sorted_check = df["time_window"].is_monotonic_increasing

    print("\nTimestamp sorted:")
    print(sorted_check)

    # 6. SAMPLE PREDICTIONS
    print("\nSample predictions:")

    print(
        df[
            required_columns
        ].head(10).to_string(index=False)
    )

    # 7. LARGEST ERRORS
    print("\nLargest prediction errors:")

    largest_errors = (
        df.assign(
            absolute_error=df["prediction_error"].abs()
        )
        .sort_values(
            "absolute_error",
            ascending=False
        )
        .head(10)
    )

    print(
        largest_errors[
            [
                "time_window",
                "attack_rate",
                "predicted_attack_rate",
                "prediction_error",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    inspect_predictions()