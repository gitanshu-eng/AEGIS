import type { KPISummary, NetworkTimelinePoint, InvestigationEpisode } from '../../types/aegis';

export const MOCK_KPI: KPISummary = {
  current_flows_min: 14280,
  attack_activity_rate: 0.18,
  escalation_probability: 0.72,
  risk_score: 78,
  risk_severity: 'HIGH',
  risk_contributors: {
    forecast: 0.35,
    activity: 0.25,
    velocity: 0.20,
    persistence: 0.20,
  },
  active_episodes_count: 3,
  active_episodes_severity: 'HIGH',
};

export const MOCK_TIMELINE: NetworkTimelinePoint[] = [
  { timestamp: '02:25', attack_rate: 0.02, escalation_forecast: 0.15, risk_score: 18, total_flows: 12400, benign_flows: 12152, attack_flows: 248, network_state: 'OBSERVED' },
  { timestamp: '02:26', attack_rate: 0.03, escalation_forecast: 0.18, risk_score: 21, total_flows: 12890, benign_flows: 12503, attack_flows: 387, network_state: 'OBSERVED' },
  { timestamp: '02:27', attack_rate: 0.02, escalation_forecast: 0.22, risk_score: 25, total_flows: 13100, benign_flows: 12838, attack_flows: 262, network_state: 'OBSERVED' },
  { timestamp: '02:28', attack_rate: 0.04, escalation_forecast: 0.38, risk_score: 36, total_flows: 13450, benign_flows: 12912, attack_flows: 538, network_state: 'OBSERVED' },
  { timestamp: '02:29', attack_rate: 0.06, escalation_forecast: 0.54, risk_score: 52, total_flows: 14200, benign_flows: 13348, attack_flows: 852, network_state: 'OBSERVED' },
  { timestamp: '02:30', attack_rate: 0.08, escalation_forecast: 0.65, risk_score: 64, total_flows: 14900, benign_flows: 13708, attack_flows: 1192, network_state: 'OBSERVED' },
  { timestamp: '02:31', attack_rate: 0.28, escalation_forecast: 0.72, risk_score: 78, total_flows: 18400, benign_flows: 13248, attack_flows: 5152, network_state: 'OBSERVED', episode_id: 'EP-Friday-02-03-2018-0012' },
  { timestamp: '02:32', attack_rate: 0.34, escalation_forecast: 0.69, risk_score: 75, total_flows: 19100, benign_flows: 12606, attack_flows: 6494, network_state: 'OBSERVED', episode_id: 'EP-Friday-02-03-2018-0012' },
  { timestamp: '02:33', attack_rate: 0.22, escalation_forecast: 0.58, risk_score: 66, total_flows: 17200, benign_flows: 13416, attack_flows: 3784, network_state: 'OBSERVED' },
  { timestamp: '02:34', attack_rate: 0.00, escalation_forecast: 0.00, risk_score: 0, total_flows: 0, benign_flows: 0, attack_flows: 0, network_state: 'UNOBSERVED', gap_reason: 'No valid observed network packets in window 02:34' },
  { timestamp: '02:35', attack_rate: 0.12, escalation_forecast: 0.45, risk_score: 48, total_flows: 14500, benign_flows: 12760, attack_flows: 1740, network_state: 'OBSERVED' },
  { timestamp: '02:36', attack_rate: 0.05, escalation_forecast: 0.32, risk_score: 35, total_flows: 13800, benign_flows: 13110, attack_flows: 690, network_state: 'OBSERVED' },
];

export const MOCK_EPISODES: InvestigationEpisode[] = [
  {
    episode_id: 'EP-Friday-02-03-2018-0012',
    dataset: 'Friday-02-03-2018',
    start_time: '02:31:00 UTC',
    end_time: '02:39:00 UTC',
    duration_minutes: 8,
    peak_risk: 78,
    severity: 'HIGH',
    dominant_signal: 'Forecast & Packet Velocity',
    forecast_behavior: 'Elevated escalation likelihood preceding high volume ingress',
    audit_classification: 'simultaneous',
    forecast_trigger_time: '02:31:00 UTC',
    physical_breach_time: '02:31:00 UTC',
    lead_lag_minutes: 0,
    candidate_mitre_techniques: [
      { id: 'T1498', name: 'Network Denial of Service', confidence: 'HEURISTIC_CONTEXTUAL' },
      { id: 'T1499', name: 'Endpoint Denial of Service', confidence: 'HEURISTIC_CONTEXTUAL' }
    ],
    constituent_incident_ids: ['INC-0203-0091', 'INC-0203-0092'],
    deterministic_narrative: 'Simultaneous breach indicators matched the temporal escalation trigger in the same window. Flow volume surged by 38% with a disproportionate drop in forward inter-arrival time.',
    investigation_state: 'NEW'
  },
  {
    episode_id: 'EP-Friday-02-03-2018-0019',
    dataset: 'Friday-02-03-2018',
    start_time: '05:12:00 UTC',
    end_time: '05:24:00 UTC',
    duration_minutes: 12,
    peak_risk: 62,
    severity: 'MEDIUM',
    dominant_signal: 'Persistence Anomaly',
    forecast_behavior: 'Sustained elevated escalation likelihood across multiple windows',
    audit_classification: 'lagging',
    forecast_trigger_time: '05:14:00 UTC',
    physical_breach_time: '05:12:00 UTC',
    lead_lag_minutes: -2,
    candidate_mitre_techniques: [
      { id: 'T1046', name: 'Network Service Discovery', confidence: 'HEURISTIC_CONTEXTUAL' }
    ],
    constituent_incident_ids: ['INC-0203-0145'],
    deterministic_narrative: 'Temporal escalation forecast lagged the physical flow onset by 2 minutes. Persistent low-volume port sweeps observed across internal subnet range.',
    investigation_state: 'NEW'
  }
];
