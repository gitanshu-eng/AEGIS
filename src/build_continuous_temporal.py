import pandas as pd

INPUT_PATH = (
    "data/processed/"
    "Friday-02-03-2018_temporal.csv"
)

OUTPUT_PATH = (
    "data/processed/"
    "Friday-02-03-2018_temporal_continuous.csv"
)


def build_continuous_temporal():
    print("Loading temporal dataset...")

    df = pd.read_csv(INPUT_PATH)
    df["time_window"] = pd.to_datetime(df["time_window"])

    # Create complete 1-minute timeline
    full_timeline = pd.date_range(
        start=df["time_window"].min(),
        end=df["time_window"].max(),
        freq="1min"
    )

    timeline = pd.DataFrame({
        "time_window": full_timeline
    })

    # Preserve observed data
    result = timeline.merge(
        df,
        on="time_window",
        how="left"
    )

    # Mark whether this minute was actually observed
    result["observed"] = result["total_flows"].notna().astype(int)

    result = result.sort_values(
        "time_window"
    ).reset_index(drop=True)

    result.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n--- CONTINUOUS TEMPORAL DATASET ---")
    print(f"Expected windows: {len(full_timeline)}")
    print(f"Final windows:    {len(result)}")
    print(
        f"Observed windows: "
        f"{result['observed'].sum()}"
    )
    print(
        f"Unobserved windows: "
        f"{(result['observed'] == 0).sum()}"
    )

    print("\n--- GAP SAMPLE ---")
    gap_sample = result[
        result["observed"] == 0
    ].head(5)

    print(gap_sample.to_string(index=False))

    print("\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_continuous_temporal()
    