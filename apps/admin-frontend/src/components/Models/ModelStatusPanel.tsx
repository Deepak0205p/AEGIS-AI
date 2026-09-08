'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useModelStore } from '@/store/useModelStore';
import { VRAMSummaryCard } from './VRAMSummaryCard';
import { ModelCardGrid } from './ModelCardGrid';
import { SwapEventLog } from './SwapEventLog';
import { ComputeNodeManager } from './ComputeNodeManager';
import {
  ArrowRightLeft,
  RefreshCw,
  Zap,
  Cpu,
  Layers,
  CheckCircle2,
  SlidersHorizontal,
} from 'lucide-react';

export function ModelStatusPanel() {
  const {
    models,
    activePrimaryId,
    activeSecondaryId,
    isSwapping,
    isPolling,
    startPolling,
    stopPolling,
    triggerModelSwap,
  } = useModelStore();

  const [selectedSwapTarget, setSelectedSwapTarget] = useState<string>('qwen2-vl-2b');

  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  const secondaryModels = models.filter((m) => !m.is_primary);

  const handleQuickSwap = () => {
    if (!selectedSwapTarget || selectedSwapTarget === activeSecondaryId) return;
    triggerModelSwap(selectedSwapTarget);
  };

  return (
    <div className="space-y-4 font-sans text-gray-900 dark:text-[#ededed]">
      {/* Real-time Status & Quick Hot-Swap Toolbar */}
      <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-emerald-950/40 border border-emerald-800/50 text-emerald-400 text-[11px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>2s Telemetry Polling: ACTIVE</span>
          </div>
          <span className="text-gray-400 dark:text-gray-500">|</span>
          <span className="text-gray-600 dark:text-gray-300">
            Active Models: <strong>{activePrimaryId || 'qwen3-4b'}</strong> + <strong>{activeSecondaryId || 'qwen2.5-coder-3b'}</strong>
          </span>
        </div>

        {/* Quick Hot-Swap Dropdown & Action */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <label className="text-gray-500 text-[11px] whitespace-nowrap">Hot-Swap Secondary:</label>
          <select
            value={selectedSwapTarget}
            onChange={(e) => setSelectedSwapTarget(e.target.value)}
            disabled={isSwapping}
            className="px-2.5 py-1.5 bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800 rounded-lg text-xs text-gray-900 dark:text-gray-200 focus:outline-none focus:border-cyan-500"
          >
            {secondaryModels.length > 0 ? (
              secondaryModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name || m.name} ({m.vram_mb} MB)
                </option>
              ))
            ) : (
              <option value="qwen2.5vl:3b">Sovereign Multimodal (qwen2.5vl:3b)</option>
            )}
          </select>

          <button
            onClick={handleQuickSwap}
            disabled={isSwapping || selectedSwapTarget === activeSecondaryId}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-xs transition-colors cursor-pointer"
          >
            <ArrowRightLeft className={`w-3.5 h-3.5 ${isSwapping ? 'animate-spin' : ''}`} />
            <span>{isSwapping ? 'Swapping VRAM...' : 'Hot-Swap (<1.2s)'}</span>
          </button>
        </div>
      </div>

      {/* Dynamic VRAM Summary Gauge */}
      <VRAMSummaryCard />

      {/* Distributed Compute Nodes & Worker Devices Manager */}
      <ComputeNodeManager />

      {/* Model Catalog Grid */}
      <ModelCardGrid />

      {/* LRU Swapping Event Log */}
      <SwapEventLog />
    </div>
  );
}
