import { useEffect, useRef } from "react";
import type { NetworkTimelinePoint } from "../types/aegis";

const POLL_INTERVAL_MS = 5000;

const API_BASE = (import.meta.env.VITE_API_URL?.replace(/\/$/, "")) ?? (import.meta.env.DEV ? "http://localhost:8000" : "https://aegis-api-hqnx.onrender.com");
const API_KEY = import.meta.env.VITE_API_KEY ?? 'dev-insecure-key';

export function useLiveTick(
  dataset: string,
  onTick: (point: NetworkTimelinePoint, mode?: string) => void
) {
  const onTickRef = useRef<(point: NetworkTimelinePoint, mode?: string) => void>(onTick);
  onTickRef.current = onTick;

  useEffect(() => {
    let active = true;

    const poll = async () => {
      if (!active) return;
      try {
        let data: any = null;
        let usedPcap = false;

        try {
          const pcapRes = await fetch(
            `${API_BASE}/api/pcap/tick?name=${encodeURIComponent(dataset)}`,
            { headers: { Accept: "application/json", "X-API-Key": API_KEY } }
          );
          if (pcapRes.ok) {
            const pcapData = await pcapRes.json();
            if (!pcapData.error) {
              data = pcapData;
              usedPcap = true;
            }
          }
        } catch (_) {}

        if (!data) {
          const res = await fetch(
            `${API_BASE}/api/live/tick?dataset=${encodeURIComponent(dataset)}`,
            { headers: { Accept: "application/json", "X-API-Key": API_KEY } }
          );
          if (!res.ok) return;
          data = await res.json();
        }

        if (!active) return;

        const point: NetworkTimelinePoint = {
          timestamp:           data.timestamp,
          attack_rate:         data.attack_rate ?? 0,
          escalation_forecast: data.escalation_forecast ?? 0,
          risk_score:          data.risk_score ?? 0,
          total_flows:         data.total_flows ?? 0,
          benign_flows:        data.benign_flows ?? 0,
          attack_flows:        data.attack_flows ?? 0,
          network_state:       data.network_state ?? "OBSERVED",
        };

        onTickRef.current(point, usedPcap ? "PCAP_REPLAY" : "CSV_REPLAY");
      } catch (_) {
        // silently skip failed ticks
      }
    };

    const timer = setInterval(poll, POLL_INTERVAL_MS);
    poll();

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [dataset]);
}



