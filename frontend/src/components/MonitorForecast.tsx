import { useEffect, useState } from "react";
import { API, API_KEY } from "../api/client";

interface ForecastRow {
  timestamp: string;
  segment_id: number;
  attack_rate: number;
  actual_escalation: number;
  escalation_probability: number;
  primary_evidence_feature: string;
}

interface Props { dataset: string; }

export default function MonitorForecast({ dataset }: Props) {
  const [rows, setRows] = useState<ForecastRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataset) return;
    fetch(`${API}/api/forecast?dataset=${dataset}`, { headers: { 'X-API-Key': API_KEY } })
      .then(r => r.json())
      .then(setRows)
      .catch(e => setError(e.message));
  }, [dataset]);

  if (error) return <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs font-mono text-rose-300">Forecast error: {error}</div>;
  if (!rows.length) return <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">Loading forecast data...</div>;

  const latest = rows[rows.length - 1];
  const highRisk = rows.filter(r => (r.escalation_probability ?? 0) > 0.5);
  const featureCounts: Record<string, number> = {};
  rows.forEach(r => { if (r.primary_evidence_feature) featureCounts[r.primary_evidence_feature] = (featureCounts[r.primary_evidence_feature] ?? 0) + 1; });
  const topFeatures = Object.entries(featureCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const maxFeature = topFeatures[0]?.[1] ?? 1;

  const probColor = (p: number) => {
    if (p > 0.7) return "text-rose-400";
    if (p > 0.4) return "text-orange-400";
    if (p > 0.2) return "text-yellow-400";
    return "text-emerald-400";
  };

  const escProb = latest.escalation_probability;
  const escDisplay = isNaN(escProb) || escProb == null ? "N/A" : `${(escProb * 100).toFixed(1)}%`;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Escalation Prob", value: escDisplay, hot: (escProb ?? 0) > 0.5 },
          { label: "Attack Rate", value: `${(latest.attack_rate * 100).toFixed(2)}%`, hot: latest.attack_rate > 0.1 },
          { label: "High-Risk Windows", value: highRisk.length.toString(), hot: highRisk.length > 0 },
          { label: "Primary Driver", value: latest.primary_evidence_feature ?? "—", hot: false },
        ].map(k => (
          <div key={k.label} className={`p-4 rounded-xl border ${k.hot ? "bg-rose-950/30 border-rose-500/40" : "bg-slate-900/60 border-slate-800"}`}>
            <div className="text-xs font-mono text-slate-400 mb-1">{k.label}</div>
            <div className={`text-xl font-mono font-bold truncate ${k.hot ? "text-rose-400" : "text-white"}`}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">ESCALATION PROBABILITY — last {rows.length} windows</div>
        <div className="relative h-28">
          {(() => { const mp = Math.max(...rows.map(r => r.escalation_probability ?? 0), 0.01); return (<><div className="absolute left-0 right-0 border-t border-rose-500/20" style={{ top: "0%" }}><span className="text-[10px] font-mono text-rose-500/40 ml-1">{(mp*100).toFixed(1)}%</span></div><div className="absolute left-0 right-0 border-t border-orange-500/20 border-dashed" style={{ top: "30%" }}><span className="text-[10px] font-mono text-orange-500/40 ml-1">{(mp*0.7*100).toFixed(1)}%</span></div><div className="absolute left-0 right-0 border-t border-yellow-500/20 border-dashed" style={{ top: "60%" }}><span className="text-[10px] font-mono text-yellow-500/30 ml-1">{(mp*0.4*100).toFixed(1)}%</span></div></>);})()}
          <div className="absolute inset-0 flex items-end gap-px pt-4">
            {(() => { const maxProb = Math.max(...rows.map(r => r.escalation_probability ?? 0), 0.01); return rows.map((r, i) => {
              const p = r.escalation_probability ?? 0;
              const h = Math.round((p / maxProb) * 96);
              const rel = maxProb > 0 ? p / maxProb : 0;
              const color = rel > 0.7 ? "bg-rose-500" : rel > 0.4 ? "bg-orange-400" : rel > 0.2 ? "bg-yellow-500" : "bg-emerald-600";
              return (
                <div key={i} className="flex-1 flex flex-col justify-end group relative">
                  <div style={{ height: h }} className={`${color} opacity-80 w-full min-h-px`} />
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10 bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs font-mono whitespace-nowrap pointer-events-none">
                    <div className="text-slate-400">{r.timestamp?.slice(11, 16)}</div>
                    <div className={probColor(p)}>prob: {(p * 100).toFixed(1)}%</div>
                    <div className="text-slate-500">{r.primary_evidence_feature}</div>
                  </div>
                </div>
              );
            });})()}
          </div>
        </div>
        <div className="flex justify-between text-xs font-mono text-slate-600 mt-1">
          <span>{rows[0]?.timestamp?.slice(11, 16)}</span>
          <span>{latest.timestamp?.slice(11, 16)}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">TOP EVIDENCE FEATURES</div>
          <div className="space-y-3">
            {topFeatures.length === 0 ? <div className="text-xs font-mono text-slate-500">No feature data</div> : topFeatures.map(([feat, count]) => (
              <div key={feat} className="flex items-center gap-2">
                <div className="text-xs font-mono text-cyan-400 w-28 truncate">{feat}</div>
                <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full" style={{ width: `${(count / maxFeature) * 100}%` }} />
                </div>
                <div className="text-xs font-mono text-slate-500 w-6 text-right">{count}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">HIGH-RISK WINDOWS (&gt;50%)</div>
          {highRisk.length === 0 ? <div className="text-xs font-mono text-slate-500">None in current window</div> : (
            <table className="w-full text-xs font-mono">
              <thead><tr className="text-slate-500 border-b border-slate-800"><th className="text-left py-1">Time</th><th className="text-right py-1">Prob</th><th className="text-right py-1">Driver</th></tr></thead>
              <tbody>
                {highRisk.slice(-8).map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/50">
                    <td className="py-1 text-slate-300">{r.timestamp?.slice(11, 16)}</td>
                    <td className={`py-1 text-right ${probColor(r.escalation_probability)}`}>{(r.escalation_probability * 100).toFixed(1)}%</td>
                    <td className="py-1 text-right text-slate-400 truncate max-w-20">{r.primary_evidence_feature}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}


