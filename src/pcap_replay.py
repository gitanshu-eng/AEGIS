# -*- coding: utf-8 -*-
import os
import threading
import pandas as pd
from src.pcap_to_flows import extract_flows
from src.flows_to_features import compute_features
from src.inference import predict

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCAP_DIR  = os.path.join(BASE_DIR, "data", "pcap_synthetic")

class PcapReplay:
    def __init__(self, pcap_path: str):
        self.pcap_path = pcap_path
        self.cursor    = 0
        self.rows      = []
        self.loaded    = False
        self.error     = None
        self._lock     = threading.Lock()
        self._load()

    def _load(self):
        try:
            flows = extract_flows(self.pcap_path)
            features = compute_features(flows)
            self.rows   = features.to_dict(orient="records")
            self.loaded = True
            print(f"PcapReplay loaded {len(self.rows)} windows from {self.pcap_path}")
        except Exception as e:
            self.error = str(e)

    def tick(self) -> dict:
        with self._lock:
            if not self.loaded or not self.rows:
                return {"error": self.error or "No data", "telemetry_mode": "PCAP_REPLAY"}
            row = self.rows[self.cursor]
            self.cursor = (self.cursor + 1) % len(self.rows)
            infer = predict(row)
            return {
                "telemetry_mode":      "PCAP_REPLAY",
                "data_source":         "synthetic_pcap",
                "pcap_path":           self.pcap_path,
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
                "pcap_path":       self.pcap_path,
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
                path = os.path.join(PCAP_DIR, f"{name}_synthetic.pcap")
                self._replays[name] = PcapReplay(path)
            return self._replays[name]

    def tick(self, name: str) -> dict:
        return self._get_or_create(name).tick()

    def reset(self, name: str):
        self._get_or_create(name).reset()

    def status(self, name: str) -> dict:
        return self._get_or_create(name).status


pcap_replay_manager = PcapReplayManager()
