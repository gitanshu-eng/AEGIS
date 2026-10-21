import pandas as pd

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_risk_signals.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"

OUTPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_risk.csv"
)

OUTPUT_PATH = f"{PROCESSED_DATA_DIR}/{OUTPUT_FILE}"


def calculate_risk_score(df):

    # Normalize the three signals to a 0–1 range.

    forecast_component = (
        df["forecast_signal"].clip(0, 1)
    )

    activity_component = (
        df["activity_signal"].clip(0, 1)
    )

    # Use the validation RMSE from Phase 2
    # as the reference scale for prediction error.
    validation_rmse = 0.148429

    error_component = (
        df["error_signal"] / validation_rmse
    ).clip(0, 1)

    # Weighted risk score
    #
    # Forecast signal : 45%
    # Activity signal : 40%
    # Error signal    : 15%

    df["risk_score"] = (
        (
            0.45 * forecast_component
            + 0.40 * activity_component
            + 0.15 * error_component
        )
        * 100
    )

    # Risk level

    df["risk_level"] = pd.cut(
        df["risk_score"],
        bins=[
            -1,
            30,
            60,
            80,
            100
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        ]
    )

    # Human-readable explanation

    def generate_reason(row):

        reasons = []

        if row["forecast_signal"] >= 0.40:
            reasons.append(
                "high predicted attack activity"
            )

        if row["activity_signal"] >= 0.40:
            reasons.append(
                "high observed attack activity"
            )

        if row["error_signal"] >= validation_rmse:
            reasons.append(
                "large forecast deviation"
            )

        if not reasons:
            reasons.append(
                "no dominant risk signal"
            )

        return "; ".join(reasons)

    df["risk_reason"] = df.apply(
        generate_reason,
        axis=1
    )

    return df


def build_risk_engine():

    print("--- AEGIS CYBER RISK ENGINE ---")

    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    print(f"Input rows: {len(df)}")

    df = calculate_risk_score(df)

    output_columns = [
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
        "segment_id",
    ]

    df[output_columns].to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n--- RISK ENGINE COMPLETE ---")

    print(
        f"Risk score minimum: "
        f"{df['risk_score'].min():.2f}"
    )

    print(
        f"Risk score maximum: "
        f"{df['risk_score'].max():.2f}"
    )

    print("\nRisk levels:")

    print(
        df["risk_level"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nHighest risk windows:")

    highest_risk = (
        df.sort_values(
            "risk_score",
            ascending=False
        )
        .head(10)
    )

    print(
        highest_risk[
            [
                "time_window",
                "risk_score",
                "risk_level",
                "risk_reason"
            ]
        ].to_string(index=False)
    )

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_risk_engine()