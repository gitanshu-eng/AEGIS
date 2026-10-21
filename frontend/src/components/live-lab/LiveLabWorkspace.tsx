import React, { useState } from 'react';
import { Terminal, Shield, CheckCircle, Play, RefreshCw, XCircle } from 'lucide-react';

interface VerificationResult {
  execution_id: string;
  timestamp: string;
  observation_mode: 'REAL_OBSERVED' | 'SIMULATED_OBSERVED';
  pre_risk: number;
  post_risk: number;
  predicted_risk: number;
  model_error: number;
  status: 'VERIFIED_EFFECTIVE' | 'INEFFECTIVE';
}

export const LiveLabWorkspace: React.FC = () => {
  const [authorized, setAuthorized] = useState<boolean>(false);
  const [activeTestRunning, setActiveTestRunning] = useState<boolean>(false);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [safeFailureTriggered, setSafeFailureTriggered] = useState<boolean>(false);

  const handleSimulateExecution = () => {
    setActiveTestRunning(true);
    setSafeFailureTriggered(false);
    setTimeout(() => {
      setActiveTestRunning(false);
      setVerification({
        execution_id: 'EXEC-7EB10600',
        timestamp: new Date().toISOString(),
        observation_mode: 'SIMULATED_OBSERVED',
        pre_risk: 78,
        post_risk: 29,
        predicted_risk: 31,
        model_error: -2,
        status: 'VERIFIED_EFFECTIVE',
      });
    }, 1200);
  };

  const handleTriggerSafeFailure = () => {
    setVerification(null);
    setSafeFailureTriggered(true);
  };

  return (
    <div className="space-y-6">
      <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-500/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-purple-900/60 border border-purple-500/40 text-purple-300">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-wide font-mono">LIVE LAB SECURITY TESTBED</h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 font-mono flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                ENVIRONMENT APPROVED
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Authorized Controlled Security Testing Subnet: <code className="text-cyan-300 font-mono">172.31.32.0/24 (VLAN-70)</code>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="text-slate-400">Lab State:</span>
          <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-purple-300 font-semibold">
            READY / ARMED
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyan-400" />
              Autonomous Defense Gate
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/70 border border-amber-500/40 text-amber-300 font-mono">
              AWAITING SOC APPROVAL
            </span>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Active Target Incident:</span>
                <span className="text-white font-bold">INC-LAB-0422</span>
              </div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Recommended Mitigation:</span>
                <span className="text-cyan-300 font-semibold">VLAN Host Isolation (Port Reassignment)</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Projected Risk Reduction:</span>
                <span className="text-emerald-400 font-bold">78 → 31 (Δ -47 pts)</span>
              </div>
            </div>

            <label className="flex items-center gap-3 p-3 bg-slate-950/40 rounded-lg border border-slate-800/80 cursor-pointer">
              <input
                type="checkbox"
                checked={authorized}
                onChange={(e) => setAuthorized(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
              />
              <span className="text-slate-300 text-[11px] leading-tight">
                Confirm explicit SOC authorization to execute automated mitigation in isolated testbed.
              </span>
            </label>

            <div className="flex items-center gap-3 pt-2">
              <button
                disabled={!authorized || activeTestRunning}
                onClick={handleSimulateExecution}
                className={`flex-1 py-2.5 px-4 rounded-lg font-mono text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  authorized && !activeTestRunning
                    ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-500/20'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                }`}
              >
                {activeTestRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Enforcing Rules...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Authorize & Execute Response
                  </>
                )}
              </button>

              <button
                onClick={handleTriggerSafeFailure}
                className="py-2.5 px-3 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 text-xs font-mono"
              >
                Test Fallback
              </button>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              Verification Engine
            </h3>
            {verification && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 font-mono font-bold">
                {verification.observation_mode}
              </span>
            )}
          </div>

          {safeFailureTriggered ? (
            <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-500/50 text-xs font-mono space-y-3">
              <div className="flex items-center gap-2 text-rose-300 font-bold">
                <XCircle className="w-4 h-4 text-rose-400" />
                DEFENSE STATUS: UNABLE TO SAFELY MITIGATE AUTOMATICALLY
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Reason: Required containment protocol exceeds currently authorized blast-radius boundaries for this testbed asset.
              </p>
              <div className="p-2.5 bg-black/40 rounded border border-rose-900/60 space-y-1 text-[11px]">
                <div className="text-slate-400 font-bold">Escalation Directives:</div>
                <div className="text-slate-300">1. Tier-3 SOC manual review assigned.</div>
                <div className="text-slate-300">2. Isolate test asset via manual chassis disconnect.</div>
                <div className="text-slate-300">3. Raw telemetry preserved in S3 incident ledger.</div>
              </div>
            </div>
          ) : verification ? (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div className="text-slate-400 mb-1">Execution Ledger: <span className="text-white font-bold">{verification.execution_id}</span></div>
                <div className="text-slate-400 text-[11px]">Timestamp: {verification.timestamp}</div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2.5 bg-slate-950/50 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Pre-Risk</span>
                  <span className="text-sm font-bold text-rose-400">{verification.pre_risk}</span>
                </div>
                <div className="p-2.5 bg-slate-950/50 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Post-Risk</span>
                  <span className="text-sm font-bold text-emerald-400">{verification.post_risk}</span>
                </div>
                <div className="p-2.5 bg-slate-950/50 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Model Error</span>
                  <span className="text-sm font-bold text-cyan-300">{verification.model_error} pts</span>
                </div>
              </div>

              <div className="p-3 rounded bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 flex items-center justify-between">
                <span>Verification State:</span>
                <span className="font-bold flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4" />
                  VERIFIED_EFFECTIVE
                </span>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs font-mono text-slate-500">
              Awaiting authorization trigger to collect live post-intervention telemetry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
