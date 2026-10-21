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


def create_risk_signals():

    print("--- AEGIS RISK SIGNAL ENGINE ---")

    # 1. LOAD PREDICTIONS
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    # 2. ABSOLUTE PREDICTION ERROR
    df["absolute_error"] = (
        df["prediction_error"].abs()
    )

    # 3. FORECAST SIGNAL
    #
    # Higher predicted attack rate
    # means stronger forecast signal.

    df["forecast_signal"] = (
        df["predicted_attack_rate"]
    )

    # 4. ACTUAL ACTIVITY SIGNAL
    #
    # Higher observed attack rate
    # means stronger current activity.

    df["activity_signal"] = (
        df["attack_rate"]
    )

    # 5. ERROR SIGNAL
    #
    # Larger difference between
    # prediction and reality means
    # greater forecast uncertainty.

    df["error_signal"] = (
        df["absolute_error"]
    )

    # 6. DISPLAY SUMMARY
    print(f"Rows: {len(df)}")

    print("\nSignal statistics:")

    print(
        df[
            [
                "forecast_signal",
                "activity_signal",
                "error_signal",
            ]
        ]
        .describe()
        .to_string()
    )

    # 7. SHOW STRONGEST FORECAST SIGNALS
    print("\n--- STRONGEST FORECAST SIGNALS ---")

    strongest = (
        df.sort_values(
            "forecast_signal",
            ascending=False
        )
        .head(10)
    )

    print(
        strongest[
            [
                "time_window",
                "forecast_signal",
                "activity_signal",
                "error_signal",
            ]
        ].to_string(index=False)
    )

    # 8. SAVE SIGNAL DATA
    output_file = CLEANED_FILE.replace(
        "_cleaned.csv",
        "_risk_signals.csv"
    )

    output_path = (
        f"{PROCESSED_DATA_DIR}/{output_file}"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print("\nRisk signals saved to:")
    print(output_path)


if __name__ == "__main__":
    create_risk_signals()