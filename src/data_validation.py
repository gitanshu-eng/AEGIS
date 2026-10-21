import pandas as pd


# --------------------------------------------------
# AEGIS — Phase 1
# Data Validation
# --------------------------------------------------

DATA_PATH = "data/raw/CIC-IDS2018/Friday-02-03-2018_TrafficForML_CICFlowMeter.csv"


def load_sample():
    """Load a small sample of the raw dataset."""

    df = pd.read_csv(DATA_PATH, nrows=10_000)

    print("Dataset loaded successfully")
    print(f"Rows loaded: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


def validate_dataset(df):
    """Perform basic validation checks."""

    print("\n--- VALIDATION ---")

    # Missing values
    missing = df.isna().sum()
    print("\nMissing values:")
    print(missing[missing > 0])

    # Duplicate rows
    duplicates = df[df.duplicated(keep=False)]

    print(f"\nDuplicate rows: {df.duplicated().sum()}")

    if not duplicates.empty:
        print("\nSample duplicate rows:")
        print(duplicates.head(10).to_string(index=False))

    # Labels
    print("\nLabels:")
    print(df["Label"].value_counts())

    # Timestamp
    print("\nTimestamp:")
    print(df["Timestamp"].head())


if __name__ == "__main__":
    data = load_sample()
    validate_dataset(data)