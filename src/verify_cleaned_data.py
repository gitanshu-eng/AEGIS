import pandas as pd


# --------------------------------------------------
# AEGIS — Phase 1
# Cleaned Data Verification
# --------------------------------------------------

DATA_PATH = (
    "data/interim/"
    "Friday-02-03-2018_cleaned.csv"
)


def verify_dataset():

    print("Loading cleaned dataset...")

    df = pd.read_csv(DATA_PATH)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\n--- MISSING VALUES ---")
    missing = df.isna().sum()
    print(missing[missing > 0])

    print("\n--- DUPLICATES ---")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\n--- TIMESTAMP ---")
    print(f"Data type: {df['Timestamp'].dtype}")
    print(df["Timestamp"].head())

    print("\n--- LABELS ---")
    print(df["Label"].value_counts())

    print("\n--- TIME RANGE ---")
    print(f"Start: {df['Timestamp'].min()}")
    print(f"End:   {df['Timestamp'].max()}")


if __name__ == "__main__":
    verify_dataset()