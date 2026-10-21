from pathlib import Path

import pandas as pd

from configuration.dataset_config import INTERIM_DATA_DIR


def inspect_file(file_name):
    path = Path(INTERIM_DATA_DIR) / file_name

    print(f"\n{'=' * 70}")
    print(f"FILE: {file_name}")
    print(f"{'=' * 70}")

    df = pd.read_csv(
        path,
        low_memory=False
    )

    # Convert timestamps only for inspection.
    timestamps = pd.to_datetime(
        df["Timestamp"],
        errors="coerce"
    )

    # --------------------------------------------------
    # 1. INVALID / MISSING TIMESTAMPS
    # --------------------------------------------------

    bad_timestamp = df[
        timestamps.isna()
    ]

    if not bad_timestamp.empty:
        print("\n--- INVALID / MISSING TIMESTAMP ROWS ---")

        print(
            bad_timestamp[
                ["Timestamp", "Label"]
            ].to_string(index=True)
        )

    else:
        print("\n--- INVALID / MISSING TIMESTAMP ROWS ---")
        print("None")

    # --------------------------------------------------
    # 2. SUSPICIOUSLY OLD TIMESTAMPS
    # --------------------------------------------------

    suspicious = df[
        timestamps < pd.Timestamp("2018-01-01")
    ]

    print("\n--- SUSPICIOUS OLD TIMESTAMP ROWS ---")

    if not suspicious.empty:

        print(
            suspicious.head(20)[
                ["Timestamp", "Label"]
            ].to_string(index=True)
        )

    else:
        print("None")

    # --------------------------------------------------
    # 3. SUSPICIOUS TIMESTAMP COUNT
    # --------------------------------------------------

    print(
        f"\nSuspicious timestamp count: "
        f"{len(suspicious)}"
    )

    # --------------------------------------------------
    # 4. TIMESTAMP RANGE
    # --------------------------------------------------

    valid_timestamps = timestamps.dropna()

    print("\n--- VALID TIMESTAMP RANGE ---")

    if not valid_timestamps.empty:
        print(
            f"Start: {valid_timestamps.min()}"
        )

        print(
            f"End:   {valid_timestamps.max()}"
        )

    else:
        print("No valid timestamps found")


def main():

    inspect_file(
        "Thursday-01-03-2018_cleaned.csv"
    )

    inspect_file(
        "Wednesday-14-02-2018_cleaned.csv"
    )


if __name__ == "__main__":
    main()