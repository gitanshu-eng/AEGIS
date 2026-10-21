import { create } from 'zustand';
import { AEGIS_DATASETS } from '../types/aegis';
import type { NavItem, DataMode, AegisDataset, ScenarioRunState, PhaseExecutionStep } from '../types/aegis';

const INITIAL_STEPS: PhaseExecutionStep[] = [
  { phase_number: 'P01', name: 'Continuous Ingestion', tagline: '1-min grid construction & gap integrity validation', status: 'COMPLETED', runtime_ms: 212, summary_metric: '14,280 flows/min • 90.9% continuity', artifact_path: 'data/processed/{dataset}_temporal_continuous.csv', source_file: 'build_continuous_temporal.py' },
  { phase_number: 'P02', name: 'Escalation Forecast', tagline: 'Temporal window feature engineering & XGBoost forecasting', status: 'COMPLETED', runtime_ms: 259, summary_metric: 'P(Escalation) = 0.72 • Leading warning', artifact_path: 'data/processed/{dataset}_predictions.csv', source_file: 'forecasting_model.py' },
  { phase_number: 'P03', name: 'Deterministic Scoring', tagline: 'Ensemble risk calculation (Activity + Velocity + Persistence)', status: 'COMPLETED', runtime_ms: 383, summary_metric: 'Peak Risk: 78 / 100 [HIGH]', artifact_path: 'data/processed/{dataset}_risk.csv', source_file: 'risk_engine.py' },
  { phase_number: 'P04', name: 'Investigation & MITRE', tagline: 'Episode clustering, Lead/Lag audit, and heuristic TTP tags', status: 'COMPLETED', runtime_ms: 386, summary_metric: '2 Episodes • Simultaneous audit tag', artifact_path: 'data/processed/{dataset}_evidence.csv', source_file: 'evidence_builder.py' },
  { phase_number: 'P05', name: 'Historical Memory', tagline: 'K-NN vector correlation over prior SOC incident clusters', status: 'COMPLETED', runtime_ms: 289, summary_metric: 'Matched: EP-Thursday-15-02-2018 (87%)', artifact_path: 'outputs/memory/episode_index.faiss', source_file: 'episode_memory.py' },
  { phase_number: 'P06A', name: 'Counterfactual Matrix', tagline: 'Hypothetical intervention modeling (Token bucket vs Isolation)', status: 'COMPLETED', runtime_ms: 395, summary_metric: 'Max risk delta: -47 pts projected', artifact_path: 'outputs/simulations/counterfactual_matrix.json', source_file: 'counterfactual_engine.py' },
  { phase_number: 'P06B', name: 'Active Defense Mode', tagline: 'Concrete firewall rule dispatch & container VLAN isolation', status: 'COMPLETED', runtime_ms: 120, summary_metric: 'Active Defense Playbook Enforced', artifact_path: 'outputs/defense/enforcement_ledger.json', source_file: 'autonomous_defense.py' },
  { phase_number: 'P07', name: 'Live Lab Verification', tagline: 'SOC gated testbed deployment & post-mitigation telemetry capture', status: 'COMPLETED', runtime_ms: 468, summary_metric: 'REAL_OBSERVED: Verified Effective (29 risk)', artifact_path: 'outputs/live_lab/execution_ledger.json', source_file: 'live_defense_gateway.py' },
];

export interface AegisState {
  currentNav: NavItem;
  selectedDataset: AegisDataset;
  selectedEpisodeId: string | null;
  selectedSourceFile: string;
  dataMode: DataMode;
  scenario: ScenarioRunState;
  setNav: (nav: NavItem) => void;
  selectDataset: (dataset: AegisDataset) => void;
  selectEpisode: (episodeId: string | null) => void;
  setSelectedSourceFile: (file: string) => void;
  setDataMode: (mode: DataMode) => void;
  runScenario: (dataset: AegisDataset) => void;
}

export const useAegisStore = create<AegisState>((set, get) => ({
  currentNav: 'COMMAND_CENTER',
  selectedDataset: AEGIS_DATASETS[0], // cic_ids2017
  selectedEpisodeId: null,
  selectedSourceFile: 'forecasting_model.py',
  dataMode: 'DEMO',
  scenario: {
    dataset: AEGIS_DATASETS[0],
    isRunning: false,
    activePhase: 'P07',
    progressPercent: 100,
    startedAt: new Date(Date.now() - 3600000).toISOString(),
    completedAt: new Date().toISOString(),
    steps: INITIAL_STEPS.map((s) => ({
      ...s,
      artifact_path: s.artifact_path?.replace('{dataset}', AEGIS_DATASETS[2]),
    })),
  },
  setNav: (nav) => set({ currentNav: nav }),
  selectDataset: (dataset) => {
    set({ selectedDataset: dataset, selectedEpisodeId: null });
    get().runScenario(dataset);
  },
  selectEpisode: (episodeId) => set({ 
    selectedEpisodeId: episodeId, 
    currentNav: 'INVESTIGATE_EPISODES',
  }),
  setSelectedSourceFile: (file) => set({ selectedSourceFile: file }),
  setDataMode: (mode) => set({ dataMode: mode }),
  runScenario: (dataset) => {
    const freshSteps: PhaseExecutionStep[] = INITIAL_STEPS.map((s) => ({
      ...s,
      status: 'PENDING',
      runtime_ms: undefined,
      artifact_path: s.artifact_path?.replace('{dataset}', dataset),
    }));

    set({
      scenario: {
        dataset,
        isRunning: true,
        activePhase: 'P01',
        progressPercent: 5,
        startedAt: new Date().toISOString(),
        completedAt: undefined,
        steps: freshSteps,
      },
    });

    freshSteps.forEach((step, idx) => {
      setTimeout(() => {
        set((state) => {
          const updatedSteps = [...state.scenario.steps];
          if (idx > 0) {
            updatedSteps[idx - 1] = {
              ...updatedSteps[idx - 1],
              status: 'COMPLETED',
              runtime_ms: 180 + Math.floor(Math.random() * 250),
            };
          }
          updatedSteps[idx] = {
            ...updatedSteps[idx],
            status: 'RUNNING',
          };

          const progress = Math.round(((idx + 1) / freshSteps.length) * 100);

          return {
            scenario: {
              ...state.scenario,
              activePhase: step.phase_number,
              progressPercent: progress,
              steps: updatedSteps,
            },
          };
        });

        if (idx === freshSteps.length - 1) {
          setTimeout(() => {
            set((state) => {
              const finalizedSteps = [...state.scenario.steps];
              finalizedSteps[idx] = {
                ...finalizedSteps[idx],
                status: 'COMPLETED',
                runtime_ms: 220 + Math.floor(Math.random() * 200),
              };
              return {
                scenario: {
                  ...state.scenario,
                  isRunning: false,
                  activePhase: 'P07',
                  progressPercent: 100,
                  completedAt: new Date().toISOString(),
                  steps: finalizedSteps,
                },
              };
            });
          }, 350);
        }
      }, idx * 350);
    });
  },
}));
