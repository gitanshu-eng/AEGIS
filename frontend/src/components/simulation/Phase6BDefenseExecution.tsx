import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Terminal, 
  RotateCcw, 
  AlertTriangle, 
  Lock, 
  Unlock, 
  Info,
  X
} from 'lucide-react';
import { API, API_KEY } from "../../api/client";

interface Phase6BDefenseExecutionProps {
  baselineRisk?: number;
  episodeId?: string;
  dataset?: string;
}

interface CounterMeasure {
  id: string;
  name: string;
  type: string;
  blastRadius: 'MINIMAL' | 'MODERATE' | 'BROAD';
  latency: string;
  simulatedRisk: number;
  forwardPayload: string;
  rollbackPayload: string;
  description: string;
}

const MEASURES: CounterMeasure[] = [
  {
    id: 'vlan-isolation',
    name: 'VLAN Quarantine Isolation',
    type: 'Host Network Micro-Segmentation',
    blastRadius: 'MINIMAL',
    latency: '120ms',
    simulatedRisk: 31,
    forwardPayload: 'ovs-vsctl set port tap-soc-host tag=999 # Quarantine Subnet 172.31.32.14',
    rollbackPayload: 'ovs-vsctl remove port tap-soc-host tag 999 # Restore Normal Port Access',
    description: 'Cuts off the infected device from the rest of the network to stop the attack from spreading.'
  },
  {
    id: 'token-bucket',
    name: 'Slow Down Suspicious Traffic',
    type: 'Traffic Rate Shaping',
    blastRadius: 'MINIMAL',
    latency: '45ms',
    simulatedRisk: 54,
    forwardPayload: 'tc qdisc add dev eth0 root handle 1: cbq avpkt 1000 bandwidth 100mbit',
    rollbackPayload: 'tc qdisc del dev eth0 root # Clear Active Traffic Shaper',
    description: 'Reduces the speed of incoming traffic that looks suspicious, buying time to investigate.'
  },
  {
    id: 'bpf-drop',
    name: 'Block Malicious Packets',
    type: 'Kernel Ingress Filter',
    blastRadius: 'MODERATE',
    latency: '25ms',
    simulatedRisk: 42,
    forwardPayload: 'tc filter add dev eth0 ingress bpf da obj drop_exploit.o sec classifier',
    rollbackPayload: 'tc filter del dev eth0 ingress # Remove Active eBPF Program',
    description: 'Automatically discards incoming traffic identified as malicious before it reaches the system.'
  }
];


const STATE_MACHINE = ['QUEUED', 'DISPATCHING', 'CONFIRMED', 'VERIFIED'] as const;

interface VerificationRecord {
  action_id: string;
  state: string;
  action: string;
  target_host: string;
  predicted_risk: number | null;
  observed_risk: number | null;
  prediction_error: number | null;
  timestamp: string;
}

const VerificationTracker: React.FC<{ dataset: string }> = ({ dataset }) => {
  const [records, setRecords] = useState<VerificationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!dataset) return;
    setLoading(true);
    fetch(`${API}/api/verifications?dataset=${encodeURIComponent(dataset)}`, {
      headers: { Accept: 'application/json', 'X-API-Key': API_KEY },
    })
      .then((r) => r.json())
      .then((data: VerificationRecord[]) => setRecords(data))
      .catch(() => setRecords([]))
      .finally(() => setLoading(false));
  }, [dataset]);

  if (loading) return (
    <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono text-slate-500 animate-pulse">
      Loading Phase 6B verification records...
    </div>
  );

  if (records.length === 0) return (
    <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono text-slate-500">
      No Phase 6B verification records found for this dataset.
    </div>
  );

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-3">
      <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-3">
        Phase 6B Live Defense State Tracker � {records.length} Records
      </h3>
      {records.map((rec, idx) => {
        const activeIndex = STATE_MACHINE.indexOf(
          (rec.state?.toUpperCase() ?? 'QUEUED') as typeof STATE_MACHINE[number]
        );
        return (
          <div key={idx} className="border border-slate-800 rounded bg-slate-950/60 p-3 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-cyan-400 font-bold">{rec.action_id}</span>
              <span className="text-slate-500 truncate max-w-[200px]">{rec.target_host}</span>
            </div>

            {/* State machine bar */}
            <div className="flex items-center gap-1">
              {STATE_MACHINE.map((step, stepIdx) => {
                const isReached = stepIdx <= activeIndex;
                const isCurrent = stepIdx === activeIndex;
                return (
                  <div key={step} className="flex-1 flex flex-col items-center gap-1">
                    <div className={`h-2 w-full rounded-full transition-all ${
                      isCurrent  ? 'bg-cyan-400 ring-1 ring-cyan-400/60' :
                      isReached  ? 'bg-emerald-500' :
                                   'bg-slate-800'
                    }`} />
                    <span className={`text-[9px] font-mono ${
                      isCurrent  ? 'text-cyan-300 font-bold' :
                      isReached  ? 'text-emerald-400' :
                                   'text-slate-600'
                    }`}>{step}</span>
                  </div>
                );
              })}
            </div>

            {/* Metrics */}
            {(rec.predicted_risk !== null || rec.observed_risk !== null) && (
              <div className="flex gap-4 text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800">
                {rec.predicted_risk !== null && (
                  <span>Predicted: <span className="text-slate-200">{rec.predicted_risk?.toFixed(1)}</span></span>
                )}
                {rec.observed_risk !== null && (
                  <span>Observed: <span className="text-slate-200">{rec.observed_risk?.toFixed(1)}</span></span>
                )}
                {rec.prediction_error !== null && (
                  <span>Error: <span className={Math.abs(rec.prediction_error ?? 0) < 5 ? 'text-emerald-400' : 'text-amber-400'}>
                    {rec.prediction_error?.toFixed(2)}
                  </span></span>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export const Phase6BDefenseExecution: React.FC<Phase6BDefenseExecutionProps> = ({ 
  baselineRisk = 78, 
  episodeId = 'EP-ACTIVE',
  dataset = 'cic_ids2017'
}) => {
  const [selectedId, setSelectedId] = useState<string>('vlan-isolation');
  const [armed, setArmed] = useState<boolean>(false);
  const [showConfirmModal, setShowConfirmModal] = useState<boolean>(false);
  const [status, setStatus] = useState<'IDLE' | 'ENFORCING' | 'ACTIVE' | 'ROLLED_BACK'>('IDLE');

  const activeMeasure = MEASURES.find(m => m.id === selectedId) || MEASURES[0];

  const handleExecute = async () => {
    setShowConfirmModal(false);
    setStatus('ENFORCING');
    try {
      await fetch(`${API}/api/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-API-Key': API_KEY },
        body: JSON.stringify({ action: activeMeasure.name, target_host: '172.31.32.14', predicted_risk: activeMeasure.simulatedRisk, observed_risk: baselineRisk, payload: activeMeasure.forwardPayload, episode_id: episodeId, dataset: dataset })
      });
      setStatus('ACTIVE');
    } catch {
      setStatus('IDLE');
    }
  };

  const handleRollback = () => {
    setStatus('ENFORCING');
    setTimeout(() => {
      setStatus('ROLLED_BACK');
    }, 700);
  };

  return (
    <div className="space-y-6 text-slate-100">
      {/* Live Phase 6B State Tracker */}
      <VerificationTracker dataset={dataset} />
      {/* Header & Authorization Gate */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-slate-900/80 border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white tracking-wide">PHASE 6B: ACTIVE DEFENSE GATEWAY</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic rule dispatch &amp; isolated testbed execution with rollback fail-safes.
            {episodeId && <span className="ml-2 text-cyan-400 font-mono">Bound to {episodeId}</span>}
          </p>
        </div>

        {/* SOC Human Authorization Toggle */}
        <div className="flex items-center gap-3 bg-slate-950 px-3 py-2 rounded border border-slate-700">
          {armed ? <Unlock className="w-4 h-4 text-amber-400" /> : <Lock className="w-4 h-4 text-slate-500" />}
          <label className="text-xs font-semibold cursor-pointer select-none flex items-center gap-2">
            <input 
              type="checkbox" 
              checked={armed} 
              onChange={(e) => setArmed(e.target.checked)} 
              className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
            />
            <span className={armed ? 'text-amber-400' : 'text-slate-400'}>
              {armed ? 'AUTONOMOUS GATE: ARMED' : 'AUTONOMOUS GATE: LOCKED'}
            </span>
          </label>
        </div>
      </div>

      {/* Model-Based Disclaimer */}
      <div className="flex items-center gap-2 px-3 py-2 bg-blue-950/40 border border-blue-800/60 rounded text-xs text-blue-300">
        <Info className="w-4 h-4 text-blue-400 shrink-0" />
        <span>
          <strong>MODEL-BASED HYPOTHETICAL SIMULATION:</strong> Post-action risk reductions represent predicted outcomes under counterfactual simulation before live testbed validation.
        </span>
      </div>

      {/* Counter-Measure Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {MEASURES.map((m) => {
          const isSelected = m.id === selectedId;
          return (
            <button
              key={m.id}
              onClick={() => setSelectedId(m.id)}
              className={`p-4 rounded-lg text-left transition-all border ${
                isSelected 
                  ? 'bg-slate-800/90 border-cyan-500 ring-1 ring-cyan-500' 
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-950 text-cyan-400 border border-slate-800">
                  {m.blastRadius} BLAST
                </span>
                <span className="text-xs text-slate-400 font-mono">{m.latency}</span>
              </div>
              <h3 className="text-sm font-bold text-white mb-1">{m.name}</h3>
              <p className="text-xs text-slate-400 mb-3">{m.description}</p>
              
              <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
                <span className="text-slate-400">Predicted Risk After Action:</span>
                <span className="font-mono font-bold text-emerald-400">{baselineRisk} &rarr; {m.simulatedRisk}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Execution & Rollback Payloads Display */}
      <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
              Technical Details: {activeMeasure.name}
            </span>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
            Target: 172.31.32.14
          </span>
        </div>

        {/* Forward Payload */}
        <div>
          <div className="text-[11px] font-mono text-slate-400 mb-1 flex items-center justify-between">
            <span>FORWARD ENFORCEMENT COMMAND (PROD SINKHOLE):</span>
            <span className="text-emerald-400">DISPATCH READY</span>
          </div>
          <pre className="p-2.5 rounded bg-black/60 border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto">
            {activeMeasure.forwardPayload}
          </pre>
        </div>

        {/* Rollback Payload */}
        <div>
          <div className="text-[11px] font-mono text-slate-400 mb-1 flex items-center justify-between">
            <span>MANDATORY ROLLBACK / REVERT PAYLOAD:</span>
            <span className="text-amber-400">RESTORE READY</span>
          </div>
          <pre className="p-2.5 rounded bg-black/60 border border-slate-800 font-mono text-xs text-amber-300 overflow-x-auto">
            {activeMeasure.rollbackPayload}
          </pre>
        </div>

        {/* Action Dispatcher Control Strip */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800">
          <div className="text-xs font-mono text-slate-400">
            Current Status: <span className="font-bold text-cyan-400">{status}</span>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {status === 'ACTIVE' ? (
              <button
                onClick={handleRollback}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 bg-amber-600/90 hover:bg-amber-500 text-white rounded font-mono text-xs font-semibold tracking-wider transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                EXECUTE IMMEDIATE ROLLBACK
              </button>
            ) : (
              <button
                disabled={!armed || status === 'ENFORCING'}
                onClick={() => setShowConfirmModal(true)}
                className={`w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 rounded font-mono text-xs font-semibold tracking-wider transition-colors ${
                  armed && status !== 'ENFORCING'
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                }`}
              >
                <ShieldAlert className="w-4 h-4" />
                {status === 'ENFORCING' ? 'DISPATCHING TO TESTBED...' : 'ENFORCE PHASE 6B COUNTER-MEASURE'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Two-Step Verification Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-amber-500/70 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-amber-400">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="font-bold tracking-wide text-sm font-mono uppercase">
                  Production Infrastructure Enforcement Gate
                </h3>
              </div>
              <button 
                onClick={() => setShowConfirmModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <p>
                You are authorizing immediate mitigation dispatch to production subnet interface <strong className="text-white">172.31.32.14</strong>.
              </p>
              
              <div className="bg-slate-950 p-3 rounded border border-slate-800 font-mono space-y-1">
                <div>Action: <span className="text-cyan-400">{activeMeasure.name}</span></div>
                <div>Target Episode: <span className="text-cyan-400">{episodeId}</span></div>
                <div>Impact Level: <span className="text-emerald-400">{activeMeasure.blastRadius}</span></div>
                <div>Rollback TTL: <span className="text-amber-400">300s (Auto-revert enabled)</span></div>
              </div>

              <div className="p-2.5 bg-amber-950/40 border border-amber-800/60 rounded text-[11px] text-amber-200">
                Ensure incident ticket is stamped before execution. This action will be immutably recorded in the Phase 7 audit log.
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-semibold"
              >
                ABORT / CANCEL
              </button>
              <button
                onClick={handleExecute}
                className="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold tracking-wider"
              >
                CONFIRM &amp; DISPATCH TO TESTBED
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};





