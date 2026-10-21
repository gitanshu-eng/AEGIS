"""
AEGIS — CIC-IDS2018 Dataset Adapter
Handles whitespace stripping, strict timestamp format, and canonical flow mapping.
"""

import numpy as np
import pandas as pd
from src.adapters.base_adapter import BaseAdapter


class CICIDS2018Adapter(BaseAdapter):
    DATASET_NAME = "CIC-IDS2018"

    TIMESTAMP_COLUMN = "Timestamp"
    LABEL_COLUMN = "Label"
    FLOW_DURATION_COLUMN = "Flow Duration"
    FLOW_BYTES_COLUMN = "TotLen Fwd Pkts"       # <-- CONFIRM THIS
    FLOW_PACKETS_COLUMN = "Tot Bwd Pkts"     # <-- CONFIRM THIS

    VALID_TIMESTAMP_START = pd.Timestamp("2018-01-01")

    def load(self, input_path):
        df = pd.read_csv(input_path, low_memory=False, encoding="cp1252")
        df.columns = df.columns.str.strip()
        return df

    def clean_raw(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
        df = df.copy()
        df.columns = df.columns.str.strip()

        parsed_timestamps = pd.to_datetime(
            df[self.TIMESTAMP_COLUMN],
            format="%d/%m/%Y %H:%M:%S",
            errors="coerce"
        )

        invalid_old = (
            parsed_timestamps.isna()
            | (parsed_timestamps < self.VALID_TIMESTAMP_START)
        )
        invalid_timestamp_count = int(invalid_old.sum())

        if invalid_timestamp_count > 0:
            df = df[~invalid_old].copy()
            parsed_timestamps = parsed_timestamps[~invalid_old]

        df = df.replace([np.inf, -np.inf], np.nan)

        missing_metric_count = int(
            df[[self.FLOW_DURATION_COLUMN,
                self.FLOW_BYTES_COLUMN,
                self.FLOW_PACKETS_COLUMN]].isna().any(axis=1).sum()
        )

        df[self.FLOW_DURATION_COLUMN] = df[self.FLOW_DURATION_COLUMN].fillna(0)
        df[self.FLOW_BYTES_COLUMN] = df[self.FLOW_BYTES_COLUMN].fillna(0)
        df[self.FLOW_PACKETS_COLUMN] = df[self.FLOW_PACKETS_COLUMN].fillna(0)

        df["_parsed_ts"] = parsed_timestamps
        return df, missing_metric_count, invalid_timestamp_count

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.str.strip()

        if "_parsed_ts" in df.columns:
            df["timestamp"] = df["_parsed_ts"]
        else:
            df["timestamp"] = pd.to_datetime(
                df[self.TIMESTAMP_COLUMN],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            )

        df["label"] = df[self.LABEL_COLUMN].astype(str).str.strip()
        df["flow_duration"] = pd.to_numeric(
            df[self.FLOW_DURATION_COLUMN], errors="coerce").fillna(0.0)
        df["flow_bytes"] = pd.to_numeric(
            df[self.FLOW_BYTES_COLUMN], errors="coerce").fillna(0.0)
        df["flow_packets"] = pd.to_numeric(
            df[self.FLOW_PACKETS_COLUMN], errors="coerce").fillna(0.0)

        return df[self.get_common_columns()]
