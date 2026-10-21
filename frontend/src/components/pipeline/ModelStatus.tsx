import React from "react";
import { Brain, Activity, CheckCircle2, AlertTriangle, Clock } from "lucide-react";

interface ModelCard {
  name: string;
  role: string;
  architecture: string;
  trainedOn: string;
  status: "ACTIVE" | "STANDBY" | "UNAVAILABLE";
  accuracy: string;
  latency: string;
  note: string;
}

const MODELS: ModelCard[] = [
  {
    name: "GRU v3 (Calibrated)",
    role: "Primary Escalation Forecaster",
    architecture: "Gated Recurrent Unit — 2 layers, 64 hidden units, sigmoid calibration head",
    trainedOn: "CIC-IDS2018 (9 day-splits, LODO cross-validation)",
    status: "ACTIVE",
    accuracy: "AUROC 0.91 (LODO mean)",
    latency: "< 2ms inference",
    note: "Primary forecast signal. Produces calibrated P(Escalation) per 1-min window.",
  },
  {
    name: "Tuned Random Forest",
    role: "Escalation Classifier (Ensemble Fallback)",
    architecture: "Random Forest — 300 estimators, max_depth 12, class_weight balanced",
    trainedOn: "CIC-IDS2018 full corpus",
    status: "ACTIVE",
    accuracy: "F1 0.87 (binary escalation)",
    latency: "< 5ms inference",
    note: "Used as fallback when GRU confidence is low. Also drives risk score ensemble.",
  },
  {
    name: "Delta Forecaster (LSTM)",
    role: "Attack-Rate Change Predictor",
    architecture: "LSTM — 1 layer, 32 units, trained on Δattack_rate sequences",
    trainedOn: "CIC-IDS2018 (walk-forward split)",
    status: "STANDBY",
    accuracy: "MAE 0.031 (normalised delta)",
    latency: "< 3ms inference",
    note: "Predicts rate-of-change. Activates during BREACH_ONLY episodes to supplement GRU.",
  },
  {
    name: "Risk Ensemble Engine",
    role: "Deterministic Risk Scorer",
    architecture: "Weighted linear combiner: 35% forecast + 25% activity + 20% velocity + 20% persistence",
    trainedOn: "No training — deterministic formula",
    status: "ACTIVE",
    accuracy: "Outputs 0–100 risk index",
    latency: "< 0.1ms",
    note: "Always active. Combines all signals into the final risk score displayed in the dashboard.",
  },
  {
    name: "Episode Memory Index",
    role: "Historical Similarity Retrieval",
    architecture: "FAISS flat L2 index over 128-dim episode kinematic vectors",
    trainedOn: "All committed episode dossiers",
    status: "ACTIVE",
    accuracy: "Top-3 recall 0.89",
    latency: "< 1ms lookup",
    note: "Powers Phase 5 memory. Matches live episode morphology against historical clusters.",
  },
];

const STATUS_STYLE = {
  ACTIVE:      { color: "text-emerald-400", bg: "bg-emerald-950/60 border-emerald-500/30", icon: CheckCircle2 },
  STANDBY:     { color: "text-yellow-400",  bg: "bg-yellow-950/60 border-yellow-500/30",  icon: Clock },
  UNAVAILABLE: { color: "text-red-400",     bg: "bg-red-950/60 border-red-500/30",        icon: AlertTriangle },
};

export const ModelStatus: React.FC = () => (
  <div className="space-y-4 font-mono">
    <div className="flex items-center gap-3 mb-2">
      <div className="p-2.5 rounded-lg bg-cyan-950/70 border border-cyan-500/40 text-cyan-400">
        <Brain className="w-5 h-5" />
      </div>
      <div>
        <h2 className="text-base font-bold text-white">Model Registry</h2>
        <p className="text-xs text-slate-400 font-sans">Inference models powering the AEGIS detection pipeline</p>
      </div>
    </div>

    {MODELS.map((m) => {
      const s = STATUS_STYLE[m.status];
      const Icon = s.icon;
      return (
        <div key={m.name} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400 shrink-0" />
              <span className="text-sm font-bold text-white">{m.name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 border border-purple-500/40 text-purple-300">
                {m.role}
              </span>
            </div>
            <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded border ${s.bg} ${s.color} shrink-0`}>
              <Icon className="w-3 h-3" /> {m.status}
            </span>
          </div>

          <p className="text-xs text-slate-400 font-sans">{m.architecture}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
            {[
              { label: "Trained On", value: m.trainedOn },
              { label: "Performance", value: m.accuracy },
              { label: "Latency", value: m.latency },
              { label: "Note", value: m.note },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-950/70 rounded-lg border border-slate-800 p-2.5">
                <span className="text-slate-500 uppercase tracking-wider text-[9px] font-bold block mb-1">{label}</span>
                <span className="text-slate-300 font-sans leading-snug">{value}</span>
              </div>
            ))}
          </div>
        </div>
      );
    })}
  </div>
);
