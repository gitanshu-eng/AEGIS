import pandas as pd

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_forecasting.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"


def create_forecasting_split():

    print("--- AEGIS FORECASTING DATA SPLIT ---")

    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    # Keep chronological order.
    df = df.sort_values(
        "time_window"
    ).reset_index(drop=True)

    total_rows = len(df)

    train_end = int(total_rows * 0.70)
    validation_end = int(total_rows * 0.85)

    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:validation_end].copy()
    test = df.iloc[validation_end:].copy()

    print(f"Total rows: {total_rows}")

    print("\n--- TRAIN ---")
    print(f"Rows: {len(train)}")
    print(f"Start: {train['time_window'].min()}")
    print(f"End:   {train['time_window'].max()}")

    print("\n--- VALIDATION ---")
    print(f"Rows: {len(validation)}")
    print(f"Start: {validation['time_window'].min()}")
    print(f"End:   {validation['time_window'].max()}")

    print("\n--- TEST ---")
    print(f"Rows: {len(test)}")
    print(f"Start: {test['time_window'].min()}")
    print(f"End:   {test['time_window'].max()}")


if __name__ == "__main__":
    create_forecasting_split()