import React from 'react';
import { Shield, Cpu } from 'lucide-react';
import { useAegisStore } from '../../context/useAegisStore';
import { AEGIS_DATASETS } from '../../types/aegis';
import type { AegisDataset } from '../../types/aegis';

export const Header: React.FC = () => {
  const { selectedDataset, selectDataset, dataMode, setDataMode } = useAegisStore();

  return (
    <header className="border-b border-[#132038] bg-[#070a13]/95 backdrop-blur-md sticky top-0 z-50 px-6 py-2.5">
      <div className="flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-500/40 text-[#00f0ff]">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-widest text-sm">AEGIS</span>
              <span className="text-[9px] px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-500/50 text-emerald-400 font-mono flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                OPERATIONAL
              </span>
            </div>
            <p className="text-[10px] text-slate-400">Autonomous Cyber-Defense Platform</p>
          </div>
        </div>

        {/* Global Dataset Selector & Mode Switcher */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-lg px-2.5 py-1">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <select
              aria-label="Target Telemetry Dataset"
              value={selectedDataset}
              onChange={(e) => selectDataset(e.target.value as AegisDataset)}
              className="bg-transparent text-xs font-mono text-slate-200 focus:outline-none cursor-pointer"
            >
              {AEGIS_DATASETS.map((ds) => (
                <option key={ds} value={ds} className="bg-slate-900 text-slate-200">
                  {ds}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setDataMode(dataMode === 'DEMO' ? 'API' : 'DEMO')}
            className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded border transition-colors ${
              dataMode === 'DEMO'
                ? 'bg-amber-950/50 border-amber-500/40 text-amber-300'
                : 'bg-cyan-950/50 border-cyan-500/40 text-cyan-300'
            }`}
          >
            MODE: {dataMode}
          </button>
        </div>

      </div>
    </header>
  );
};
