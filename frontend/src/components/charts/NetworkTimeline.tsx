import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot,
} from 'recharts';
import type { NetworkTimelinePoint } from '../../types/aegis';
import { useAegisStore } from '../../context/useAegisStore';

interface Props {
  data: NetworkTimelinePoint[];
}

export const NetworkTimeline: React.FC<Props> = ({ data }) => {
  const { selectEpisode } = useAegisStore();

  const episodePoints = data.filter((d) => d.episode_id);

  return (
    <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md mb-6">
      {/* Chart Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-slate-800/80 gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wider uppercase text-white flex items-center gap-2">
            <span>Network Behavior & Risk Timeline</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">1-MIN RESOLUTION</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Synchronized ingestion volume, Phase 2 predictive forecast, and Phase 3 deterministic risk curves.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/30 border border-rose-500/80 inline-block" />
            Attack Rate
          </span>
          <span className="flex items-center gap-1.5 text-purple-400">
            <span className="w-3 h-0.5 bg-purple-400 inline-block" />
            P(Escalation)
          </span>
          <span className="flex items-center gap-1.5 text-cyan-400">
            <span className="w-3 h-0.5 bg-cyan-400 inline-block" />
            Risk Score
          </span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="w-2 h-2 rounded-full bg-amber-400 inline-block ring-2 ring-white/20" />
            Episode Marker
          </span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="attackGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="timestamp" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} domain={[0, 100]} />

            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                const point = payload[0].payload as NetworkTimelinePoint;

                return (
                  <div className="p-3 bg-[#070a13] border border-slate-700 rounded-lg shadow-2xl text-xs font-mono">
                    <div className="text-slate-400 font-bold mb-2 pb-1 border-b border-slate-800 flex justify-between gap-4">
                      <span>Window: {label} UTC</span>
                      <span className={point.network_state === 'OBSERVED' ? 'text-emerald-400' : 'text-amber-400'}>
                        {point.network_state}
                      </span>
                    </div>

                    {point.network_state === 'UNOBSERVED' ? (
                      <div className="text-amber-300 text-[11px] py-1">
                        Notice: {point.gap_reason || 'No telemetry captured'}
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <div className="flex justify-between gap-4">
                          <span className="text-slate-400">Total Flows:</span>
                          <span className="text-white font-semibold">{point.total_flows.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between gap-4 text-rose-400">
                          <span>Attack Rate:</span>
                          <span>{(point.attack_rate * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between gap-4 text-purple-400">
                          <span>Forecast Prob:</span>
                          <span>{(point.escalation_forecast * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between gap-4 text-cyan-400">
                          <span>Risk Score:</span>
                          <span className="font-bold">{point.risk_score} / 100</span>
                        </div>
                        {point.episode_id && (
                          <div className="mt-2 pt-1.5 border-t border-slate-800 text-amber-300 font-bold flex items-center justify-between">
                            <span>Episode Attached:</span>
                            <span className="underline cursor-pointer">{point.episode_id}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              }}
            />

            <Area
              type="monotone"
              dataKey={(d: NetworkTimelinePoint) => d.attack_rate * 100}
              stroke="#ef4444"
              strokeWidth={1.5}
              fill="url(#attackGrad)"
              name="Attack Rate"
            />

            <Line
              type="monotone"
              dataKey={(d: NetworkTimelinePoint) => d.escalation_forecast * 100}
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              name="Forecast"
            />

            <Line
              type="monotone"
              dataKey="risk_score"
              stroke="#00f0ff"
              strokeWidth={2}
              dot={false}
              name="Risk"
            />

            {episodePoints.map((pt, idx) => (
              <ReferenceDot
                key={idx}
                x={pt.timestamp}
                y={pt.risk_score}
                r={6}
                fill="#f59e0b"
                stroke="#ffffff"
                strokeWidth={2}
                className="cursor-pointer transition-transform hover:scale-125"
                onClick={() => pt.episode_id && selectEpisode(pt.episode_id)}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[11px] text-slate-500 mt-2 font-mono flex items-center justify-between">
        <span>Click any amber marker to load the full Level 3 forensic dossier.</span>
        <span>Deterministic XGBoost + Heuristic Ensemble</span>
      </div>
    </div>
  );
};
