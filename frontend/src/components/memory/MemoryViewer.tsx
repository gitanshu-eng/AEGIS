import React, { useEffect, useState } from "react";
import { API, API_KEY } from "../../api/client";
import { Database, Clock, Shield, Activity } from "lucide-react";

interface MemoryRecord {
  id: string;
  signature: string;
  dataset_origin: string;
  context: string;
  peak_risk_level: string;
  sustained_tactics: string[];
  similarity: number | null;
  kinematic_vector: number[];
}

interface MemoryViewerProps {
  dataset: string;
}

export const MemoryViewer: React.FC<MemoryViewerProps> = ({ dataset }) => {
  const [records, setRecords] = useState<MemoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataset) return;
    setLoading(true);
    setError(null);
    fetch(`${API}/api/memory?dataset=${encodeURIComponent(dataset)}`, {
      headers: { Accept: "application/json", "X-API-Key": API_KEY },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: MemoryRecord[]) => setRecords(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [dataset]);

  const riskColor = (level: string) => {
    if (level === "CRITICAL") return "text-rose-400";
    if (level === "HIGH") return "text-orange-400";
    if (level === "MEDIUM") return "text-amber-400";
    return "text-emerald-400";
  };

  if (loading) return (
    <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">
      Loading Phase 5 Historical Memory...
    </div>
  );

  if (error) return (
    <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs font-mono text-rose-300">
      Memory store error: {error}
    </div>
  );

  if (records.length === 0) return (
    <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-mono text-slate-400">
      No Phase 5 memory records found for dataset: {dataset}. This dataset may not have been ingested during Phase 5 processing, or may use a different naming convention in the memory store.
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2.5 rounded-lg bg-purple-900/60 border border-purple-500/40 text-purple-300">
          <Database className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-white font-mono tracking-wide">
            PHASE 5 � HISTORICAL EPISODE MEMORY
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {records.length} memory records loaded � Source: phase5_memory_store.json � Data: HISTORICAL BATCH
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {records.map((rec, idx) => (
          <div
            key={rec.id || idx}
            className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-xs font-mono font-bold text-cyan-400 truncate max-w-[200px]">
                  {rec.signature || rec.id}
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  Origin: {rec.dataset_origin || "unknown"}
                </div>
              </div>
              <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 ${riskColor(rec.peak_risk_level)}`}>
                {rec.peak_risk_level || "UNKNOWN"}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-400">
                <Clock className="w-3 h-3 shrink-0" />
                <span>Lead/Lag: <span className="text-slate-200">{rec.context || "indeterminate"}</span></span>
              </div>

              {rec.similarity !== null && rec.similarity !== undefined && (
                <div className="flex items-center gap-2 text-slate-400">
                  <Activity className="w-3 h-3 shrink-0" />
                  <span>Similarity Score: </span>
                  <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"
                      style={{ width: `${Math.min(100, (rec.similarity ?? 0) * 100)}%` }}
                    />
                  </div>
                  <span className="text-cyan-300">{((rec.similarity ?? 0) * 100).toFixed(1)}%</span>
                </div>
              )}

              {rec.sustained_tactics?.length > 0 && (
                <div className="flex items-start gap-2 text-slate-400">
                  <Shield className="w-3 h-3 shrink-0 mt-0.5" />
                  <div className="flex flex-wrap gap-1">
                    {rec.sustained_tactics.slice(0, 4).map((t, i) => (
                      <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-300">
                        {t}
                      </span>
                    ))}
                    {rec.sustained_tactics.length > 4 && (
                      <span className="text-[10px] text-slate-500">+{rec.sustained_tactics.length - 4} more</span>
                    )}
                  </div>
                </div>
              )}

              {rec.kinematic_vector?.length > 0 && (
                <div className="text-[10px] text-slate-600 font-mono mt-1">
                  Vector dim: {rec.kinematic_vector.length}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

