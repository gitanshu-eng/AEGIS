import React, { useState, useEffect } from "react";
import { History, Cpu, ShieldCheck, Loader2 } from "lucide-react";

interface SimulationRecord {
  simulation_id: string;
  name: string;
  description: string;
  baseline_risk: number;
  simulated_risk: number;
  delta: number;
  risk_reduction_pct: number;
  source_dataset: string;
  source_episode_id: string;
}

interface MemoryRecord {
  id: string;
  signature: string;
  dataset_origin: string;
  context: string;
  peak_risk_level: string;
  similarity: number | null;
  sustained_tactics: string[];
}

interface Props {
  episodeId: string;
  baselineRisk: number;
  dataset?: string;
}

export const CounterfactualMatrix: React.FC<Props> = ({
  episodeId,
  baselineRisk,
  dataset = "cic_ids2017",
}) => {
  const [simulations, setSimulations] = useState<SimulationRecord[]>([]);
  const [memory, setMemory] = useState<MemoryRecord[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loadingSim, setLoadingSim] = useState(true);
  const [loadingMem, setLoadingMem] = useState(true);
  const [simError, setSimError] = useState<string | null>(null);

  useEffect(() => {
    setLoadingSim(true);
    setSimError(null);
    fetch(`http://localhost:8000/api/simulations?dataset=${encodeURIComponent(dataset)}`, {
      headers: { Accept: "application/json" },
    })
      .then((r) => r.json())
      .then((data: SimulationRecord[]) => {
        setSimulations(data);
        if (data.length > 0) setSelected(data[0].name);
      })
      .catch((e) => setSimError(e.message))
      .finally(() => setLoadingSim(false));
  }, [dataset]);

  useEffect(() => {
    setLoadingMem(true);
    fetch(`http://localhost:8000/api/memory?dataset=${encodeURIComponent(dataset)}`, {
      headers: { Accept: "application/json" },
    })
      .then((r) => r.json())
      .then((data: MemoryRecord[]) => setMemory(data))
      .catch(() => setMemory([]))
      .finally(() => setLoadingMem(false));
  }, [dataset]);

  const activeSim = simulations.find((s) => s.name === selected) || simulations[0];
  const topMemory = memory.length > 0 ? memory[0] : null;
  const similarityPct = topMemory?.similarity != null
    ? Math.round(topMemory.similarity * 100)
    : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">

      {/* Phase 5 Historical Similarity Panel */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300 font-mono">
              <History className="w-4 h-4 text-cyan-400" />
              HISTORICAL SIMILARITY (PHASE 5)
            </div>
            {similarityPct !== null && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-500/40 text-cyan-300 font-mono">
                {similarityPct}% MATCH
              </span>
            )}
          </div>

          {loadingMem ? (
            <div className="text-xs font-mono text-slate-500 animate-pulse">Loading memory...</div>
          ) : topMemory ? (
            <div className="space-y-3 text-xs font-mono">
              <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800/80">
                <span className="text-slate-500 block mb-0.5">Matched Prior Episode:</span>
                <span className="text-white font-bold truncate block">{topMemory.signature}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800/80">
                  <span className="text-slate-500 block text-[10px]">Risk Level:</span>
                  <span className="text-slate-200 font-semibold">{topMemory.peak_risk_level}</span>
                </div>
                <div className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800/80">
                  <span className="text-slate-500 block text-[10px]">Lead/Lag:</span>
                  <span className="text-slate-200 font-semibold text-[10px]">{topMemory.context || "INDETERMINATE"}</span>
                </div>
              </div>
              {topMemory.sustained_tactics?.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {topMemory.sustained_tactics.slice(0, 3).map((t, i) => (
                    <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-[10px] text-amber-400/80 mt-2 leading-relaxed">
                Notice: Similar historical behavior denotes pattern correlation only; it does not confirm identical threat actor or technique.
              </p>
            </div>
          ) : (
            <div className="text-xs font-mono text-slate-500 mt-2">
              No historical memory records for this dataset.
            </div>
          )}
        </div>
      </div>

      {/* Phase 6 Counterfactual Simulation Panel */}
      <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 mb-4 border-b border-slate-800 gap-2">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-white font-mono">
              <Cpu className="w-4 h-4 text-purple-400" />
              COUNTERFACTUAL SIMULATION MATRIX (PHASE 6)
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Comparative impact estimation across candidate intervention protocols.
            </p>
          </div>
          <span className="text-[10px] px-2.5 py-1 rounded bg-purple-950/70 border border-purple-500/40 text-purple-300 font-mono font-bold tracking-tight">
            MODEL-BASED HYPOTHETICAL SIMULATION
          </span>
        </div>

        {loadingSim ? (
          <div className="flex items-center gap-2 text-xs font-mono text-slate-500 animate-pulse py-8 justify-center">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading Phase 6 simulations...
          </div>
        ) : simError ? (
          <div className="text-xs font-mono text-rose-400 py-4">Error: {simError}</div>
        ) : simulations.length === 0 ? (
          <div className="py-8 text-center text-xs font-mono text-slate-500">
            <p>No simulation records found for <span className="text-cyan-400">{dataset}</span>.</p>
            <p className="mt-1 text-[10px] text-slate-600">Phase 6 simulations have only been generated for CIC-IDS2018 Mar 02 dataset.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto mb-4">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
                    <th className="pb-2">Intervention Strategy</th>
                    <th className="pb-2 text-center">Baseline</th>
                    <th className="pb-2 text-center text-cyan-400">Simulated Risk</th>
                    <th className="pb-2 text-center">Reduction</th>
                    <th className="pb-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {simulations.map((item) => (
                    <tr
                      key={item.simulation_id + item.name}
                      onClick={() => setSelected(item.name)}
                      className={`cursor-pointer transition-colors ${
                        selected === item.name
                          ? "bg-cyan-950/30 text-white"
                          : "text-slate-300 hover:bg-slate-800/40"
                      }`}
                    >
                      <td className="py-2.5 flex items-center gap-2 font-medium">
                        {selected === item.name && (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff]" />
                        )}
                        {item.name}
                      </td>
                      <td className="py-2.5 text-center text-slate-400">
                        {item.baseline_risk?.toFixed(1)}
                      </td>
                      <td className="py-2.5 text-center font-bold text-cyan-300">
                        {item.simulated_risk?.toFixed(1)}
                      </td>
                      <td className="py-2.5 text-center text-emerald-400">
                        {item.risk_reduction_pct != null
                          ? `${item.risk_reduction_pct.toFixed(1)}%`
                          : "-"}
                      </td>
                      <td className="py-2.5 text-right">
                        <span className="text-[10px] px-2 py-0.5 rounded border border-slate-700 bg-slate-800 text-slate-300">
                          Simulate
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {activeSim && (
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-slate-400 block text-[11px]">
                    Projected Outcome: {activeSim.name}
                  </span>
                  <span className="text-slate-200">
                    Baseline Risk:{" "}
                    <strong className="text-rose-400">
                      {activeSim.baseline_risk?.toFixed(1)}
                    </strong>{" "}
                    → Expected Post-Mitigation:{" "}
                    <strong className="text-cyan-300">
                      {activeSim.simulated_risk?.toFixed(1)}
                    </strong>
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-bold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>
                    Δ {activeSim.delta != null ? activeSim.delta.toFixed(2) : "-"} Points
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};