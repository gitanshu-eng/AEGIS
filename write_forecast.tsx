import { useEffect, useState } from "react";
import { API } from "../api/client";

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
    fetch(${API}/api/forecasts?dataset=&limit=60)
      .then(r => r.json())
      .then(setRows)
      .catch(e => setError(e.message));
  }, [dataset]);

  if (error) return <div className="text-red-400 p-4">Forecast error: {error}</div>;
  if (!rows.length) return <div className="text-zinc-500 p-4">Loading forecast data...</div>;

  const latest = rows[rows.length - 1];
  const maxEsc = Math.max(...rows.map(r => r.escalation_probability), 0.01);
  const highRisk = rows.filter(r => r.escalation_probability > 0.5);
  const confirmedCount = rows.filter(r => r.actual_escalation === 1).length;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Segments", value: rows.length.toString(), hot: false },
          { label: "Escalation Prob", value: ${(latest.escalation_probability * 100).toFixed(1)}%, hot: latest.escalation_probability > 0.5 },
          { label: "Actual Escalations", value: confirmedCount.toString(), hot: confirmedCount > 0 },
          { label: "High-Risk Segments", value: highRisk.length.toString(), hot: highRisk.length > 0 },
        ].map(k => (
          <div key={k.label} className={ounded-lg border p-3 }>
            <div className="text-xs text-zinc-400 mb-1">{k.label}</div>
            <div className={	ext-xl font-mono font-bold }>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4">
        <div className="text-xs text-zinc-400 mb-3">ESCALATION PROBABILITY - last {rows.length} segments</div>
        <div className="flex items-end gap-px h-24">
          {rows.map((r, i) => {
            const h = Math.round((r.escalation_probability / maxEsc) * 96);
            const hot = r.escalation_probability > 0.5;
            const confirmed = r.actual_escalation === 1;
            return (
              <div key={i} className="flex-1 flex flex-col justify-end relative group">
                <div
                  style={{ height: Math.max(h, 1) }}
                  className={w-full }
                />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10 bg-zinc-800 border border-zinc-600 rounded p-1 text-xs whitespace-nowrap pointer-events-none">
                  <div>{r.timestamp?.slice(11, 16)}</div>
                  <div className="text-cyan-400">esc prob: {(r.escalation_probability * 100).toFixed(1)}%</div>
                  <div className="text-orange-400">attack rate: {(r.attack_rate * 100).toFixed(2)}%</div>
                  {confirmed && <div className="text-red-400">ESCALATED</div>}
                  {r.primary_evidence_feature && <div className="text-zinc-400">evidence: {r.primary_evidence_feature}</div>}
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-zinc-600 mt-1">
          <span>{rows[0]?.timestamp?.slice(11, 16)}</span>
          <span>{latest.timestamp?.slice(11, 16)}</span>
        </div>
        <div className="flex gap-4 mt-2 text-xs text-zinc-500">
          <span><span className="inline-block w-2 h-2 bg-red-500 mr-1 rounded-sm" />Confirmed escalation</span>
          <span><span className="inline-block w-2 h-2 bg-orange-500/70 mr-1 rounded-sm" />High probability</span>
          <span><span className="inline-block w-2 h-2 bg-cyan-700/50 mr-1 rounded-sm" />Normal</span>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4">
        <div className="text-xs text-zinc-400 mb-3">HIGH ESCALATION SEGMENTS ({highRisk.length})</div>
        {highRisk.length === 0 ? (
          <div className="text-zinc-500 text-sm">No segments above 50% escalation threshold</div>
        ) : (
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-zinc-500 border-b border-zinc-700">
                <th className="text-left py-1">Timestamp</th>
                <th className="text-right py-1">Esc Prob</th>
                <th className="text-right py-1">Actual</th>
                <th className="text-right py-1">Attack Rate</th>
                <th className="text-left py-1 pl-3">Top Feature</th>
              </tr>
            </thead>
            <tbody>
              {highRisk.slice(-10).map((r, i) => (
                <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                  <td className="py-1 text-zinc-300">{r.timestamp?.slice(0, 19)}</td>
                  <td className="py-1 text-right text-red-400">{(r.escalation_probability * 100).toFixed(1)}%</td>
                  <td className="py-1 text-right">{r.actual_escalation === 1 ? <span className="text-red-400">YES</span> : <span className="text-zinc-500">no</span>}</td>
                  <td className="py-1 text-right text-zinc-400">{(r.attack_rate * 100).toFixed(2)}%</td>
                  <td className="py-1 pl-3 text-cyan-600">{r.primary_evidence_feature ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
