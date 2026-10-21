from pathlib import Path

from configuration.dataset_config import RAW_DATA_DIR


def scan_dataset():
    data_dir = Path(RAW_DATA_DIR)

    csv_files = sorted(data_dir.glob("*.csv"))

    print("--- AEGIS DATASET INVENTORY ---")
    print(f"Directory: {data_dir}")
    print(f"CSV files found: {len(csv_files)}")

    print("\n--- FILES ---")

    for file in csv_files:
        size_mb = file.stat().st_size / (1024 * 1024)

        print(
            f"{file.name} | "
            f"{size_mb:.2f} MB"
        )


if __name__ == "__main__":
    scan_dataset()