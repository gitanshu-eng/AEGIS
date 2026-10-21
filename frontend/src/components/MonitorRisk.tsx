import { useEffect, useState } from "react";
import { API, API_KEY } from "../api/client";

interface NetworkRow {
  timestamp: string;
  total_flows: number;
  benign_flows: number;
  attack_flows: number;
  attack_rate: number;
  avg_flow_duration: number;
  avg_flow_bytes: number;
  avg_flow_packets: number;
}

interface Props { dataset: string; }

export default function MonitorRisk({ dataset }: Props) {
  const [rows, setRows] = useState<NetworkRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataset) return;
    fetch(`${API}/api/network-state?dataset=${dataset}&limit=60`)
      .then(r => r.json())
      .then(setRows)
      .catch(e => setError(e.message));
  }, [dataset]);

  if (error) return <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs font-mono text-rose-300">Risk data error: {error}</div>;
  if (!rows.length) return <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">Loading risk telemetry...</div>;

  const latest = rows[rows.length - 1];
  const totalFlowsAll = rows.reduce((s, r) => s + r.total_flows, 0);
  const totalAttackAll = rows.reduce((s, r) => s + r.attack_flows, 0);
  const avgAttackRate = rows.reduce((s, r) => s + r.attack_rate, 0) / rows.length;
  const peakAttackRate = Math.max(...rows.map(r => r.attack_rate));

  const riskLevel = (rate: number) => {
    if (rate > 0.5) return { label: "CRITICAL", color: "text-rose-400", border: "border-rose-500/40", bg: "bg-rose-950/30" };
    if (rate > 0.2) return { label: "HIGH", color: "text-orange-400", border: "border-orange-500/40", bg: "bg-orange-950/30" };
    if (rate > 0.05) return { label: "MEDIUM", color: "text-yellow-400", border: "border-yellow-500/40", bg: "bg-yellow-950/20" };
    return { label: "LOW", color: "text-emerald-400", border: "border-emerald-500/30", bg: "bg-emerald-950/20" };
  };

  const current = riskLevel(latest.attack_rate);

  return (
    <div className="space-y-4">
      <div className={`p-4 rounded-xl border ${current.bg} ${current.border} flex items-center justify-between`}>
        <div>
          <div className="text-xs font-mono text-slate-400 mb-1">CURRENT RISK LEVEL</div>
          <div className={`text-3xl font-bold font-mono ${current.color}`}>{current.label}</div>
          <div className="text-xs font-mono text-slate-500 mt-1">{latest.timestamp?.slice(0, 19)}</div>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono text-slate-400 mb-1">WINDOW ATTACK RATE</div>
          <div className={`text-2xl font-mono font-bold ${current.color}`}>{(latest.attack_rate * 100).toFixed(2)}%</div>
          <div className="text-xs font-mono text-slate-500 mt-1">{latest.attack_flows} / {latest.total_flows} flows</div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Avg Attack Rate", value: `${(avgAttackRate * 100).toFixed(2)}%`, hot: false },
          { label: "Peak Attack Rate", value: `${(peakAttackRate * 100).toFixed(2)}%`, hot: peakAttackRate > 0.2 },
          { label: "Total Flows", value: totalFlowsAll.toLocaleString(), hot: false },
          { label: "Total Attack Flows", value: totalAttackAll.toLocaleString(), hot: totalAttackAll > 0 },
        ].map(k => (
          <div key={k.label} className={`p-4 rounded-xl border ${k.hot ? "bg-rose-950/30 border-rose-500/40" : "bg-slate-900/60 border-slate-800"}`}>
            <div className="text-xs font-mono text-slate-400 mb-1">{k.label}</div>
            <div className={`text-xl font-mono font-bold ${k.hot ? "text-rose-400" : "text-white"}`}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">BENIGN vs ATTACK COMPOSITION — last {rows.length} windows</div>
        <div className="flex items-end gap-px h-28">
          {rows.map((r, i) => {
            const max = Math.max(...rows.map(x => x.total_flows), 1);
            const totalH = Math.round((r.total_flows / max) * 112);
            const attackH = r.total_flows > 0 ? Math.round((r.attack_flows / r.total_flows) * totalH) : 0;
            const benignH = totalH - attackH;
            return (
              <div key={i} className="flex-1 flex flex-col justify-end group relative">
                <div style={{ height: attackH }} className="bg-rose-500/70 w-full" />
                <div style={{ height: benignH }} className="bg-cyan-900/60 w-full" />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10 bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs font-mono whitespace-nowrap pointer-events-none">
                  <div className="text-slate-400">{r.timestamp?.slice(11, 16)}</div>
                  <div className="text-cyan-400">benign: {r.benign_flows}</div>
                  {r.attack_flows > 0 && <div className="text-rose-400">attack: {r.attack_flows}</div>}
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs font-mono text-slate-500">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-cyan-900/60 inline-block" /> Benign</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-rose-500/70 inline-block" /> Attack</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {[
          { label: "AVG FLOW DURATION (µs)", key: "avg_flow_duration" as const },
          { label: "AVG BYTES PER FLOW", key: "avg_flow_bytes" as const },
        ].map(({ label, key }) => {
          const vals = rows.map(r => r[key] ?? 0);
          const max = Math.max(...vals, 1);
          return (
            <div key={key} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">{label}</div>
              <div className="flex items-end gap-px h-16">
                {rows.map((r, i) => {
                  const h = Math.round(((r[key] ?? 0) / max) * 64);
                  return (
                    <div key={i} className="flex-1 flex flex-col justify-end">
                      <div style={{ height: h }} className="bg-gradient-to-t from-cyan-600 to-purple-600 opacity-60 w-full min-h-px" />
                    </div>
                  );
                })}
              </div>
              <div className="text-xs font-mono text-slate-300 mt-1">
                latest: {(latest[key] ?? 0) > 1000 ? ((latest[key] ?? 0) / 1000).toFixed(1) + "ms" : (latest[key] ?? 0).toFixed(1) + "µs"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


