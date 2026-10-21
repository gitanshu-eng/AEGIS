"""
AEGIS Live Replay Engine
Replays pre-computed temporal CSV data row-by-row to simulate live telemetry.
Data source: historical batch CSVs (Phase 1 outputs).
Clearly labeled as REPLAYED -- not genuine packet capture.
"""

import os
import threading
import pandas as pd
import numpy as np
from typing import Dict, Any
from src.inference import predict as infer_predict

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")


def _safe_float(v):
    if v is None:
        return None
    try:
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return None


class DatasetReplay:
    def __init__(self, dataset: str):
        self.dataset = dataset
        self.cursor  = 0
        self.rows    = []
        self.loaded  = False
        self.error   = None
        self._lock   = threading.Lock()
        self._load()

    def _load(self):
        path = os.path.join(DATA_DIR, "final_forecasts", f"{self.dataset}_final_forecast.csv")
        if not os.path.exists(path):
            self.error = f"Forecast file not found: {path}"
            return
        try:
            df = pd.read_csv(path)
            if "time_window" in df.columns:
                df = df.rename(columns={"time_window": "timestamp"})
            self.rows   = df.to_dict(orient="records")
            self.loaded = True
        except Exception as e:
            self.error = str(e)

    def tick(self) -> Dict[str, Any]:
        with self._lock:
            if not self.loaded or not self.rows:
                return {"error": self.error or "No data loaded", "telemetry_mode": "REPLAYED"}
            row = self.rows[self.cursor]
            self.cursor = (self.cursor + 1) % len(self.rows)
            observed = bool(row.get("observed", 1))
            infer = infer_predict(row) if observed else {}
            return {
                "telemetry_mode":      "REPLAYED",
                "data_source":         "historical_batch_csv",
                "dataset":             self.dataset,
                "cursor_position":     self.cursor,
                "total_rows":          len(self.rows),
                "progress_pct":        round((self.cursor / len(self.rows)) * 100, 1),
                "timestamp":           str(row.get("timestamp", "")),
                "total_flows":         int(row.get("total_flows", 0) or 0),
                "benign_flows":        int(row.get("benign_flows", 0) or 0),
                "attack_flows":        int(row.get("attack_flows", 0) or 0),
                "attack_rate":         _safe_float(row.get("attack_rate", 0)) or 0.0,
                "escalation_forecast": infer.get("p_escalation") or _safe_float(row.get("p_escalation", 0)) or 0.0,
                "risk_score":          infer.get("risk_score") or _safe_float(row.get("risk_score", 0)) or 0.0,
                "inference_mode":      infer.get("inference_mode", "REPLAYED"),
                "network_state":       "OBSERVED" if observed else "UNOBSERVED",
            }

    def reset(self):
        with self._lock:
            self.cursor = 0

    def seek(self, position: int):
        with self._lock:
            if self.rows:
                self.cursor = max(0, min(position, len(self.rows) - 1))

    @property
    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "dataset":         self.dataset,
                "loaded":          self.loaded,
                "error":           self.error,
                "total_rows":      len(self.rows),
                "cursor_position": self.cursor,
                "progress_pct":    round((self.cursor / max(len(self.rows), 1)) * 100, 1),
                "telemetry_mode":  "REPLAYED",
            }


class ReplayManager:
    def __init__(self):
        self._replays: Dict[str, DatasetReplay] = {}
        self._lock = threading.Lock()

    def _get_or_create(self, dataset: str) -> DatasetReplay:
        with self._lock:
            if dataset not in self._replays:
                self._replays[dataset] = DatasetReplay(dataset)
            return self._replays[dataset]

    def tick(self, dataset: str) -> Dict[str, Any]:
        return self._get_or_create(dataset).tick()

    def reset(self, dataset: str):
        self._get_or_create(dataset).reset()

    def seek(self, dataset: str, position: int):
        self._get_or_create(dataset).seek(position)

    def status(self, dataset: str) -> Dict[str, Any]:
        return self._get_or_create(dataset).status


replay_manager = ReplayManager()