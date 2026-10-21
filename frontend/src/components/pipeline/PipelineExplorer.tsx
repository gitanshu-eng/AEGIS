import React from 'react';
import { FileCode, Database, CheckCircle2, Terminal } from 'lucide-react';
import { useAegisStore } from '../../context/useAegisStore';

interface FileContract {
  file: string;
  phase: string;
  description: string;
  inputs: string[];
  outputs: string[];
  codePreview: string;
}

const CONTRACTS: Record<string, FileContract> = {
  'build_continuous_temporal.py': {
    file: 'build_continuous_temporal.py',
    phase: 'Phase 1: Continuous Ingestion',
    description: 'Constructs the unbroken 1-minute temporal grid, identifying missing packet windows and unobserved capture gaps.',
    inputs: ['data/raw/CIC-IDS2018/*.csv'],
    outputs: ['data/processed/{dataset}_temporal_continuous.csv'],
    codePreview: `# Phase 1 Temporal Ingestion Grid Builder
import pandas as pd
import numpy as np

def build_continuous_grid(raw_df: pd.DataFrame, freq='1min'):
    raw_df['timestamp'] = pd.to_datetime(raw_df['Timestamp'])
    full_idx = pd.date_range(raw_df['timestamp'].min(), raw_df['timestamp'].max(), freq=freq)
    grid = raw_df.set_index('timestamp').reindex(full_idx)
    grid['network_state'] = np.where(grid['total_flows'].isna(), 'UNOBSERVED', 'OBSERVED')
    return grid.fillna(0)`
  },
  'temporal_features.py': {
    file: 'temporal_features.py',
    phase: 'Phase 1: Feature Engineering',
    description: 'Calculates rolling flow velocity, Forward Inter-Arrival Time (IAT), and persistence counters.',
    inputs: ['data/processed/{dataset}_temporal_continuous.csv'],
    outputs: ['data/processed/{dataset}_temporal.csv'],
    codePreview: `# Temporal Rolling Window Signals
def extract_temporal_signals(df):
    df['flow_velocity'] = df['total_flows'].pct_change(periods=3)
    df['mean_fiat'] = df['fwd_iat_mean'].rolling(5).mean()
    df['persistence_score'] = (df['attack_ratio'] > 0.05).rolling(4).sum()
    return df`
  },
  'forecasting_model.py': {
    file: 'forecasting_model.py',
    phase: 'Phase 2: Escalation Forecasting',
    description: 'Executes the walk-forward XGBoost model to output calibrated P(Escalation) probability ahead of breach onset.',
    inputs: ['data/processed/{dataset}_temporal.csv'],
    outputs: ['data/processed/{dataset}_predictions.csv'],
    codePreview: `# XGBoost Escalation Predictor
import xgboost as xgb

def forecast_escalation(features):
    model = xgb.Booster()
    model.load_model('outputs/models/xgb_escalation.json')
    dmatrix = xgb.DMatrix(features)
    p_escalation = model.predict(dmatrix)
    return p_escalation`
  },
  'risk_engine.py': {
    file: 'risk_engine.py',
    phase: 'Phase 3: Deterministic Scoring',
    description: 'Ensemble score synthesizer combining activity, velocity, persistence, and forecast into a 0-100 deterministic risk index.',
    inputs: ['data/processed/{dataset}_predictions.csv'],
    outputs: ['data/processed/{dataset}_risk.csv'],
    codePreview: `# Deterministic Ensemble Risk Synthesizer
def compute_risk(row):
    r_forecast = 0.35 * row['p_escalation']
    r_activity = 0.25 * row['attack_activity_rate']
    r_velocity = 0.20 * min(row['flow_velocity'], 1.0)
    r_persistence = 0.20 * (row['persistence_score'] / 4.0)
    return int(round((r_forecast + r_activity + r_velocity + r_persistence) * 100))`
  },
  'evidence_builder.py': {
    file: 'evidence_builder.py',
    phase: 'Phase 4: Episode Forensic Dossiers',
    description: 'Clusters contiguous incident spikes into Investigation Episodes and audits physical breach onset vs. forecast warning.',
    inputs: ['data/processed/{dataset}_risk.csv'],
    outputs: ['data/processed/{dataset}_evidence.csv'],
    codePreview: `# Incident Clusterer & Lead/Lag Auditor
def cluster_episodes(risk_series, threshold=60):
    episodes = []
    return episodes`
  },
  'episode_memory.py': {
    file: 'episode_memory.py',
    phase: 'Phase 5: Historical Memory',
    description: 'Vector embeddings similarity retrieval matching ongoing attack morphology against historical episode clusters.',
    inputs: ['data/processed/{dataset}_evidence.csv'],
    outputs: ['outputs/memory/episode_index.faiss'],
    codePreview: `# Historical Similarity Engine
def match_historical(current_episode_vector, index, top_k=3):
    D, I = index.search(current_episode_vector, top_k)
    return I, D`
  },
  'counterfactual_engine.py': {
    file: 'counterfactual_engine.py',
    phase: 'Phase 6A: Counterfactual Simulation',
    description: 'Simulates hypothetical intervention outcomes (Rate Limiting, VLAN Shift, Rule Drops) generating min/expected/max risk bounds.',
    inputs: ['data/processed/{dataset}_evidence.csv'],
    outputs: ['outputs/simulations/counterfactual_matrix.json'],
    codePreview: `# What-If Hypothetical Risk Reductions
def simulate_mitigation(action, baseline_risk):
    delta = PLAYBOOK[action]['delta']
    return baseline_risk - delta`
  },
  'autonomous_defense.py': {
    file: 'autonomous_defense.py',
    phase: 'Phase 6B: Active Defense Enforcement',
    description: 'Dispatches concrete firewall drop rules, VLAN port shifts, and Linux traffic control (tc) token bucket constraints.',
    inputs: ['SOC Authorization Signal'],
    outputs: ['outputs/defense/enforcement_ledger.json'],
    codePreview: `# Active Defense Dispatcher
import subprocess

def apply_countermeasure(cmd):
    res = subprocess.run(cmd.split(), capture_output=True)
    return res.returncode == 0`
  },
  'live_defense_gateway.py': {
    file: 'live_defense_gateway.py',
    phase: 'Phase 7: Live Lab Verification',
    description: 'Captures genuine post-mitigation telemetry from the live testbed subnet to verify real-world risk reduction.',
    inputs: ['Live Telemetry Tap (172.31.32.0/24)'],
    outputs: ['outputs/live_lab/execution_ledger.json'],
    codePreview: `# Real-Time Verification Sniffer
def verify_mitigation(pre_risk, duration=60):
    post_telemetry = sniff_subnet('172.31.32.0/24', duration=duration)
    post_risk = calculate_current_risk(post_telemetry)
    return {'pre': pre_risk, 'post': post_risk, 'status': 'VERIFIED_EFFECTIVE'}`
  },
};

export const PipelineExplorer: React.FC = () => {
  const { selectedSourceFile } = useAegisStore();
  const contract = CONTRACTS[selectedSourceFile] || CONTRACTS['forecasting_model.py'];

  return (
    <div className="space-y-6 font-mono">
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-950/70 border border-purple-500/40 text-purple-400">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">{contract.file}</h2>
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 border border-purple-500/40 text-purple-300">
                  {contract.phase}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-sans">{contract.description}</p>
            </div>
          </div>

          <div className="text-xs text-slate-400">
            Source Path: <code className="text-cyan-300 font-bold">/opt/aegis/src/{contract.file}</code>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6 text-xs">
          <div className="p-3.5 bg-slate-950/70 rounded-lg border border-slate-800">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold block mb-1.5 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              Pipeline Inputs
            </span>
            <ul className="space-y-1 text-slate-300">
              {contract.inputs.map((inp, idx) => (
                <li key={idx} className="font-mono bg-slate-900 px-2 py-1 rounded border border-slate-800">
                  {inp}
                </li>
              ))}
            </ul>
          </div>

          <div className="p-3.5 bg-slate-950/70 rounded-lg border border-slate-800">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold block mb-1.5 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Pipeline Outputs / Artifacts
            </span>
            <ul className="space-y-1 text-slate-300">
              {contract.outputs.map((out, idx) => (
                <li key={idx} className="font-mono bg-slate-900 px-2 py-1 rounded border border-slate-800 text-emerald-300">
                  {out}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between pb-2 mb-2 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-purple-400" />
              Core Execution Logic
            </span>
            <span className="text-[10px] text-slate-500">Python 3.11</span>
          </div>
          <pre className="p-4 rounded-lg bg-black/80 border border-slate-800 text-xs text-slate-200 overflow-x-auto leading-relaxed">
            <code>{contract.codePreview}</code>
          </pre>
        </div>

      </div>
    </div>
  );
};
