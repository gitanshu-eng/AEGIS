"""
Adapter: CIC-BCCC-NRC TabularIoTAttack-2024
S3 path: s3://aegis-cic-training-2026-model.v1/datasets/tabular-iot-attack-2024/raw/
Schema : 85 columns, Label col = binary int (0=benign,1=attack), Attack Name col present
TS     : Timestamp — "06/09/2023 04:11:37 PM" — dayfirst=False, format=mixed
Flows  : flow_duration = Flow Duration
         flow_bytes    = Total Length of Fwd Packet + Total Length of Bwd Packet
         flow_packets  = Total Fwd Packet + Total Bwd packets
"""

from .base_adapter import BaseAdapter
import pandas as pd

class CICBCCCTabularIoT2024Adapter(BaseAdapter):

    TIMESTAMP_COL  = "Timestamp"
    LABEL_COL      = "Label"          # binary int, use directly
    DURATION_COL   = "Flow Duration"
    FWD_BYTES_COL  = "Total Length of Fwd Packet"
    BWD_BYTES_COL  = "Total Length of Bwd Packet"
    FWD_PKTS_COL   = "Total Fwd Packet"
    BWD_PKTS_COL   = "Total Bwd packets"

    def parse_timestamp(self, df: pd.DataFrame) -> pd.Series:
        return pd.to_datetime(df[self.TIMESTAMP_COL], format="mixed", dayfirst=False)

    def get_label(self, df: pd.DataFrame) -> pd.Series:
        return df[self.LABEL_COL].astype(int)

    def get_flow_duration(self, df: pd.DataFrame) -> pd.Series:
        return pd.to_numeric(df[self.DURATION_COL], errors="coerce").fillna(0.0)

    def get_flow_bytes(self, df: pd.DataFrame) -> pd.Series:
        fwd = pd.to_numeric(df[self.FWD_BYTES_COL], errors="coerce").fillna(0.0)
        bwd = pd.to_numeric(df[self.BWD_BYTES_COL], errors="coerce").fillna(0.0)
        return fwd + bwd

    def get_flow_packets(self, df: pd.DataFrame) -> pd.Series:
        fwd = pd.to_numeric(df[self.FWD_PKTS_COL], errors="coerce").fillna(0.0)
        bwd = pd.to_numeric(df[self.BWD_PKTS_COL], errors="coerce").fillna(0.0)
        return fwd + bwd
