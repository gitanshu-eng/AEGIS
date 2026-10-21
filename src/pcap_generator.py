# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
from scapy.all import wrpcap, IP, TCP, Raw

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
PCAP_DIR = os.path.join(BASE_DIR, "data", "pcap_synthetic")
os.makedirs(PCAP_DIR, exist_ok=True)

def generate_pcap(dataset: str = "cic_ids2018_mar02"):
    csv_path = os.path.join(DATA_DIR, f"{dataset}_temporal_continuous.csv")
    df = pd.read_csv(csv_path)
    tcol = "time_window" if "time_window" in df.columns else "timestamp"
    df = df[df["observed"] == 1].head(60).reset_index(drop=True)

    packets = []
    for idx, row in df.iterrows():
        ts         = pd.Timestamp(row[tcol]).timestamp()
        n_benign   = int(row.get("benign_flows", 20))
        n_attack   = int(row.get("attack_flows", 0))
        avg_bytes  = float(row.get("avg_flow_bytes", 500))
        avg_pkts   = max(int(row.get("avg_flow_packets", 5)), 1)
        payload_sz = max(1, int(avg_bytes / avg_pkts))

        for i in range(min(n_benign, 200)):
            src = f"192.168.{(i // 50) + 1}.{(i % 50) + 1}"
            dst = f"10.0.0.{(i % 50) + 1}"
            pkt = IP(src=src, dst=dst, proto=6) / TCP(sport=10000 + i, dport=80, flags="PA") / Raw(load=b"B" * payload_sz)
            pkt.time = ts + (i * 0.001)
            packets.append(pkt)

        for i in range(min(n_attack, 100)):
            src = f"172.16.{(i // 50) + 1}.{(i % 50) + 100}"
            dst = f"10.0.0.{(i % 20) + 1}"
            pkt = IP(src=src, dst=dst, proto=6) / TCP(sport=20000 + i, dport=443, flags="S") / Raw(load=b"A" * payload_sz)
            pkt.time = ts + (i * 0.001)
            packets.append(pkt)

    out_path = os.path.join(PCAP_DIR, f"{dataset}_synthetic.pcap")
    wrpcap(out_path, packets)
    print(f"Written {len(packets)} packets to {out_path}")
    return out_path

if __name__ == "__main__":
    generate_pcap()
