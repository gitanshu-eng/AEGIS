"""
AEGIS — CIC IoT-DIAD 2024 Dataset Adapter
Labels are derived from filename (Label column contains NeedManualLabel throughout).
Timestamp format: DD/MM/YYYY HH:MM:SS AM/PM (dayfirst=True, 12h clock).
DoS-TCP_Flood files are near-empty and must be skipped before calling this adapter.
"""

import re
import numpy as np
import pandas as pd
from src.adapters.base_adapter import BaseAdapter


class CICIoTDIAD2024Adapter(BaseAdapter):
    DATASET_NAME = "CIC-IoT-DIAD-2024"

    TIMESTAMP_COLUMN     = "Timestamp"
    LABEL_COLUMN         = "Label"
    FLOW_DURATION_COLUMN = "Flow Duration"
    FLOW_BYTES_COLUMN    = "Total Length of Fwd Packet"
    FLOW_PACKETS_COLUMN  = "Total Fwd Packet"

    VALID_TIMESTAMP_START = pd.Timestamp("2022-01-01")
    SKIP_PATTERN          = re.compile(r"^DoS-TCP_Flood", re.IGNORECASE)

    @staticmethod
    def label_from_filename(filename: str) -> str:
        """
        Derives the attack/benign label from the filename stem.
        BenignTraffic* -> 'Benign'
        DDoS-ACK_Fragmentation3 -> 'DDoS-ACK_Fragmentation'
        Strips trailing digits and numberic suffixes.
        """
        stem = filename.replace(".pcap_Flow.csv", "").replace(".csv", "")
        # Strip trailing digits (e.g. DDoS-ICMP_Flood12 -> DDoS-ICMP_Flood)
        stem = re.sub(r"\d+$", "", stem).rstrip("-_")
        if stem.lower().startswith("benign"):
            return "Benign"
        return stem

    @staticmethod
    def should_skip(filename: str) -> bool:
        """Returns True for near-empty DoS-TCP_Flood files."""
        return bool(CICIoTDIAD2024Adapter.SKIP_PATTERN.match(filename))

    def load(self, input_path: str) -> pd.DataFrame:
        df = pd.read_csv(input_path, low_memory=False)
        df.columns = df.columns.str.strip()
        return df

    def clean_raw(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
        df = df.copy()
        df.columns = df.columns.str.strip()

        # Parse timestamps
        parsed = pd.to_datetime(
            df[self.TIMESTAMP_COLUMN],
            format="mixed",
            dayfirst=True,
            errors="coerce"
        )

        invalid = parsed.isna() | (parsed < self.VALID_TIMESTAMP_START)
        invalid_count = int(invalid.sum())

        if invalid_count > 0:
            df = df[~invalid].copy()
            parsed = parsed[~invalid]

        # Replace inf values
        df = df.replace([np.inf, -np.inf], np.nan)

        missing_count = int(
            df[[self.FLOW_DURATION_COLUMN,
                self.FLOW_BYTES_COLUMN,
                self.FLOW_PACKETS_COLUMN]]
            .isna().any(axis=1).sum()
        )

        df[self.FLOW_DURATION_COLUMN] = df[self.FLOW_DURATION_COLUMN].fillna(0)
        df[self.FLOW_BYTES_COLUMN]    = df[self.FLOW_BYTES_COLUMN].fillna(0)
        df[self.FLOW_PACKETS_COLUMN]  = df[self.FLOW_PACKETS_COLUMN].fillna(0)

        df["_parsed_ts"] = parsed.values
        return df, missing_count, invalid_count

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.str.strip()

        if "_parsed_ts" in df.columns:
            df["timestamp"] = df["_parsed_ts"]
        else:
            df["timestamp"] = pd.to_datetime(
                df[self.TIMESTAMP_COLUMN],
                format="mixed",
                dayfirst=True,
                errors="coerce"
            )

        # Label is set externally from filename — preserve if already set,
        # otherwise fall back to raw Label column
        if "label" not in df.columns:
            df["label"] = df[self.LABEL_COLUMN].astype(str).str.strip()

        df["flow_duration"] = pd.to_numeric(
            df[self.FLOW_DURATION_COLUMN], errors="coerce").fillna(0.0)
        df["flow_bytes"] = pd.to_numeric(
            df[self.FLOW_BYTES_COLUMN], errors="coerce").fillna(0.0)
        df["flow_packets"] = pd.to_numeric(
            df[self.FLOW_PACKETS_COLUMN], errors="coerce").fillna(0.0)

        return df[self.get_common_columns()]

    def is_attack(self, label: str) -> bool:
        return str(label).strip().lower() != "benign"
