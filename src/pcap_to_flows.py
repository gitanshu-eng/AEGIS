import os
import pandas as pd
import numpy as np
from collections import defaultdict
from scapy.all import rdpcap, IP, TCP, UDP

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def extract_flows(pcap_path: str) -> pd.DataFrame:
    print(f"Reading {pcap_path}...")
    packets = rdpcap(pcap_path)
    print(f"Loaded {len(packets)} packets")

    windows = defaultdict(lambda: {
        "total_flows": 0, "benign_flows": 0, "attack_flows": 0,
        "bytes": [], "pkts": [], "durations": []
    })

    flow_tracker = {}

    for pkt in packets:
        if not pkt.haslayer(IP):
            continue
        ts  = float(pkt.time)
        win = int(ts // 60) * 60

        src = pkt[IP].src
        dst = pkt[IP].dst
        proto = pkt[IP].proto
        size  = len(pkt)

        sport = pkt.sport if hasattr(pkt, "sport") else 0
        dport = pkt.dport if hasattr(pkt, "dport") else 0
        fkey  = (src, dst, sport, dport, proto, win)

        if fkey not in flow_tracker:
            flow_tracker[fkey] = {"start": ts, "bytes": 0, "pkts": 0}
            windows[win]["total_flows"] += 1
            # heuristic: attack flows from 172.16.x.x sources
            if src.startswith("172.16."):
                windows[win]["attack_flows"] += 1
            else:
                windows[win]["benign_flows"] += 1

        flow_tracker[fkey]["bytes"] += size
        flow_tracker[fkey]["pkts"]  += 1

    for fkey, fdata in flow_tracker.items():
        win = fkey[5]
        duration = 0.0
        windows[win]["bytes"].append(fdata["bytes"])
        windows[win]["pkts"].append(fdata["pkts"])
        windows[win]["durations"].append(duration)

    rows = []
    for win in sorted(windows):
        w = windows[win]
        total   = max(w["total_flows"], 1)
        attack  = w["attack_flows"]
        rows.append({
            "timestamp":        pd.Timestamp(win, unit="s"),
            "total_flows":      w["total_flows"],
            "benign_flows":     w["benign_flows"],
            "attack_flows":     attack,
            "attack_rate":      attack / total,
            "avg_flow_bytes":   np.mean(w["bytes"]) if w["bytes"] else 0,
            "avg_flow_packets": np.mean(w["pkts"])  if w["pkts"]  else 0,
            "avg_flow_duration": np.mean(w["durations"]) if w["durations"] else 0,
            "observed":         1,
        })

    df = pd.DataFrame(rows)
    print(f"Extracted {len(df)} 1-minute windows")
    return df

if __name__ == "__main__":
    pcap_path = os.path.join(BASE_DIR, "data", "pcap_synthetic", "cic_ids2018_mar02_synthetic.pcap")
    df = extract_flows(pcap_path)
    print(df[["timestamp","total_flows","attack_flows","attack_rate"]].to_string(index=False))
