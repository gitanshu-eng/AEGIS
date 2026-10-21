from pathlib import Path

import pandas as pd

from configuration.dataset_config import INTERIM_DATA_DIR


def verify_file(file_path):
    print(f"\n{'=' * 60}")
    print(f"FILE: {file_path.name}")
    print(f"{'=' * 60}")

    df = pd.read_csv(file_path, low_memory=False)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\n--- MISSING VALUES ---")
    missing = df.isna().sum()
    missing = missing[missing > 0]

    if missing.empty:
        print("No missing values")
    else:
        print(missing)

    print("\n--- DUPLICATES ---")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\n--- TIMESTAMP ---")
    timestamps = pd.to_datetime(
        df["Timestamp"],
        errors="coerce"
    )

    print(f"Invalid timestamps: {timestamps.isna().sum()}")
    print(f"Start: {timestamps.min()}")
    print(f"End:   {timestamps.max()}")

    print("\n--- LABELS ---")
    print(df["Label"].value_counts().head(15))

    return df


def main():
    interim_dir = Path(INTERIM_DATA_DIR)

    cleaned_files = sorted(
        interim_dir.glob("*_cleaned.csv")
    )

    print("--- AEGIS CLEANED DATA VERIFICATION ---")
    print(f"Cleaned files found: {len(cleaned_files)}")

    for file_path in cleaned_files:
        verify_file(file_path)


if __name__ == "__main__":
    main()