import pandas as pd

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
    TIMESTAMP_COLUMN,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_temporal_continuous.csv"
)

OUTPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_forecasting.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"
OUTPUT_PATH = f"{PROCESSED_DATA_DIR}/{OUTPUT_FILE}"


def create_forecasting_features():

    print("--- AEGIS FORECASTING FEATURE CREATION ---")

    # 1. LOAD DATA
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
    df["time_window"]
)

    print(f"Input rows: {len(df)}")

    # 2. CREATE A CONTINUOUS-SEGMENT ID
    #
    # A new segment starts whenever:
    # - the current row is unobserved
    # - OR the previous observed timestamp is not exactly
    #   one minute before the current timestamp.

    observed = df["observed"].eq(1)

    time_diff = df["time_window"].diff()

    new_segment = (
        observed
        & (
            ~observed.shift(fill_value=False)
            | (time_diff != pd.Timedelta(minutes=1))
        )
    )

    df["segment_id"] = new_segment.cumsum()

    # 3. CREATE LAG FEATURES
    #
    # These represent recent attack-rate history.

    lag_windows = [1, 2, 3, 5]

    for lag in lag_windows:
        df[f"attack_rate_lag_{lag}"] = (
            df.groupby("segment_id")["attack_rate"]
            .shift(lag)
        )

    # 4. KEEP ONLY OBSERVED TARGET ROWS
    #
    # We cannot train on missing target values.

    df = df[df["observed"] == 1].copy()

    # 5. REMOVE ROWS WITHOUT COMPLETE LAG HISTORY
    feature_columns = [
        f"attack_rate_lag_{lag}"
        for lag in lag_windows
    ]

    before_drop = len(df)

    df = df.dropna(
        subset=feature_columns + ["attack_rate"]
    ).copy()

    rows_removed = before_drop - len(df)

    # 6. SAVE
    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # 7. REPORT
    print("\n--- FORECASTING FEATURES CREATED ---")
    print(f"Rows removed due to incomplete history: {rows_removed}")
    print(f"Final rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nForecasting features:")
    print(feature_columns)

    print("\nSample:")
    print(
        df[
            [
                "time_window",
                "attack_rate",
                *feature_columns,
                "segment_id",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    create_forecasting_features()