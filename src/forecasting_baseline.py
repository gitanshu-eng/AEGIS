import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_forecasting.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"


def evaluate_baseline():

    print("--- AEGIS FORECASTING BASELINE ---")

    # Load forecasting dataset
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    # Chronological order
    df = df.sort_values(
        "time_window"
    ).reset_index(drop=True)

    # Same 70 / 15 / 15 split
    total_rows = len(df)

    train_end = int(total_rows * 0.70)
    validation_end = int(total_rows * 0.85)

    validation = df.iloc[
        train_end:validation_end
    ].copy()

    test = df.iloc[
        validation_end:
    ].copy()

    # Persistence prediction:
    # predict current attack rate using lag_1
    validation["prediction"] = (
        validation["attack_rate_lag_1"]
    )

    test["prediction"] = (
        test["attack_rate_lag_1"]
    )

    # Validation metrics
    validation_mae = mean_absolute_error(
        validation["attack_rate"],
        validation["prediction"]
    )

    validation_rmse = mean_squared_error(
        validation["attack_rate"],
        validation["prediction"]
    ) ** 0.5

    # Test metrics
    test_mae = mean_absolute_error(
        test["attack_rate"],
        test["prediction"]
    )

    test_rmse = mean_squared_error(
        test["attack_rate"],
        test["prediction"]
    ) ** 0.5

    print("\n--- VALIDATION BASELINE ---")
    print(f"MAE:  {validation_mae:.6f}")
    print(f"RMSE: {validation_rmse:.6f}")

    print("\n--- TEST BASELINE ---")
    print(f"MAE:  {test_mae:.6f}")
    print(f"RMSE: {test_rmse:.6f}")


if __name__ == "__main__":
    evaluate_baseline()
    