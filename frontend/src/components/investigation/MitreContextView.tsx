import { useEffect, useState } from "react";
import { API } from "../../api/client";

interface Episode {
  episode_id: string;
  start_time: string;
  peak_risk_score: number;
  peak_risk_level: string;
  sustained_tactics: string[];
  sustained_techniques: string[];
}

interface Props { dataset: string; }

export default function MitreContextView({ dataset }: Props) {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataset) return;
    fetch(`${API}/api/episodes?dataset=${dataset}`)
      .then(r => r.json())
      .then(setEpisodes)
      .catch(e => setError(e.message));
  }, [dataset]);

  if (error) return <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs font-mono text-rose-300">Error: {error}</div>;
  if (!episodes.length) return <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">Loading MITRE data...</div>;

  const tacticCount: Record<string, number> = {};
  const techniqueCount: Record<string, number> = {};
  const techniqueEpisodes: Record<string, string[]> = {};

  episodes.forEach(ep => {
    (ep.sustained_tactics || []).forEach(t => { tacticCount[t] = (tacticCount[t] ?? 0) + 1; });
    (ep.sustained_techniques || []).forEach(t => {
      techniqueCount[t] = (techniqueCount[t] ?? 0) + 1;
      if (!techniqueEpisodes[t]) techniqueEpisodes[t] = [];
      techniqueEpisodes[t].push(ep.episode_id);
    });
  });

  const tactics = Object.entries(tacticCount).sort((a, b) => b[1] - a[1]);
  const techniques = Object.entries(techniqueCount).sort((a, b) => b[1] - a[1]);
  const maxTactic = tactics[0]?.[1] ?? 1;
  const maxTechnique = techniques[0]?.[1] ?? 1;

  const riskColor = (level: string) => {
    if (level === "CRITICAL") return "text-rose-400";
    if (level === "HIGH") return "text-orange-400";
    if (level === "MEDIUM") return "text-yellow-400";
    return "text-emerald-400";
  };

  return (
    <div className="space-y-4">
      {/* KPI strip */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total Episodes", value: episodes.length.toString() },
          { label: "Unique Tactics", value: tactics.length.toString() },
          { label: "Unique Techniques", value: techniques.length.toString() },
          { label: "Top Tactic", value: tactics[0]?.[0]?.split(":")[1]?.trim() ?? "—" },
        ].map(k => (
          <div key={k.label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs font-mono text-slate-400 mb-1">{k.label}</div>
            <div className="text-xl font-mono font-bold text-white truncate">{k.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Tactics */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">TACTIC FREQUENCY</div>
          <div className="space-y-3">
            {tactics.map(([tactic, count]) => {
              const id = tactic.split(":")[0]?.trim();
              const name = tactic.split(":")[1]?.trim() ?? tactic;
              return (
                <div key={tactic} className="flex items-center gap-2">
                  <div className="text-xs font-mono text-cyan-400 w-16 shrink-0">{id}</div>
                  <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"
                      style={{ width: `${(count / maxTactic) * 100}%` }} />
                  </div>
                  <div className="text-xs font-mono text-slate-300 truncate w-32">{name}</div>
                  <div className="text-xs text-slate-500 w-4 text-right">{count}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Techniques */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">TECHNIQUE FREQUENCY</div>
          <div className="space-y-3">
            {techniques.map(([technique, count]) => {
              const id = technique.split(":")[0]?.trim();
              const name = technique.split(":")[1]?.trim() ?? technique;
              const isSelected = selected ? techniqueEpisodes[technique]?.includes(selected) : false;
              return (
                <div key={technique} className={`flex items-center gap-2 rounded-lg px-1 py-0.5 transition-colors ${isSelected ? "bg-slate-700/50" : ""}`}>
                  <div className="text-xs font-mono text-purple-400 w-16 shrink-0">{id}</div>
                  <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                      style={{ width: `${(count / maxTechnique) * 100}%` }} />
                  </div>
                  <div className="text-xs font-mono text-slate-300 truncate w-32">{name}</div>
                  <div className="text-xs text-slate-500 w-4 text-right">{count}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Episode list */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-xs font-mono text-slate-400 mb-3 tracking-wide">EPISODES — click to highlight techniques</div>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {episodes.map(ep => (
            <div key={ep.episode_id}
              onClick={() => setSelected(selected === ep.episode_id ? null : ep.episode_id)}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                selected === ep.episode_id
                  ? "border-cyan-500/50 bg-slate-800/80"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
              }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-cyan-400">{ep.episode_id}</span>
                <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 ${riskColor(ep.peak_risk_level)}`}>
                  {ep.peak_risk_level}
                </span>
                <span className="text-xs font-mono text-slate-500">{ep.start_time?.slice(0, 16)}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {(ep.sustained_techniques || []).map(t => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-purple-300">
                    {t.split(":")[0]?.trim()}
                  </span>
                ))}
                {(ep.sustained_tactics || []).map(t => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-cyan-300">
                    {t.split(":")[0]?.trim()}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
