import { useEffect, useState } from "react";
import { API, API_KEY } from "../api/client";

interface NetworkRow {
  timestamp: string;
  total_flows: number;
  benign_flows: number;
  attack_flows: number;
  attack_rate: number;
  avg_flow_bytes: number;
  avg_flow_packets: number;
  observed: boolean;
}

interface Props { dataset: string; }

export default function MonitorNetwork({ dataset }: Props) {
  const [rows, setRows] = useState<NetworkRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataset) return;
    fetch(`${API}/api/network-state?dataset=${dataset}&limit=60`, { headers: { 'X-API-Key': API_KEY } })
      .then(r => r.json())
      .then(setRows)
      .catch(e => setError(e.message));
  }, [dataset]);

  if (error) return <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs font-mono text-rose-300">Network data error: {error}</div>;
  if (!rows.length) return <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">Loading network telemetry...</div>;

  const latest = rows[rows.length - 1];
  const maxFlows = Math.max(...rows.map(r => r.total_flows), 1);
  const attackRows = rows.filter(r => r.attack_flows > 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total Flows", value: latest.total_flows.toLocaleString(), hot: false },
          { label: "Attack Flows", value: latest.attack_flows.toLocaleString(), hot: latest.attack_flows > 0 },
          { label: "Attack Rate", value: `${(latest.attack_rate * 100).toFixed(2)}%`, hot: latest.attack_rate > 0.1 },
          { label: "Avg Bytes/Flow", value: latest.avg_flow_bytes?.toFixed(0) ?? "—", hot: false },
        ].map(k => (
          <div key={k.label} className={`p-4 rounded-xl border ${k.hot ? "bg-rose-950/30 border-rose-500/40" : "bg-slate-900/60 border-slate-800"}`}>
            <div className="text-xs font-mono text-slate-400 mb-1">{k.label}</div>
            <div className={`text-xl font-mono font-bold ${k.hot ? "text-rose-400" : "text-white"}`}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">FLOW VOLUME — last {rows.length} windows</div>
        <div className="flex items-end gap-px h-24">
          {rows.map((r, i) => {
            const totalH = Math.round((r.total_flows / maxFlows) * 96);
            const attackH = Math.round((r.attack_flows / maxFlows) * 96);
            return (
              <div key={i} className="flex-1 flex flex-col justify-end relative group">
                <div style={{ height: totalH }} className="w-full relative bg-cyan-900/50">
                  {attackH > 0 && <div style={{ height: attackH }} className="absolute bottom-0 left-0 right-0 bg-rose-500/70" />}
                </div>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10 bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs font-mono whitespace-nowrap pointer-events-none">
                  <div className="text-slate-400">{r.timestamp?.slice(11, 16)}</div>
                  <div className="text-cyan-400">flows: {r.total_flows}</div>
                  {r.attack_flows > 0 && <div className="text-rose-400">attack: {r.attack_flows}</div>}
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-xs font-mono text-slate-600 mt-1">
          <span>{rows[0]?.timestamp?.slice(11, 16)}</span>
          <span>{latest.timestamp?.slice(11, 16)}</span>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">ATTACK WINDOWS ({attackRows.length} detected)</div>
        {attackRows.length === 0 ? (
          <div className="text-xs font-mono text-slate-500">No attack flows in current window</div>
        ) : (
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-slate-500 border-b border-slate-800">
                <th className="text-left py-1">Timestamp</th>
                <th className="text-right py-1">Attack Flows</th>
                <th className="text-right py-1">Attack Rate</th>
                <th className="text-right py-1">Avg Bytes</th>
              </tr>
            </thead>
            <tbody>
              {attackRows.slice(-10).map((r, i) => (
                <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="py-1 text-slate-300">{r.timestamp?.slice(0, 19)}</td>
                  <td className="py-1 text-right text-rose-400">{r.attack_flows}</td>
                  <td className="py-1 text-right text-orange-400">{(r.attack_rate * 100).toFixed(2)}%</td>
                  <td className="py-1 text-right text-slate-400">{r.avg_flow_bytes?.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}


