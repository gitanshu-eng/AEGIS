export type DataMode = 'DEMO' | 'API';

export type NavItem =
  | 'COMMAND_CENTER'
  | 'MONITOR_NETWORK'
  | 'MONITOR_FORECAST'
  | 'MONITOR_RISK'
  | 'INVESTIGATE_EPISODES'
  | 'INVESTIGATE_EVIDENCE'
  | 'INVESTIGATE_MITRE'
  | 'MEMORY_HISTORICAL'
  | 'SIMULATE_COUNTERFACTUALS'
  | 'DEFENSE_ACTIONS'
  | 'VERIFY_OUTCOMES'
  | 'SYSTEM_PIPELINE'
  | 'SYSTEM_MODELS';

export type ViewLevel = 'COMMAND_CENTER' | 'DATASET_WORKSPACE' | 'INVESTIGATION_WORKSPACE' | 'LIVE_LAB';

export const AEGIS_DATASETS = [
  'cic_ids2018_mar02',
  'cic_ids2018_mar01',
  'cic_ids2018_feb28',
  'cic_ids2018_feb23',
  'cic_ids2018_feb22',
  'cic_ids2018_feb21',
  'cic_ids2018_feb20',
  'cic_ids2018_feb16',
  'cic_ids2018_feb15',
  'cic_ids2018_feb14',
  'cic_ids2018',
  'cic_ids2017',
  'cic_iot_diad_2024',
  'cic_bccc_tabular_iot_2024',
  'cic_apt_iiot_2024',
] as const;

export type AegisDataset = typeof AEGIS_DATASETS[number];

export type PhaseStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface PhaseExecutionStep {
  phase_number: string;
  name: string;
  tagline: string;
  status: PhaseStatus;
  runtime_ms?: number;
  summary_metric?: string;
  artifact_path?: string;
  source_file: string;
}

export interface ScenarioRunState {
  dataset: AegisDataset;
  isRunning: boolean;
  activePhase: string;
  progressPercent: number;
  startedAt?: string;
  completedAt?: string;
  steps: PhaseExecutionStep[];
}

export interface KPISummary {
  current_flows_min: number;
  attack_activity_rate: number;
  escalation_probability: number;
  risk_score: number;
  risk_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_contributors: {
    forecast: number;
    activity: number;
    velocity: number;
    persistence: number;
  };
  active_episodes_count: number;
  active_episodes_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface NetworkTimelinePoint {
  timestamp: string;
  attack_rate: number;
  escalation_forecast: number;
  risk_score: number;
  total_flows: number;
  benign_flows: number;
  attack_flows: number;
  network_state: 'OBSERVED' | 'UNOBSERVED';
  gap_reason?: string;
  episode_id?: string;
}

export type LeadLagClassification = 
  | 'simultaneous'
  | 'indeterminate'
  | 'lagging'
  | 'f_only_no_physical_breach'
  | 'breach_only_no_forecast'
  | 'leading';

export interface InvestigationEpisode {
  episode_id: string;
  dataset: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  peak_risk: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  dominant_signal: string;
  forecast_behavior: string;
  audit_classification: LeadLagClassification;
  forecast_trigger_time?: string;
  physical_breach_time?: string;
  lead_lag_minutes?: number;
  candidate_mitre_techniques: {
    id: string;
    name: string;
    confidence: 'HEURISTIC_CONTEXTUAL';
  }[];
  constituent_incident_ids: string[];
  deterministic_narrative: string;
  investigation_state: 'NEW';
}

export interface CounterfactualIntervention {
  intervention_name: string;
  action_type?: 'RATE_LIMIT' | 'HOST_ISOLATION' | 'SIGNATURE_BLOCK' | 'FLOW_EXPULSION' | 'MONITORING';
  min_hypothetical_risk: number;
  expected_hypothetical_risk: number;
  max_hypothetical_risk: number;
  latency_ms?: number;
  blast_radius?: 'MINIMAL' | 'MODERATE' | 'HIGH';
  enforcement_command?: string;
}
