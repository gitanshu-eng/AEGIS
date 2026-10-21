# -*- coding: utf-8 -*-
import os
import threading
import pandas as pd
from src.inference import predict

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCAP_DIR      = os.path.join(BASE_DIR, "data", "pcap_synthetic")
FEATURES_DIR  = os.path.join(BASE_DIR, "data", "pcap_features")


class PcapReplay:
    def __init__(self, name: str):
        self.name   = name
        self.cursor = 0
        self.rows   = []
        self.loaded = False
        self.error  = None
        self.source = None
        self._lock  = threading.Lock()
        self._load()

    def _load(self):
        # --- Option 1: pre-extracted CSV (works on Render) ---
        csv_path = os.path.join(FEATURES_DIR, f"{self.name}_features.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                self.rows   = df.to_dict(orient="records")
                self.loaded = True
                self.source = "csv"
                print(f"[PcapReplay] Loaded {len(self.rows)} rows from CSV: {csv_path}")
                return
            except Exception as e:
                self.error = f"CSV load failed: {e}"

        # --- Option 2: live PCAP parsing (local only, needs Scapy) ---
        pcap_path = os.path.join(PCAP_DIR, f"{self.name}_synthetic.pcap")
        if os.path.exists(pcap_path):
            try:
                from src.pcap_to_flows import extract_flows
                from src.flows_to_features import compute_features
                flows       = extract_flows(pcap_path)
                features    = compute_features(flows)
                self.rows   = features.to_dict(orient="records")
                self.loaded = True
                self.source = "pcap"
                print(f"[PcapReplay] Loaded {len(self.rows)} rows from PCAP: {pcap_path}")
                return
            except Exception as e:
                self.error = f"PCAP load failed: {e}"

        self.error = f"No CSV or PCAP found for '{self.name}' in {FEATURES_DIR} or {PCAP_DIR}"

    def tick(self) -> dict:
        with self._lock:
            if not self.loaded or not self.rows:
                return {
                    "error":          self.error or "No data loaded",
                    "telemetry_mode": "PCAP_REPLAY",
                    "name":           self.name,
                }
            row  = self.rows[self.cursor]
            self.cursor = (self.cursor + 1) % len(self.rows)
            infer = predict(row)
            return {
                "telemetry_mode":      "PCAP_REPLAY",
                "data_source":         self.source,
                "name":                self.name,
                "cursor_position":     self.cursor,
                "total_rows":          len(self.rows),
                "progress_pct":        round((self.cursor / len(self.rows)) * 100, 1),
                "timestamp":           str(row.get("timestamp", "")),
                "total_flows":         int(row.get("total_flows", 0) or 0),
                "benign_flows":        int(row.get("benign_flows", 0) or 0),
                "attack_flows":        int(row.get("attack_flows", 0) or 0),
                "attack_rate":         float(row.get("attack_rate", 0) or 0),
                "escalation_forecast": infer.get("p_escalation") or 0.0,
                "risk_score":          infer.get("risk_score") or 0.0,
                "inference_mode":      infer.get("inference_mode", "UNAVAILABLE"),
                "network_state":       "OBSERVED",
            }

    def reset(self):
        with self._lock:
            self.cursor = 0

    @property
    def status(self) -> dict:
        with self._lock:
            return {
                "loaded":          self.loaded,
                "error":           self.error,
                "source":          self.source,
                "name":            self.name,
                "total_rows":      len(self.rows),
                "cursor_position": self.cursor,
                "progress_pct":    round((self.cursor / max(len(self.rows), 1)) * 100, 1),
                "telemetry_mode":  "PCAP_REPLAY",
            }


class PcapReplayManager:
    def __init__(self):
        self._replays = {}
        self._lock    = threading.Lock()

    def _get_or_create(self, name: str) -> PcapReplay:
        with self._lock:
            if name not in self._replays:
                self._replays[name] = PcapReplay(name)
            return self._replays[name]

    def tick(self, name: str) -> dict:
        return self._get_or_create(name).tick()

    def reset(self, name: str):
        self._get_or_create(name).reset()

    def status(self, name: str) -> dict:
        return self._get_or_create(name).status


pcap_replay_manager = PcapReplayManager()
