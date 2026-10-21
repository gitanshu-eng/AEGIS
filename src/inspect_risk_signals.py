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


def inspect_risk_signals():

    print("--- AEGIS RISK SIGNAL INSPECTION ---")

    # 1. LOAD PREDICTIONS
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    # 2. CREATE ABSOLUTE PREDICTION ERROR
    df["absolute_error"] = (
        df["prediction_error"].abs()
    )

    # 3. CREATE FORECAST CHANGE
    df["forecast_change"] = (
        df["predicted_attack_rate"]
        - df["attack_rate"]
    )

    # 4. BASIC INFORMATION
    print(f"Rows: {len(df)}")

    print("\n--- ATTACK RATE ---")

    print(
        df["attack_rate"]
        .describe()
        .to_string()
    )

    print("\n--- PREDICTED ATTACK RATE ---")

    print(
        df["predicted_attack_rate"]
        .describe()
        .to_string()
    )

    print("\n--- ABSOLUTE PREDICTION ERROR ---")

    print(
        df["absolute_error"]
        .describe()
        .to_string()
    )

    # 5. HIGH FORECAST VALUES
    print("\n--- HIGHEST PREDICTED ATTACK RATES ---")

    highest_forecasts = (
        df.sort_values(
            "predicted_attack_rate",
            ascending=False
        )
        .head(10)
    )

    print(
        highest_forecasts[
            [
                "time_window",
                "attack_rate",
                "predicted_attack_rate",
                "absolute_error",
            ]
        ].to_string(index=False)
    )

    # 6. HIGHEST ERRORS
    print("\n--- HIGHEST PREDICTION ERRORS ---")

    highest_errors = (
        df.sort_values(
            "absolute_error",
            ascending=False
        )
        .head(10)
    )

    print(
        highest_errors[
            [
                "time_window",
                "attack_rate",
                "predicted_attack_rate",
                "absolute_error",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    inspect_risk_signals()