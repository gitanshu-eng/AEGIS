import React from 'react';
import { 
  CheckCircle2, 
  Loader2, 
  Clock, 
  Layers, 
  ArrowRight, 
  RefreshCw 
} from 'lucide-react';
import { useAegisStore } from '../../context/useAegisStore';
import type { PhaseExecutionStep } from '../../types/aegis';

export const ScenarioRunnerBanner: React.FC = () => {
  const { scenario, selectedDataset, runScenario, setNav, setSelectedSourceFile } = useAegisStore();

  return (
    <div className="mb-6 p-4 rounded-xl bg-[#091224]/80 border border-[#1e3458] shadow-xl backdrop-blur-md">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-[#00f0ff]">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                Full-Lifecycle Scenario Execution (Phase 1�7)
              </span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold flex items-center gap-1 ${
                scenario.isRunning 
                  ? 'bg-amber-950/80 border border-amber-500/40 text-amber-300 animate-pulse'
                  : 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-300'
              }`}>
                {scenario.isRunning ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin" />
                    EXECUTING PHASE {scenario.activePhase}...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3 h-3" />
                    SCENARIO PIPELINE READY
                  </>
                )}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
              Target Telemetry Dataset: <strong className="text-cyan-300 font-bold">{selectedDataset}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block font-mono text-xs">
            <span className="text-slate-500 block text-[10px]">Pipeline Progress</span>
            <span className="text-white font-bold">{scenario.progressPercent}% Complete</span>
          </div>

          <button
            onClick={() => runScenario(selectedDataset)}
            disabled={scenario.isRunning}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all ${
              scenario.isRunning
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-cyan-500/20 hover:bg-cyan-500/30 text-[#00f0ff] border border-cyan-500/50'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scenario.isRunning ? 'animate-spin' : ''}`} />
            Rerun Scenario
          </button>

          <button
            onClick={() => {
              setSelectedSourceFile('forecasting_model.py');
              setNav('SYSTEM_PIPELINE');
            }}
            className="px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700 flex items-center gap-1"
          >
            Details
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden my-3">
        <div 
          className="bg-gradient-to-r from-cyan-500 via-purple-500 to-emerald-400 h-full transition-all duration-300"
          style={{ width: `${scenario.progressPercent}%` }}
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 pt-1 font-mono text-[11px]">
        {scenario.steps.map((step: PhaseExecutionStep) => {
          const isCurrent = step.status === 'RUNNING';
          const isDone = step.status === 'COMPLETED';

          return (
            <div
              key={step.phase_number}
              onClick={() => {
                setSelectedSourceFile(step.source_file);
                setNav('SYSTEM_PIPELINE');
              }}
              className={`p-2 rounded-lg border transition-all cursor-pointer hover:border-slate-600 ${
                isCurrent
                  ? 'bg-cyan-950/40 border-[#00f0ff] text-white shadow-lg shadow-cyan-500/10'
                  : isDone
                  ? 'bg-slate-950/60 border-slate-800 text-slate-300'
                  : 'bg-slate-950/30 border-slate-900 text-slate-600'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-[10px] text-slate-400">{step.phase_number}</span>
                {isCurrent ? (
                  <Loader2 className="w-3 h-3 text-[#00f0ff] animate-spin" />
                ) : isDone ? (
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Clock className="w-3 h-3 text-slate-600" />
                )}
              </div>
              <div className="font-semibold truncate text-[11px]">{step.name}</div>
              <div className="text-[10px] text-slate-500 truncate mt-0.5">
                {step.runtime_ms ? `${step.runtime_ms}ms` : step.status}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
