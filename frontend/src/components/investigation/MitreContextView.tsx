import { useEffect, useState } from "react";
import { API, API_KEY } from "../../api/client";

interface Episode {
  episode_id: string;
  start_time: string;
  peak_risk_score: number;
  peak_risk_level: string;
  sustained_tactics: string[];
  sustained_techniques: string[];
}

interface Props { dataset: string; }

const TACTIC_ORDER = [
  "TA0043","TA0042","TA0001","TA0002","TA0003","TA0004",
  "TA0005","TA0006","TA0007","TA0008","TA0009","TA0010",
  "TA0011","TA0040",
];

function parsePair(s: string): { id: string; name: string } {
  const [id, ...rest] = s.split(":");
  return { id: id.trim(), name: rest.join(":").trim() || id.trim() };
}

export default function MitreContextView({ dataset }: Props) {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataset) return;
    setEpisodes([]); setSelected(null); setError(null);
    fetch(`${API}/api/mitre-context?dataset=${dataset}`, { headers: { 'X-API-Key': API_KEY } })
      .then(r => r.json())
      .then(setEpisodes)
      .catch(e => setError(e.message));
  }, [dataset]);

  if (error) return (
    <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs font-mono text-rose-300">
      Error: {error}
    </div>
  );
  if (!episodes.length) return (
    <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">
      Loading MITRE ATT&CK data...
    </div>
  );

  const tacticMap = new Map<string, string>();
  const techniqueMap = new Map<string, string>();
  const cellEpisodes = new Map<string, Set<string>>();
  const techniqueTactics = new Map<string, Set<string>>();

  episodes.forEach(ep => {
    const tactics = (ep.sustained_tactics || []).map(parsePair);
    const techniques = (ep.sustained_techniques || []).map(parsePair);
    tactics.forEach(t => tacticMap.set(t.id, t.name));
    techniques.forEach(t => techniqueMap.set(t.id, t.name));
    tactics.forEach(tac => {
      techniques.forEach(tech => {
        const key = `${tac.id}|${tech.id}`;
        if (!cellEpisodes.has(key)) cellEpisodes.set(key, new Set());
        cellEpisodes.get(key)!.add(ep.episode_id);
        if (!techniqueTactics.has(tech.id)) techniqueTactics.set(tech.id, new Set());
        techniqueTactics.get(tech.id)!.add(tac.id);
      });
    });
  });

  const tacticIds = TACTIC_ORDER.filter(id => tacticMap.has(id));
  const techniqueIds = [...techniqueMap.keys()].sort((a, b) => {
    const countA = [...(techniqueTactics.get(a) ?? [])].reduce((s, tac) => s + (cellEpisodes.get(`${tac}|${a}`)?.size ?? 0), 0);
    const countB = [...(techniqueTactics.get(b) ?? [])].reduce((s, tac) => s + (cellEpisodes.get(`${tac}|${b}`)?.size ?? 0), 0);
    return countB - countA;
  });

  const maxEpCount = Math.max(...[...cellEpisodes.values()].map(s => s.size), 1);

  function cellColor(count: number, isHighlighted: boolean): string {
    if (count === 0) return "";
    if (isHighlighted) return "bg-cyan-400 border-cyan-300";
    const intensity = count / maxEpCount;
    if (intensity > 0.66) return "bg-rose-500/80 border-rose-400/60";
    if (intensity > 0.33) return "bg-amber-500/70 border-amber-400/50";
    return "bg-purple-500/60 border-purple-400/40";
  }

  const riskColor = (level: string) => {
    if (level === "CRITICAL") return "text-rose-400";
    if (level === "HIGH") return "text-orange-400";
    if (level === "MEDIUM") return "text-yellow-400";
    return "text-emerald-400";
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total Episodes", value: episodes.length.toString() },
          { label: "Unique Tactics", value: tacticIds.length.toString() },
          { label: "Unique Techniques", value: techniqueIds.length.toString() },
          { label: "Top Tactic", value: tacticMap.get(tacticIds[0]) ?? "—" },
        ].map(k => (
          <div key={k.label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs font-mono text-slate-400 mb-1">{k.label}</div>
            <div className="text-xl font-mono font-bold text-white truncate">{k.value}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-4 px-1">
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Hit frequency:</span>
        {[
          { cls: "bg-purple-500/60 border-purple-400/40", label: "Low" },
          { cls: "bg-amber-500/70 border-amber-400/50",   label: "Medium" },
          { cls: "bg-rose-500/80 border-rose-400/60",     label: "High" },
          { cls: "bg-cyan-400 border-cyan-300",           label: "Selected episode" },
        ].map(({ cls, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={`w-3 h-3 rounded-sm border ${cls}`} />
            <span className="text-[10px] font-mono text-slate-400">{label}</span>
          </div>
        ))}
        {selected && (
          <button onClick={() => setSelected(null)} className="ml-auto text-[10px] font-mono text-cyan-400 hover:text-white border border-cyan-500/40 px-2 py-0.5 rounded transition-colors">
            Clear filter
          </button>
        )}
      </div>

      <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
        <div className="text-xs font-mono text-slate-400 px-4 pt-3 pb-2 border-b border-slate-800 tracking-wide uppercase">
          MITRE ATT&CK Matrix — {selected ? `filtered to ${selected}` : "all episodes"}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[10px] font-mono border-collapse">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-slate-900 text-left px-3 py-2 text-slate-500 font-normal border-b border-r border-slate-800 w-48 min-w-[12rem]">
                  Technique
                </th>
                {tacticIds.map(tid => (
                  <th key={tid} className="px-2 py-2 border-b border-slate-800 text-center text-slate-400 font-normal whitespace-nowrap min-w-[6rem]">
                    <div className="text-cyan-500">{tid}</div>
                    <div className="text-[9px] text-slate-500 leading-tight mt-0.5 max-w-[5rem] mx-auto truncate">{tacticMap.get(tid)}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {techniqueIds.map((techId, rowIdx) => {
                const techName = techniqueMap.get(techId) ?? techId;
                return (
                  <tr key={techId} className={rowIdx % 2 === 0 ? "bg-slate-950/30" : ""}>
                    <td className="sticky left-0 z-10 bg-slate-900/95 border-r border-slate-800 px-3 py-1.5">
                      <div className="text-purple-400">{techId}</div>
                      <div className="text-slate-400 text-[9px] leading-tight mt-0.5 max-w-[10rem] truncate">{techName}</div>
                    </td>
                    {tacticIds.map(tacId => {
                      const key = `${tacId}|${techId}`;
                      const epSet = cellEpisodes.get(key);
                      const count = epSet?.size ?? 0;
                      const isHighlighted = selected ? (epSet?.has(selected) ?? false) : false;
                      const cls = cellColor(count, isHighlighted);
                      return (
                        <td key={tacId} className="border-b border-slate-800/40 text-center py-1.5 px-2">
                          {count > 0 ? (
                            <div className={`inline-flex items-center justify-center w-6 h-6 rounded border text-[9px] font-bold ${cls}`}>{count}</div>
                          ) : (
                            <div className="inline-block w-6 h-6 rounded border border-slate-800/30 bg-slate-900/20" />
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide uppercase">Episodes — click to filter matrix</div>
        <div className="space-y-2 max-h-56 overflow-y-auto">
          {episodes.map(ep => (
            <div key={ep.episode_id}
              onClick={() => setSelected(selected === ep.episode_id ? null : ep.episode_id)}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${selected === ep.episode_id ? "border-cyan-500/50 bg-slate-800/80" : "bg-slate-900/60 border-slate-800 hover:border-slate-700"}`}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-mono font-bold text-cyan-400">{ep.episode_id}</span>
                <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 ${riskColor(ep.peak_risk_level)}`}>{ep.peak_risk_level}</span>
                <span className="text-xs font-mono text-slate-500">{ep.start_time?.slice(0, 16)}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {(ep.sustained_techniques || []).map(t => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-purple-300">{t.split(":")[0]?.trim()}</span>
                ))}
                {(ep.sustained_tactics || []).map(t => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-cyan-300">{t.split(":")[0]?.trim()}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="text-[10px] font-mono text-slate-600 text-right">
        HEURISTIC_CONTEXTUAL — techniques paired to tactics by episode co-occurrence
      </div>
    </div>
  );
}
