from pathlib import Path

import pandas as pd

from configuration.dataset_config import (
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
)


def clean_dataset(input_path):
    input_path = Path(input_path)

    output_name = input_path.name.replace(
        "_TrafficForML_CICFlowMeter.csv",
        "_cleaned.csv"
    )

    output_path = Path(INTERIM_DATA_DIR) / output_name

    print(f"\nLoading: {input_path.name}")

    df = pd.read_csv(
        input_path,
        low_memory=False
    )

    original_rows = len(df)

    print(f"Original rows: {original_rows}")

    # --------------------------------------------------
    # 1. REMOVE EMBEDDED HEADER ROWS
    # --------------------------------------------------

    header_rows = (
        df["Label"]
        .astype(str)
        .str.strip()
        .str.upper()
        == "LABEL"
    )

    header_rows_removed = header_rows.sum()

    df = df[~header_rows].copy()

    # --------------------------------------------------
    # 2. PARSE TIMESTAMP
    # --------------------------------------------------

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    # --------------------------------------------------
    # 3. REMOVE INVALID TIMESTAMPS
    # --------------------------------------------------

    invalid_timestamp = (
        df["Timestamp"].isna()
    )

    invalid_timestamp_removed = (
        invalid_timestamp.sum()
    )

    df = df[~invalid_timestamp].copy()

    # --------------------------------------------------
    # 4. REMOVE SUSPICIOUSLY OLD TIMESTAMPS
    # --------------------------------------------------

    suspicious_timestamp = (
        df["Timestamp"]
        < pd.Timestamp("2018-01-01")
    )

    suspicious_timestamp_removed = (
        suspicious_timestamp.sum()
    )

    df = df[~suspicious_timestamp].copy()

    # --------------------------------------------------
    # 5. REMOVE DUPLICATES
    # --------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates()

    duplicates_removed = (
        before_duplicates - len(df)
    )

    # --------------------------------------------------
    # 6. HANDLE MISSING FLOW BYTES
    # --------------------------------------------------

    missing_flow_bytes = (
        df["Flow Byts/s"].isna().sum()
    )

    df["Flow Byts/s"] = (
        df["Flow Byts/s"].fillna(0)
    )

    # --------------------------------------------------
    # 7. SORT CHRONOLOGICALLY
    # --------------------------------------------------

    df = (
        df.sort_values("Timestamp")
        .reset_index(drop=True)
    )

    # --------------------------------------------------
    # 8. SAVE
    # --------------------------------------------------

    df.to_csv(
        output_path,
        index=False
    )

    # --------------------------------------------------
    # REPORT
    # --------------------------------------------------

    print("--- CLEANING COMPLETE ---")

    print(
        f"Embedded headers removed: "
        f"{header_rows_removed}"
    )

    print(
        f"Invalid timestamps removed: "
        f"{invalid_timestamp_removed}"
    )

    print(
        f"Suspicious old timestamps removed: "
        f"{suspicious_timestamp_removed}"
    )

    print(
        f"Duplicates removed: "
        f"{duplicates_removed}"
    )

    print(
        f"Missing Flow Byts/s handled: "
        f"{missing_flow_bytes}"
    )

    print(
        f"Final rows: "
        f"{len(df)}"
    )

    print(
        f"Columns: "
        f"{len(df.columns)}"
    )

    print(
        f"Saved to: "
        f"{output_path}"
    )


def main():
    raw_dir = Path(RAW_DATA_DIR)

    csv_files = sorted(
        raw_dir.glob("*.csv")
    )

    print("--- AEGIS MULTI-FILE CLEANING ---")
    print(f"Files found: {len(csv_files)}")

    for csv_file in csv_files:
        clean_dataset(csv_file)


if __name__ == "__main__":
    main()