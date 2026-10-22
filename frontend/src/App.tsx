import { useEffect, useState } from "react";
import { Header } from "./components/common/Header";
import { Sidebar } from "./components/common/Sidebar";
import { KPICards } from "./components/command-center/KPICards";
import { NetworkTimeline } from "./components/charts/NetworkTimeline";
import { EpisodeDossier } from "./components/investigation/EpisodeDossier";
import { DatasetWorkspace } from "./components/dataset-workspace/DatasetWorkspace";
import { LiveLabWorkspace } from "./components/live-lab/LiveLabWorkspace";
import { ScenarioRunnerBanner } from "./components/pipeline/ScenarioRunner";
import { PipelineExplorer } from "./components/pipeline/PipelineExplorer";
import { ModelStatus } from "./components/pipeline/ModelStatus";
import { CounterfactualMatrix } from "./components/simulation/CounterfactualMatrix";
import { Phase6BDefenseExecution } from "./components/simulation/Phase6BDefenseExecution";
import { useAegisStore } from "./context/useAegisStore";
import { fetchKPISummary, fetchTimeline, fetchEpisodes } from "./api/client";
import { MemoryViewer } from "./components/memory/MemoryViewer";
import MonitorNetwork from "./components/MonitorNetwork";
import MonitorForecast from "./components/MonitorForecast";
import MonitorRisk from "./components/MonitorRisk";
import MitreContextView from "./components/investigation/MitreContextView";
import { LiveFeedView } from "./components/live-feed/LiveFeedView";
import { useLiveTick } from "./hooks/useLiveTick";
import type { KPISummary, NetworkTimelinePoint, InvestigationEpisode } from "./types/aegis";

const MAX_TIMELINE_POINTS = 500;

// Render cold-start guard — polls /api/health until backend is awake
async function waitForBackend(apiBase: string, maxWaitMs = 30000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    try {
      const res = await fetch(`${apiBase}/api/health`, { signal: AbortSignal.timeout(4000) });
      if (res.ok) return;
    } catch (_) {}
    await new Promise(r => setTimeout(r, 2000));
  }
}

export default function App() {
  const { currentNav, selectedDataset, selectedEpisodeId } = useAegisStore();
  const [kpi, setKpi] = useState<KPISummary | null>(null);
  const [timeline, setTimeline] = useState<NetworkTimelinePoint[]>([]);
  const [episodes, setEpisodes] = useState<InvestigationEpisode[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [livePoint, setLivePoint] = useState<NetworkTimelinePoint | null>(null);
  const [backendReady, setBackendReady] = useState(false);

  // Wake backend on mount
  useEffect(() => {
    const base = (import.meta as any).env?.VITE_API_URL ?? 'https://aegis-api-hqnx.onrender.com';
    waitForBackend(base).then(() => setBackendReady(true));
  }, []);

  // Initial full load when dataset changes
  useEffect(() => {
    if (!backendReady) return;
    setLoading(true);
    Promise.all([
      fetchKPISummary(selectedDataset),
      fetchTimeline(selectedDataset),
      fetchEpisodes(selectedDataset),
    ])
      .then(([kpiData, timelineData, episodesData]) => {
        setKpi(kpiData);
        setTimeline(timelineData);
        setEpisodes(episodesData);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedDataset, backendReady]);

  // Live tick — appends new point to timeline every 5 seconds + refreshes KPIs
  useLiveTick(selectedDataset, (point, mode) => {
    setLivePoint(point);
    (point as any).telemetry_mode = mode;
    setTimeline((prev) => {
      const updated = [...prev, point];
      return updated.length > MAX_TIMELINE_POINTS
        ? updated.slice(updated.length - MAX_TIMELINE_POINTS)
        : updated;
    });
    // Update KPI from live tick data
    if (point.network_state === "OBSERVED") {
      setKpi((prev) => {
        if (!prev) return prev;
        const attackRate = point.attack_rate ?? 0;
        const riskScore = point.risk_score ?? prev.risk_score;
        const severity =
          riskScore >= 80 ? "CRITICAL" :
          riskScore >= 60 ? "HIGH" :
          riskScore >= 40 ? "MEDIUM" : "LOW";
        return {
          ...prev,
          current_flows_min: point.total_flows ?? prev.current_flows_min,
          attack_activity_rate: attackRate,
          escalation_probability: point.escalation_forecast ?? prev.escalation_probability,
          risk_score: riskScore,
          risk_severity: severity as typeof prev.risk_severity,
          risk_contributors: {
            ...prev.risk_contributors,
            activity: Math.min(1, attackRate),
            velocity: Math.min(1, attackRate * 1.2),
          },
        };
      });
    }
  });

  const activeEpisode =
    episodes.find((e) => e.episode_id === selectedEpisodeId) || episodes[0];

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto px-6 pt-5 pb-16">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800/60">
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                <span>{currentNav.replace(/_/g, " ")}</span>
                <span className="text-xs font-mono text-slate-500">
                  [{selectedDataset}]
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Phase 1-7 Synchronized Cyber-Defense Pipeline • Deterministic
                Scoring • Autonomous Response
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* Live tick indicator */}
              {livePoint && (
                <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse inline-block" />
                  {(livePoint as any).telemetry_mode === "PCAP_REPLAY" ? "PCAP" : "LIVE"} {livePoint.timestamp?.slice(11, 16)}
                </div>
              )}
              <div className="text-xs font-mono text-slate-500">
                Active Target:{" "}
                <span className="text-[#00f0ff]">{selectedDataset}</span>
              </div>
            </div>
          </div>

          <ScenarioRunnerBanner />

          {(loading || !kpi) && currentNav !== "SYSTEM_PIPELINE" && currentNav !== "SYSTEM_MODELS" ? (
            <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">
              {!backendReady ? "Waking AEGIS backend — Render cold start, may take 15–30s..." : "Querying AEGIS Telemetry Engine..."}
            </div>
          ) : (
            <>
              {currentNav === "COMMAND_CENTER" && (
                <>
                  <KPICards kpi={kpi} />
                  <NetworkTimeline data={timeline} />
                  {activeEpisode && (
                    <div className="mt-8 pt-6 border-t border-slate-800/80">
                      <div className="text-sm font-bold font-mono text-white mb-4 flex items-center gap-2">
                        <span>Active Episode Investigation & Autonomous Response</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-normal">
                          {activeEpisode.episode_id}
                        </span>
                      </div>
                      <EpisodeDossier episode={activeEpisode} />
                    </div>
                  )}
                </>
              )}

              {currentNav === "MONITOR_NETWORK" && (
                <MonitorNetwork dataset={selectedDataset} />
              )}

              {currentNav === "MONITOR_FORECAST" && (
                <MonitorForecast dataset={selectedDataset} />
              )}

              {currentNav === "MONITOR_RISK" && (
                <MonitorRisk dataset={selectedDataset} />
              )}

              {currentNav === "INVESTIGATE_EPISODES" && activeEpisode && (
                <EpisodeDossier episode={activeEpisode} />
              )}

              {currentNav === "INVESTIGATE_EVIDENCE" && (
                <DatasetWorkspace episodes={episodes} timeline={timeline} />
              )}

              {currentNav === "INVESTIGATE_MITRE" && (
                <MitreContextView dataset={selectedDataset} />
              )}

              {currentNav === "MEMORY_HISTORICAL" && (
                <MemoryViewer dataset={selectedDataset} />
              )}

              {currentNav === "SIMULATE_COUNTERFACTUALS" && activeEpisode && (
                <CounterfactualMatrix
                  episodeId={activeEpisode.episode_id}
                  baselineRisk={activeEpisode.peak_risk}
                  dataset={selectedDataset}
                />
              )}

              {currentNav === "DEFENSE_ACTIONS" && activeEpisode && (
                <Phase6BDefenseExecution
                  baselineRisk={activeEpisode.peak_risk}
                  episodeId={activeEpisode.episode_id}
                  dataset={selectedDataset}
                />
              )}

              {currentNav === "VERIFY_OUTCOMES" && <LiveLabWorkspace />}

              {currentNav === "LIVE_FEED" && (
                <LiveFeedView dataset={selectedDataset} />
              )}

            </>
          )}
          {currentNav === "SYSTEM_PIPELINE" && <PipelineExplorer />}
          {currentNav === "SYSTEM_MODELS" && <ModelStatus />}
        </main>
      </div>
    </div>
  );
}
