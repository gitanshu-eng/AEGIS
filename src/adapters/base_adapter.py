"""
AEGIS — Base Dataset Adapter Interface
Standardized interface for raw flow dataset adapters.
"""

from abc import ABC, abstractmethod
import pandas as pd


class BaseAdapter(ABC):
    DATASET_NAME: str = "BASE"

    TIMESTAMP_COLUMN: str = ""
    LABEL_COLUMN: str = ""
    FLOW_DURATION_COLUMN: str = ""
    FLOW_BYTES_COLUMN: str = ""
    FLOW_PACKETS_COLUMN: str = ""

    @abstractmethod
    def clean_raw(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
        """
        Cleans dataset-specific artifacts (e.g., invalid timestamps, nulls, inf values).
        Returns: (cleaned_df, missing_metric_count, invalid_timestamp_count)
        """
        pass

    @abstractmethod
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms dataset into AEGIS canonical flow columns:
        - timestamp (pd.to_datetime)
        - label (str)
        - flow_duration (float)
        - flow_bytes (float)
        - flow_packets (float)
        """
        pass

    def is_attack(self, label: str) -> bool:
        """Determines if a label represents an attack flow."""
        return str(label).strip().lower() != "benign"

    def get_common_columns(self) -> list[str]:
        """Returns the canonical AEGIS feature columns."""
        return [
            "timestamp",
            "label",
            "flow_duration",
            "flow_bytes",
            "flow_packets",
        ]
