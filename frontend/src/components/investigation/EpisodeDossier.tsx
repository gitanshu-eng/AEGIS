import React from 'react';
import { ShieldAlert, Clock, ArrowLeft, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';
import type { InvestigationEpisode, LeadLagClassification } from '../../types/aegis';
import { CounterfactualMatrix } from '../simulation/CounterfactualMatrix';
import { Phase6BDefenseExecution } from '../simulation/Phase6BDefenseExecution';
import { useAegisStore } from '../../context/useAegisStore';

interface Props {
  episode: InvestigationEpisode;
}

const AUDIT_BADGES: Record<LeadLagClassification, { label: string; bg: string; text: string; border: string }> = {
  simultaneous: {
    label: 'Simultaneous Breach & Forecast',
    bg: 'bg-blue-950/60',
    text: 'text-blue-400',
    border: 'border-blue-500/40',
  },
  leading: {
    label: 'Leading Warning (Early Forecast)',
    bg: 'bg-emerald-950/60',
    text: 'text-emerald-400',
    border: 'border-emerald-500/40',
  },
  lagging: {
    label: 'Lagging Warning (Post-Onset)',
    bg: 'bg-amber-950/60',
    text: 'text-amber-400',
    border: 'border-amber-500/40',
  },
  indeterminate: {
    label: 'Indeterminate Temporal Alignment',
    bg: 'bg-slate-800/80',
    text: 'text-slate-300',
    border: 'border-slate-600/40',
  },
  f_only_no_physical_breach: {
    label: 'Forecast Only (No Physical Breach)',
    bg: 'bg-purple-950/60',
    text: 'text-purple-300',
    border: 'border-purple-500/40',
  },
  breach_only_no_forecast: {
    label: 'Breach Only (No Forecast Alert)',
    bg: 'bg-rose-950/60',
    text: 'text-rose-400',
    border: 'border-rose-500/40',
  },
};

export const EpisodeDossier: React.FC<Props> = ({ episode }) => {
  const { setNav } = useAegisStore();
  const auditInfo = AUDIT_BADGES[episode.audit_classification];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setNav('COMMAND_CENTER')}
          className="text-xs font-mono text-slate-400 hover:text-[#00f0ff] flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Return to Command Center
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500">Investigation State:</span>
          <span className="text-xs px-2.5 py-0.5 rounded font-mono font-bold bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
            {episode.investigation_state}
          </span>
          <span className="text-[11px] text-slate-400">(Awaiting SOC review)</span>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-slate-800 gap-3">
          <div>
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <h2 className="text-lg font-bold text-white font-mono">{episode.episode_id}</h2>
              <span className="text-xs px-2 py-0.5 rounded bg-rose-950/80 border border-rose-500/40 text-rose-400 font-mono font-bold">
                {episode.severity}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">Dataset Context: {episode.dataset}</p>
          </div>

          <div className={`px-3 py-1.5 rounded-lg border ${auditInfo.bg} ${auditInfo.border} ${auditInfo.text} text-xs font-mono flex items-center gap-2`}>
            <AlertCircle className="w-4 h-4" />
            <span>Audit: {auditInfo.label}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-xs font-mono">
          <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Temporal Window</span>
            <span className="text-slate-200 font-bold flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              {episode.start_time} – {episode.end_time}
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Duration: {episode.duration_minutes} min</span>
          </div>

          <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Peak Risk Score</span>
            <span className="text-white text-base font-bold">{episode.peak_risk} / 100</span>
            <span className="text-[10px] text-rose-400 block mt-0.5">Threshold Exceeded</span>
          </div>

          <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Dominant Signal</span>
            <span className="text-cyan-300 font-semibold">{episode.dominant_signal}</span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Primary Escalator</span>
          </div>

          <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Lead / Lag Delta</span>
            <span className="text-slate-200 font-bold">
              {episode.lead_lag_minutes !== undefined ? `${episode.lead_lag_minutes} min` : 'N/A'}
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">Physical vs Forecast</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80 mb-6">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300 font-mono mb-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            DETERMINISTIC INVESTIGATION NARRATIVE
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">{episode.deterministic_narrative}</p>
        </div>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
              Candidate MITRE ATT&CK Mapping
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono">
              HEURISTIC CONTEXTUAL MAPPING — UNCONFIRMED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {episode.candidate_mitre_techniques.map((tech) => (
              <div
                key={tech.id}
                className="p-3 bg-slate-950/40 border border-slate-800 rounded-lg flex items-center justify-between"
              >
                <div>
                  <span className="text-xs font-mono font-bold text-purple-400 mr-2">{tech.id}</span>
                  <span className="text-xs text-slate-200">{tech.name}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                  Deterministic Context
                </span>
              </div>
            ))}
          </div>
        </div>

        <CounterfactualMatrix episodeId={episode.episode_id} baselineRisk={episode.peak_risk} />
        <Phase6BDefenseExecution baselineRisk={episode.peak_risk} episodeId={episode.episode_id} />

      </div>
    </div>
  );
};
