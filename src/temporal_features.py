import pandas as pd

from configuration.dataset_config import (
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    LABEL_COLUMN,
    TIMESTAMP_COLUMN,
    TEMPORAL_FREQUENCY,
    CLEANED_FILE,
)

INPUT_FILE = CLEANED_FILE

OUTPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_temporal.csv"
)

INPUT_PATH = (
    f"{INTERIM_DATA_DIR}/{INPUT_FILE}"
)

OUTPUT_PATH = (
    f"{PROCESSED_DATA_DIR}/{OUTPUT_FILE}"
)


def create_temporal_dataset():

    print("Loading cleaned dataset...")

    df = pd.read_csv(INPUT_PATH)

    # Convert timestamp
    df[TIMESTAMP_COLUMN] = pd.to_datetime(
        df[TIMESTAMP_COLUMN],
        errors="coerce"
    )

    # Binary attack indicator
    df["is_attack"] = (
        df[LABEL_COLUMN]
        .str.upper()
        .ne("BENIGN")
        .astype(int)
    )

    # Create time windows
    df["time_window"] = (
        df[TIMESTAMP_COLUMN]
        .dt.floor(TEMPORAL_FREQUENCY)
    )

    # Aggregate network activity
    temporal = (
        df.groupby("time_window")
        .agg(
            total_flows=(LABEL_COLUMN, "size"),

            benign_flows=(
                LABEL_COLUMN,
                lambda x:
                (x.str.upper() == "BENIGN").sum()
            ),

            attack_flows=(
                "is_attack",
                "sum"
            ),

            avg_flow_duration=(
                "Flow Duration",
                "mean"
            ),

            avg_flow_bytes=(
                "TotLen Fwd Pkts",
                "mean"
            ),

            avg_flow_packets=(
                "Tot Fwd Pkts",
                "mean"
            ),
        )
        .reset_index()
    )

    # Attack proportion
    temporal["attack_rate"] = (
        temporal["attack_flows"]
        / temporal["total_flows"]
    )

    # Sort chronologically
    temporal = (
        temporal
        .sort_values("time_window")
        .reset_index(drop=True)
    )

    # Save temporal dataset
    temporal.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n--- TEMPORAL DATASET CREATED ---")
    print(f"Original flows: {len(df)}")
    print(f"Time windows: {len(temporal)}")
    print(f"Columns: {len(temporal.columns)}")

    print("\nSample:")

    print(
        temporal.head(10)
        .to_string(index=False)
    )

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    create_temporal_dataset()