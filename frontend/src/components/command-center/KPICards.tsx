import React from 'react';
import { Activity, TrendingUp, AlertTriangle, Search } from 'lucide-react';
import type { KPISummary } from '../../types/aegis';

interface Props {
  kpi: KPISummary;
}

export const KPICards: React.FC<Props> = ({ kpi }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      
      {/* 1. Network Activity (Phase 1) */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Network Ingestion</span>
          <Activity className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-2xl font-bold font-mono text-white mb-1">
          {kpi.current_flows_min.toLocaleString()} <span className="text-xs font-normal text-slate-400">flows/min</span>
        </div>
        <div className="text-xs text-slate-400 flex items-center justify-between font-mono pt-2 border-t border-slate-800/80">
          <span>Malicious Traffic Ratio</span>
          <span className="text-amber-400 font-semibold">{(kpi.attack_activity_rate * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* 2. Escalation Forecast (Phase 2) */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Escalation Forecast</span>
          <TrendingUp className="w-4 h-4 text-purple-400" />
        </div>
        <div className="text-2xl font-bold font-mono text-purple-300 mb-1">
          {(kpi.escalation_probability * 100).toFixed(0)}%
        </div>
        <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 leading-relaxed">
          Elevated escalation likelihood based on temporal windowing.
        </div>
      </div>

      {/* 3. Deterministic Risk (Phase 3) */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Deterministic Risk</span>
          <AlertTriangle className="w-4 h-4 text-rose-400" />
        </div>
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-2xl font-bold font-mono text-white">{kpi.risk_score}</span>
          <span className="text-xs font-mono text-slate-500">/ 100</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-rose-950/80 border border-rose-500/40 text-rose-400 font-mono ml-auto">
            {kpi.risk_severity}
          </span>
        </div>
        <div className="grid grid-cols-4 gap-1 pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-400 text-center">
          <div>Fcst: {(kpi.risk_contributors.forecast * 100).toFixed(0)}%</div>
          <div>Act: {(kpi.risk_contributors.activity * 100).toFixed(0)}%</div>
          <div>Vel: {(kpi.risk_contributors.velocity * 100).toFixed(0)}%</div>
          <div>Per: {(kpi.risk_contributors.persistence * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* 4. Active Investigations (Phase 4) */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Triage Queue</span>
          <Search className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-2xl font-bold font-mono text-white">{kpi.active_episodes_count}</span>
          <span className="text-xs text-slate-400">Episodes</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 font-mono ml-auto">
            NEW
          </span>
        </div>
        <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
          Awaiting SOC review. Unverified attack status.
        </div>
      </div>

    </div>
  );
};
