import React, { useState, useEffect, useRef } from "react";
import { Radio, Activity, Shield, Zap, RefreshCw } from "lucide-react";
import { API, API_KEY } from "../../api/client";

interface TickData {
  timestamp: string;
  total_flows: number;
  benign_flows: number;
  attack_flows: number;
  attack_rate: number;
  escalation_forecast: number;
  risk_score: number;
  inference_mode: string;
  data_source: string;
  cursor_position: number;
  total_rows: number;
  progress_pct: number;
  network_state: string;
}

const MAX_HISTORY = 30;

export const LiveFeedView: React.FC<{ dataset: string }> = ({ dataset }) => {
  const [ticks, setTicks]     = useState<TickData[]>([]);
  const [latest, setLatest]   = useState<TickData | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [paused, setPaused]   = useState(false);
  const pausedRef             = useRef(paused);
  pausedRef.current           = paused;

  useEffect(() => {
    setTicks([]);
    setLatest(null);
    setError(null);

    const poll = async () => {
      if (pausedRef.current) return;
      try {
        const res = await fetch(
          `${API}/api/pcap/tick?name=${encodeURIComponent(dataset)}`,
          { headers: { Accept: "application/json", "X-API-Key": API_KEY } }
        );
        if (!res.ok) { setError(`HTTP ${res.status}`); return; }
        const data = await res.json() as any;
        if (data.error) { setError(String(data.error)); return; }
        setError(null);
        setLatest(data);
        setTicks((prev) => {
          const next = [...prev, data];
          return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
        });
      } catch (e) {
        setError("Failed to reach backend");
      }
    };

    poll();
    const timer = setInterval(poll, 3000);
    return () => clearInterval(timer);
  }, [dataset]);

  const maxAttack = Math.max(...ticks.map((t) => t.attack_rate), 0.01);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/30">
            <Radio className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold font-mono text-white tracking-wide">LIVE PCAP FEED</h2>
            <p className="text-xs text-slate-400 font-mono">
              Source: <span className="text-cyan-300">{dataset}</span>
              {latest && <> � Row {latest.cursor_position}/{latest.total_rows} � {latest.progress_pct}% complete</>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {error ? (
            <span className="text-xs font-mono text-rose-400 px-2 py-1 rounded bg-rose-950/40 border border-rose-500/30">{error}</span>
          ) : latest ? (
            <span className="flex items-center gap-1.5 text-xs font-mono text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              {paused ? "PAUSED" : "STREAMING"}
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
              <RefreshCw className="w-3 h-3 animate-spin" /> Connecting...
            </span>
          )}
          <button
            onClick={() => setPaused((p) => !p)}
            className="px-3 py-1.5 rounded-lg text-xs font-mono border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
          >
            {paused ? "Resume" : "Pause"}
          </button>
        </div>
      </div>

      {/* KPI Row */}
      {latest && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Flows", value: latest.total_flows.toLocaleString(), icon: Activity, color: "text-cyan-400" },
            { label: "Attack Flows", value: latest.attack_flows.toLocaleString(), icon: Shield, color: "text-rose-400" },
            { label: "Attack Rate", value: `${(latest.attack_rate * 100).toFixed(1)}%`, icon: Zap, color: "text-amber-400" },
            { label: "Escalation P", value: `${(latest.escalation_forecast * 100).toFixed(1)}%`, icon: Radio, color: "text-purple-400" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${color}`} />
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">{label}</span>
              </div>
              <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
              <div className="text-[10px] font-mono text-slate-500 mt-1">{latest.timestamp?.slice(0, 19)}</div>
            </div>
          ))}
        </div>
      )}

      {/* Attack Rate Sparkline */}
      {ticks.length > 1 && (
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 mb-3 uppercase tracking-wider">Attack Rate History</div>
          <div className="flex items-end gap-1 h-20">
            {ticks.map((t, i) => {
              const pct = t.attack_rate / maxAttack;
              const isLatest = i === ticks.length - 1;
              return (
                <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                  <div
                    className={`w-full rounded-sm transition-all ${isLatest ? "bg-cyan-400" : "bg-cyan-800/60"}`}
                    style={{ height: `${Math.max(4, pct * 100)}%` }}
                    title={`${(t.attack_rate * 100).toFixed(1)}% @ ${t.timestamp?.slice(11, 19)}`}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-[10px] font-mono text-slate-600 mt-1">
            <span>{ticks[0]?.timestamp?.slice(11, 16)}</span>
            <span>{ticks[ticks.length - 1]?.timestamp?.slice(11, 16)}</span>
          </div>
        </div>
      )}

      {/* Raw Tick Log */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 uppercase tracking-wider">Tick Log</div>
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {[...ticks].reverse().map((t, i) => (
            <div key={i} className="flex items-center gap-3 text-[11px] font-mono py-1 border-b border-slate-800/60">
              <span className="text-slate-500 w-28 shrink-0">{t.timestamp?.slice(11, 19)}</span>
              <span className="text-cyan-300 w-24 shrink-0">{t.total_flows} flows</span>
              <span className="text-rose-400 w-24 shrink-0">{(t.attack_rate * 100).toFixed(1)}% atk</span>
              <span className={`w-28 shrink-0 ${t.inference_mode === "UNAVAILABLE" ? "text-slate-500" : "text-emerald-400"}`}>
                {t.inference_mode}
              </span>
              <span className="text-slate-500">{t.data_source}</span>
            </div>
          ))}
          {ticks.length === 0 && !error && (
            <div className="text-slate-500 text-center py-4">Waiting for first tick...</div>
          )}
        </div>
      </div>
    </div>
  );
};


