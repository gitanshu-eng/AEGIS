import type { KPISummary, NetworkTimelinePoint, InvestigationEpisode } from '../types/aegis';

export const API = (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { headers: { Accept: 'application/json' } });
  if (!res.ok) {
    const body = await res.text().catch(() => res.statusText);
    throw new Error(`[${res.status}] ${path}: ${body}`);
  }
  return res.json();
}

export async function fetchKPISummary(dataset: string): Promise<KPISummary> {
  const [networkRows, forecastRows, incidents, episodes] = await Promise.all([
    get<any[]>(`/api/network-state?dataset=${encodeURIComponent(dataset)}&limit=300`),
    get<any[]>(`/api/forecasts?dataset=${encodeURIComponent(dataset)}&limit=300`),
    get<any[]>(`/api/incidents?dataset=${encodeURIComponent(dataset)}`),
    get<any[]>(`/api/episodes?dataset=${encodeURIComponent(dataset)}`),
  ]);

  const observed = networkRows.filter((r) => r.observed !== false && r.unobserved !== true);
  const latest = observed[observed.length - 1] ?? networkRows[networkRows.length - 1] ?? {};
  const lastFc = forecastRows[forecastRows.length - 1] ?? {};
  const escalationProb: number = lastFc.escalation_probability ?? 0;

  const recent = observed.slice(-10);
  const avgAttackRate =
    recent.length > 0
      ? recent.reduce((s, r) => s + (r.attack_rate ?? 0), 0) / recent.length
      : 0;

  const scores = incidents.map((i) => i.risk_score ?? 0);
  const peakRisk = scores.length > 0 ? Math.max(...scores) : 0;
  const avgRisk = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
  const riskScore = Math.round(peakRisk * 0.6 + avgRisk * 0.4);
  const severity =
    riskScore >= 80 ? 'CRITICAL' : riskScore >= 60 ? 'HIGH' : riskScore >= 40 ? 'MEDIUM' : 'LOW';

  const avgForecast =
    incidents.length > 0
      ? incidents.reduce((s, i) => s + (i.escalation_probability ?? 0), 0) / incidents.length
      : escalationProb;

  return {
    current_flows_min:      latest.total_flows ?? 0,
    attack_activity_rate:   avgAttackRate,
    escalation_probability: escalationProb,
    risk_score:             riskScore,
    risk_severity:          severity as KPISummary['risk_severity'],
    risk_contributors: {
      forecast:    Math.min(1, avgForecast),
      activity:    Math.min(1, avgAttackRate),
      velocity:    Math.min(1, avgAttackRate * 1.2),
      persistence: Math.min(1, episodes.length / 10),
    },
    active_episodes_count:    episodes.length,
    active_episodes_severity: severity as KPISummary['active_episodes_severity'],
  };
}

export async function fetchTimeline(dataset: string): Promise<NetworkTimelinePoint[]> {
  const [networkRows, forecastRows] = await Promise.all([
    get<any[]>(`/api/network-state?dataset=${encodeURIComponent(dataset)}&limit=300`),
    get<any[]>(`/api/forecasts?dataset=${encodeURIComponent(dataset)}&limit=300`),
  ]);

  const fcMap = new Map<string, number>();
  for (const f of forecastRows) {
    if (f.timestamp) fcMap.set(f.timestamp, f.escalation_probability ?? 0);
  }

  return networkRows.map((row) => {
    const isUnobserved = row.unobserved === true || row.observed === false;
    const fcProb = fcMap.get(row.timestamp) ?? 0;
    const attackRate: number = row.attack_rate ?? 0;
    const riskScore = Math.round((0.5 * attackRate + 0.5 * fcProb) * 100);

    return {
      timestamp:           row.timestamp,
      attack_rate:         attackRate,
      escalation_forecast: fcProb,
      risk_score:          isUnobserved ? 0 : riskScore,
      total_flows:         row.total_flows ?? 0,
      benign_flows:        row.benign_flows ?? 0,
      attack_flows:        row.attack_flows ?? 0,
      network_state:       isUnobserved ? 'UNOBSERVED' : 'OBSERVED',
      gap_reason:          isUnobserved ? 'No valid observed network packets in window' : undefined,
    } as NetworkTimelinePoint;
  });
}

export async function fetchEpisodes(dataset: string): Promise<InvestigationEpisode[]> {
  const rows = await get<any[]>(`/api/episodes?dataset=${encodeURIComponent(dataset)}`);

  return rows.map((ep) => {
    const peakRisk: number = ep.peak_risk_score ?? ep.peak_risk ?? 0;
    const severity =
      peakRisk >= 80 ? 'CRITICAL' : peakRisk >= 60 ? 'HIGH' : peakRisk >= 40 ? 'MEDIUM' : 'LOW';
    const tactics: string[] = ep.sustained_tactics ?? [];
    const techniques: string[] = ep.sustained_techniques ?? [];

    return {
      episode_id:            ep.episode_id,
      dataset:               ep.dataset ?? dataset,
      start_time:            ep.start_time ?? '',
      end_time:              ep.end_time ?? '',
      duration_minutes:      ep.duration_minutes ?? 0,
      peak_risk:             peakRisk,
      severity:              severity as InvestigationEpisode['severity'],
      dominant_signal:       ep.dominant_signal ?? '',
      forecast_behavior:     ep.lead_lag_classification ?? '',
      audit_classification:  (ep.lead_lag_classification ?? 'indeterminate').toLowerCase() as InvestigationEpisode['audit_classification'],
      forecast_trigger_time: ep.start_time,
      physical_breach_time:  ep.start_time,
      lead_lag_minutes:      ep.lead_time_minutes ?? 0,
      candidate_mitre_techniques: techniques.map((t) => ({
        id:         t.split(':')[0]?.trim() ?? t,
        name:       t.split(':')[1]?.trim() ?? t,
        confidence: 'HEURISTIC_CONTEXTUAL' as const,
      })),
      constituent_incident_ids: [],
      deterministic_narrative:
        `${ep.dominant_signal ?? 'Signal'} detected. ` +
        `Lead/Lag: ${ep.lead_lag_classification ?? 'indeterminate'}. ` +
        `Tactics: ${tactics.slice(0, 2).join(', ') || 'N/A'}.`,
      investigation_state: (ep.investigation_state ?? 'NEW') as InvestigationEpisode['investigation_state'],
    } as InvestigationEpisode;
  });
}
