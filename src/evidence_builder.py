import pandas as pd

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_risk.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"

OUTPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_evidence.csv"
)

OUTPUT_PATH = f"{PROCESSED_DATA_DIR}/{OUTPUT_FILE}"


def build_evidence():

    print("--- AEGIS EVIDENCE BUILDER ---")

    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    print(f"Input rows: {len(df)}")

    evidence_records = []

    for _, row in df.iterrows():

        evidence = []

        # Forecast evidence
        if row["forecast_signal"] >= 0.40:
            evidence.append(
                "Predicted attack activity is elevated"
            )

        # Observed activity evidence
        if row["activity_signal"] >= 0.40:
            evidence.append(
                "Observed attack activity is elevated"
            )

        # Forecast deviation evidence
        if row["error_signal"] >= 0.148429:
            evidence.append(
                "Prediction deviation is large"
            )

        # Default evidence
        if not evidence:
            evidence.append(
                "No dominant risk signal detected"
            )

        evidence_records.append(
            "; ".join(evidence)
        )

    df["evidence"] = evidence_records

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
        "evidence",
        "segment_id",
    ]

    df[output_columns].to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n--- EVIDENCE BUILD COMPLETE ---")

    print(
        f"Evidence records: {len(df)}"
    )

    print("\nSample evidence:")

    print(
        df[
            [
                "time_window",
                "risk_score",
                "risk_level",
                "evidence",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_evidence()