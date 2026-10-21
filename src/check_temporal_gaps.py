import pandas as pd

INPUT_PATH = (
    "data/processed/"
    "Friday-02-03-2018_temporal.csv"
)

def check_temporal_gaps():
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(df["time_window"])

    expected = pd.date_range(
        start=df["time_window"].min(),
        end=df["time_window"].max(),
        freq="1min"
    )

    actual = pd.DatetimeIndex(df["time_window"])

    missing = expected.difference(actual)

    print("--- TEMPORAL GAP SUMMARY ---")
    print(f"Expected windows: {len(expected)}")
    print(f"Actual windows:   {len(actual)}")
    print(f"Missing windows:  {len(missing)}")

    if len(missing) == 0:
        print("\nNo temporal gaps found.")
        return

    # Group consecutive missing minutes into gap periods
    missing_series = pd.Series(missing)

    gap_id = (
        missing_series.diff()
        .dt.total_seconds()
        .ne(60)
        .cumsum()
    )

    gaps = (
        missing_series
        .groupby(gap_id)
        .agg(["min", "max", "count"])
        .reset_index(drop=True)
    )

    print("\n--- GAP PERIODS ---")
    print(gaps.to_string(index=False))

if __name__ == "__main__":
    check_temporal_gaps()