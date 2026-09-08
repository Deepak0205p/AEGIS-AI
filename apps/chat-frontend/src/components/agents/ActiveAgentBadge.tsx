'use client';

import React from 'react';
import { useCustomAgentStore } from '@/store/useCustomAgentStore';
import { Bot, Sparkles, X, ChevronRight, Sliders } from 'lucide-react';

export function ActiveAgentBadge() {
  const { agents, activeAgentId, setActiveAgent, openBuilder } = useCustomAgentStore();

  const activeAgent = agents.find((a) => a.id === activeAgentId);
  if (!activeAgent) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-2xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/50 shadow-xs mb-1.5 self-start animate-in fade-in slide-in-from-bottom-2 duration-150">
      <span className="text-sm">{activeAgent.avatar || '🤖'}</span>
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] font-bold text-blue-900 dark:text-blue-200">
          {activeAgent.name}
        </span>
        <span className="text-[9px] font-mono font-medium px-1.5 py-0.2 rounded bg-blue-200/60 dark:bg-blue-800/60 text-blue-800 dark:text-blue-200">
          {activeAgent.role}
        </span>
      </div>

      <button
        onClick={() => openBuilder(activeAgent)}
        className="p-1 rounded-full text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors ml-1"
        title="Configure Agent Workflow"
      >
        <Sliders className="w-3 h-3" />
      </button>

      <button
        onClick={() => setActiveAgent(null)}
        className="p-1 rounded-full text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
        title="Switch back to General AEGIS AI Assistant"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}
