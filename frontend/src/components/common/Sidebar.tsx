import React from 'react';
import {
  Home,
  Network,
  TrendingUp,
  Shield,
  FileText,
  Database,
  ShieldAlert,
  Clock,
  Sliders,
  ShieldCheck,
  CheckCircle2,
  Layers,
  Settings,
} from 'lucide-react';
import { useAegisStore } from '../../context/useAegisStore';
import type { NavItem } from '../../types/aegis';

interface MenuItem {
  id: NavItem;
  label: string;
  icon: React.ElementType;
}

interface MenuGroup {
  title?: string;
  items: MenuItem[];
}

const MENU_GROUPS: MenuGroup[] = [
  {
    title: 'MONITOR',
    items: [
      { id: 'MONITOR_NETWORK', label: 'Network State', icon: Network },
      { id: 'MONITOR_FORECAST', label: 'Forecast', icon: TrendingUp },
      { id: 'MONITOR_RISK', label: 'Risk', icon: Shield },
    ],
  },
  {
    title: 'INVESTIGATE',
    items: [
      { id: 'INVESTIGATE_EPISODES', label: 'Episodes', icon: FileText },
      { id: 'INVESTIGATE_EVIDENCE', label: 'Evidence', icon: Database },
      { id: 'INVESTIGATE_MITRE', label: 'MITRE Context', icon: ShieldAlert },
    ],
  },
  {
    title: 'MEMORY',
    items: [
      { id: 'MEMORY_HISTORICAL', label: 'Historical Episodes', icon: Clock },
    ],
  },
  {
    title: 'SIMULATE',
    items: [
      { id: 'SIMULATE_COUNTERFACTUALS', label: 'Counterfactuals', icon: Sliders },
    ],
  },
  {
    title: 'DEFENSE',
    items: [
      { id: 'DEFENSE_ACTIONS', label: 'Actions', icon: ShieldCheck },
    ],
  },
  {
    title: 'VERIFY',
    items: [
      { id: 'VERIFY_OUTCOMES', label: 'Outcomes', icon: CheckCircle2 },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { id: 'SYSTEM_PIPELINE', label: 'Data Pipeline', icon: Layers },
      { id: 'SYSTEM_MODELS', label: 'Model Status', icon: Settings },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const { currentNav, setNav } = useAegisStore();

  return (
    <aside className="w-60 shrink-0 bg-[#060b17] border-r border-[#132038] min-h-[calc(100vh-53px)] flex flex-col justify-between select-none py-3 px-3">
      
      {/* Top Nav List */}
      <div className="space-y-4">
        {/* Command Center Main Button (Pill highlight matching image) */}
        <button
          onClick={() => setNav('COMMAND_CENTER')}
          className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            currentNav === 'COMMAND_CENTER'
              ? 'bg-[#0052cc] text-white shadow-lg shadow-blue-500/30 border border-blue-400/50'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
          }`}
        >
          <Home className="w-4 h-4 shrink-0 text-white" />
          <span>Command Center</span>
        </button>

        {/* Grouped Sections */}
        <div className="space-y-4 pt-1">
          {MENU_GROUPS.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="px-3 text-[10px] font-sans font-bold tracking-wider text-slate-500">
                {group.title}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentNav === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setNav(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-1.5 rounded-md text-xs transition-colors ${
                      isActive
                        ? 'text-[#00c8ff] font-semibold bg-cyan-950/40 border-l-2 border-[#00c8ff]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#00c8ff]' : 'text-slate-400'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Brand Logo & Tagline: "AEGIS - SEE FURTHER. STOP SOONER." */}
      <div className="pt-6 pb-2 px-2 border-t border-slate-900/80">
        <div className="flex items-center gap-2.5">
          {/* Stylized Delta Triangle Logo */}
          <div className="relative w-6 h-6 flex items-center justify-center shrink-0">
            <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-slate-400">
              <path
                d="M12 3L2 21H22L12 3Z"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-slate-500"
              />
              <path
                d="M12 9L6 20H18L12 9Z"
                fill="currentColor"
                className="text-cyan-400/80"
              />
            </svg>
          </div>
          <div>
            <div className="text-xs font-bold tracking-widest text-slate-300 font-mono">
              AEGIS
            </div>
            <div className="text-[8px] font-mono tracking-wider text-slate-500 font-semibold uppercase">
              SEE FURTHER. STOP SOONER.
            </div>
          </div>
        </div>
      </div>

    </aside>
  );
};
