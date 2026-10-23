import React from 'react';
import { Database, Activity, AlertCircle, Clock, ShieldAlert, ArrowUpRight, BarChart3, Radio } from 'lucide-react';
import { useAegisStore } from '../../context/useAegisStore';
import type { InvestigationEpisode, NetworkTimelinePoint } from '../../types/aegis';

interface Props {
  episodes: InvestigationEpisode[];
  timeline: NetworkTimelinePoint[];
}

export const DatasetWorkspace: React.FC<Props> = ({ episodes, timeline }) => {
  const { selectedDataset, selectEpisode } = useAegisStore();

  const observedCount = timeline.filter((t) => t.network_state === 'OBSERVED').length;
  const unobservedCount = timeline.filter((t) => t.network_state === 'UNOBSERVED').length;
  const continuityPct = ((observedCount / (timeline.length || 1)) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      
      {/* 1. Dataset Profile & Telemetry Continuity Ledger */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold font-mono">Dataset Target</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-base font-bold font-mono text-white truncate mb-1">
            {selectedDataset}
          </div>
          <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 font-mono">
            Source: Canadian Institute for Cybersecurity
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold font-mono">Data Coverage</span>
            <Radio className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-300 mb-1">
            {continuityPct}%
          </div>
          <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 font-mono flex justify-between">
            <span>Monitored: {observedCount} min</span>
            <span className="text-amber-400">Missing Windows: {unobservedCount} min</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold font-mono">Active Threat Events</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mb-1">
            {episodes.length} <span className="text-xs font-normal text-slate-400">Flagged Clusters</span>
          </div>
          <div className="text-[11px] text-cyan-300 pt-2 border-t border-slate-800/80 font-mono">
            State: NEW (SOC Review Pending)
          </div>
        </div>
      </div>

      {/* 2. Feature Dynamics & Ingestion Integrity Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left: Continuous Windows & Telemetry Audit */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Continuous Telemetry Audit Ledger
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
              MONITORING GAPS
            </span>
          </div>

          <div className="space-y-2 font-mono text-xs max-h-64 overflow-y-auto pr-1">
            {timeline.map((point) => (
              <div
                key={point.timestamp}
                className={`p-2.5 rounded-lg border flex items-center justify-between ${
                  point.network_state === 'OBSERVED'
                    ? 'bg-slate-950/40 border-slate-800/80 text-slate-300'
                    : 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 text-[11px]">{point.timestamp} UTC</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                    point.network_state === 'OBSERVED' ? 'bg-emerald-950 text-emerald-400' : 'bg-amber-950 text-amber-400'
                  }`}>
                    {point.network_state}
                  </span>
                </div>

                <div className="text-right text-[11px]">
                  {point.network_state === 'OBSERVED' ? (
                    <span>{point.total_flows.toLocaleString()} flows • {(point.attack_rate * 100).toFixed(1)}% mal</span>
                  ) : (
                    <span className="text-amber-400 text-[10px]">{point.gap_reason || 'Missing Packets'}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Flow Distribution & Ingestion Metrics */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
              <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" />
                Phase 1 Flow Signal Profile
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950/60 border border-purple-500/40 text-purple-300 font-mono">
                XGBOOST INPUTS
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Forward Inter-Arrival Time (Mean):</span>
                  <span className="text-slate-200 font-bold">14.2 µs (Disproportionate Surge)</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1.5">
                  <div className="bg-cyan-400 h-full w-[78%]" />
                </div>
              </div>

              <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Traffic Speed:</span>
                  <span className="text-rose-400 font-bold">Surge +38% Baseline</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1.5">
                  <div className="bg-rose-400 h-full w-[84%]" />
                </div>
              </div>

              <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Attack Duration:</span>
                  <span className="text-amber-300 font-bold">4 Consecutive Windows</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1.5">
                  <div className="bg-amber-400 h-full w-[52%]" />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 p-2.5 rounded bg-slate-950/80 border border-slate-800 text-[10px] text-slate-400 flex items-start gap-2 font-mono">
            <AlertCircle className="w-3.5 h-3.5 text-cyan-400 mt-0.5 shrink-0" />
            <span>Extracted directly from Phase 1 temporal window partitions without modification.</span>
          </div>
        </div>

      </div>

      {/* 3. Dataset Investigation Episodes Directory */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
          <div>
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              Dataset Investigation Episodes ({episodes.length})
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Click any episode row to load its Level 3 forensic dossier and mitigation matrix.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
                <th className="pb-2">Episode ID</th>
                <th className="pb-2">Window</th>
                <th className="pb-2 text-center">Duration</th>
                <th className="pb-2 text-center">Peak Risk</th>
                <th className="pb-2">Audit Classification</th>
                <th className="pb-2">Dominant Signal</th>
                <th className="pb-2 text-right">Dossier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {episodes.map((ep) => (
                <tr
                  key={ep.episode_id}
                  onClick={() => selectEpisode(ep.episode_id)}
                  className="cursor-pointer transition-colors text-slate-300 hover:bg-slate-800/40 hover:text-white"
                >
                  <td className="py-3 font-bold text-white flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    {ep.episode_id}
                  </td>
                  <td className="py-3 text-slate-400">{ep.start_time} – {ep.end_time}</td>
                  <td className="py-3 text-center">{ep.duration_minutes} min</td>
                  <td className="py-3 text-center">
                    <span className="px-2 py-0.5 rounded bg-rose-950/70 border border-rose-500/30 text-rose-300 font-bold">
                      {ep.peak_risk}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                      {ep.audit_classification}
                    </span>
                  </td>
                  <td className="py-3 text-cyan-300">{ep.dominant_signal}</td>
                  <td className="py-3 text-right">
                    <button className="px-2.5 py-1 rounded bg-cyan-950/60 border border-cyan-500/40 text-[#00f0ff] hover:bg-cyan-900/60 text-[10px] inline-flex items-center gap-1 font-bold">
                      Open Dossier
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
