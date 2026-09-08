'use client';

import React from 'react';
import { useCustomAgentStore } from '@/store/useCustomAgentStore';
import { Sliders, X, Sparkles, Zap } from 'lucide-react';

export function ActiveAgentBadge() {
  const { agents, activeAgentId, setActiveAgent, openBuilder } = useCustomAgentStore();

  const activeAgent = agents.find((a) => a.id === activeAgentId);
  if (!activeAgent) return null;

  return (
    <div className="flex items-center justify-between w-full max-w-full mb-2 px-3.5 py-2 rounded-2xl bg-gradient-to-r from-blue-50/90 via-indigo-50/60 to-purple-50/40 dark:from-[#0b1329]/90 dark:via-[#111827]/90 dark:to-[#17152b]/90 border border-blue-200/80 dark:border-blue-500/30 shadow-[0_2px_12px_rgba(59,130,246,0.08)] dark:shadow-[0_4px_20px_rgba(30,58,138,0.25)] backdrop-blur-md animate-in fade-in slide-in-from-bottom-2 duration-200">
      {/* Left: Avatar + Agent Name + Persona Tag */}
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="h-6 w-6 rounded-xl bg-blue-500/15 dark:bg-blue-400/20 border border-blue-500/30 dark:border-blue-400/30 flex items-center justify-center shrink-0 shadow-2xs text-xs">
          {activeAgent.avatar ? (
            <span className="text-xs leading-none">{activeAgent.avatar}</span>
          ) : (
            <Zap className="h-3.5 w-3.5 text-amber-500 fill-amber-500/30" />
          )}
        </div>

        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-bold tracking-tight text-slate-900 dark:text-slate-100 truncate">
            {activeAgent.name}
          </span>
          <span className="hidden xs:inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-mono font-semibold bg-blue-500/10 text-blue-700 dark:text-[#a8c7fa] border border-blue-500/20 truncate max-w-[220px]">
            {activeAgent.role}
          </span>
        </div>
      </div>

      {/* Right: Actions (Configure & Switch back) */}
      <div className="flex items-center gap-1 shrink-0 ml-2">
        <button
          type="button"
          onClick={() => openBuilder(activeAgent)}
          className="p-1.5 rounded-xl text-slate-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-[#a8c7fa] hover:bg-white/80 dark:hover:bg-white/[0.08] active:scale-95 transition-all cursor-pointer"
          title="Configure Agent Workflow & Instructions"
        >
          <Sliders className="w-3.5 h-3.5" />
        </button>

        <button
          type="button"
          onClick={() => setActiveAgent(null)}
          className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400 hover:bg-white/80 dark:hover:bg-white/[0.08] active:scale-95 transition-all cursor-pointer"
          title="Dismiss Custom Agent (Return to Default AI)"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
