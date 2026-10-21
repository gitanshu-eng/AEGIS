import pandas as pd

INPUT_PATH = (
    "data/processed/"
    "Friday-02-03-2018_temporal_continuous.csv"
)


def final_phase1_check():

    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    print("--- AEGIS PHASE 1 FINAL CHECK ---")

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")
    print(list(df.columns))

    print("\nObserved status:")
    print(df["observed"].value_counts())

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nAttack rate:")
    print(
        f"Minimum: {df['attack_rate'].min()}"
    )
    print(
        f"Maximum: {df['attack_rate'].max()}"
    )

    print("\nChronological order:")
    print(
        f"Sorted: "
        f"{df['time_window'].is_monotonic_increasing}"
    )

    print("\nTime range:")
    print(f"Start: {df['time_window'].min()}")
    print(f"End:   {df['time_window'].max()}")

    print("\nFirst observed rows:")
    print(
        df[df["observed"] == 1]
        .head(3)
        .to_string(index=False)
    )

    print("\nFirst unobserved rows:")
    print(
        df[df["observed"] == 0]
        .head(3)
        .to_string(index=False)
    )


if __name__ == "__main__":
    final_phase1_check()