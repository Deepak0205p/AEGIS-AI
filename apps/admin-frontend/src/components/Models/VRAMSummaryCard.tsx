'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useModelStore } from '@/store/useModelStore';
import {
  Cpu,
  Thermometer,
  Server,
  AlertTriangle,
  CheckCircle2,
  Zap,
} from 'lucide-react';

export function VRAMSummaryCard() {
  const { vram, gpuTemperatureC, gpuUtilizationPct, backendType } = useModelStore();

  const totalMb = vram.total_mb > 0 ? vram.total_mb : 8029;
  const usedMb = vram.used_mb > 0 ? vram.used_mb : 4500;
  const usedPercentage = Math.round((usedMb / totalMb) * 100);

  // VRAM status styling
  const isHighPressure = usedPercentage >= 90;
  const isModerate = usedPercentage >= 70 && usedPercentage < 90;

  const barColor = isHighPressure
    ? 'bg-rose-500'
    : isModerate
    ? 'bg-amber-500'
    : 'bg-emerald-500';

  const statusBadgeColor = isHighPressure
    ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
    : isModerate
    ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
    : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';

  return (
    <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-4 font-sans text-gray-900 dark:text-[#ededed]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-gray-800/80 pb-3.5">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 dark:bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-xs font-semibold tracking-wider text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <span>{vram.gpu_available ? 'Dedicated GPU VRAM Budget' : 'Host Device Compute & Memory'}</span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${statusBadgeColor}`}>
                {isHighPressure ? 'HIGH VRAM PRESSURE' : isModerate ? 'MODERATE LOAD' : 'OPTIMAL HEADROOM'}
              </span>
            </h2>
            <p className="text-[11px] font-mono text-gray-500 dark:text-gray-400 mt-0.5">
              Hardware: <span className="text-gray-900 dark:text-gray-200">{vram.gpu_name || 'NVIDIA RTX 4060 Laptop (8GB)'}</span>
            </p>
          </div>
        </div>

        {/* Backend & Temperature Badges */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300">
            <Server className="w-3.5 h-3.5 text-cyan-500" />
            <span className="text-[11px]">Backend: <strong>{backendType || 'OLLaMA :11434'}</strong></span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300">
            <Thermometer className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[11px]">Temp: <strong>{gpuTemperatureC || 48.0}°C</strong></span>
          </div>
        </div>
      </div>

      {/* Dynamic VRAM Allocation Progress Bar */}
      <div className="space-y-2 font-mono">
        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-semibold text-gray-900 dark:text-gray-100 tracking-tight tabular-nums">
              {usedMb.toLocaleString()}
            </span>
            <span className="text-xs text-gray-500">/ {totalMb.toLocaleString()} MB GDDR6</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-900 dark:text-gray-200 tabular-nums">
              {usedPercentage}% Allocated
            </span>
            <span className="text-[10px] text-gray-400">
              (Free: {Math.max(0, totalMb - usedMb).toLocaleString()} MB)
            </span>
          </div>
        </div>

        {/* Progress Track */}
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <motion.div
            className={`h-full ${barColor} rounded-full transition-colors`}
            style={{ width: `${Math.min(100, usedPercentage)}%` }}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, usedPercentage)}%` }}
            transition={{ type: 'spring', stiffness: 100, damping: 20 }}
          />
        </div>
      </div>

      {/* Allocation Breakdown Table */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-gray-100 dark:border-gray-800 font-mono text-xs">
        <div className="space-y-0.5 p-2 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/60">
          <p className="text-[10px] text-gray-400 uppercase">OS &amp; Compositor</p>
          <p className="text-gray-900 dark:text-gray-100 font-bold tabular-nums">
            {vram.os_overhead_mb || 400} MB
          </p>
        </div>

        <div className="space-y-0.5 p-2 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/60">
          <p className="text-[10px] text-cyan-400 uppercase truncate">Primary ({useModelStore.getState().models.find(m => m.is_primary)?.id || 'deepseek-v4-pro:4b'})</p>
          <p className="text-cyan-600 dark:text-cyan-300 font-bold tabular-nums">
            {vram.primary_model_mb || 2480} MB
          </p>
        </div>

        <div className="space-y-0.5 p-2 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/60">
          <p className="text-[10px] text-emerald-400 uppercase truncate">Secondary ({useModelStore.getState().models.find(m => !m.is_primary && m.status === 'active')?.id || 'qwen2.5vl:3b'})</p>
          <p className="text-emerald-600 dark:text-emerald-300 font-bold tabular-nums">
            {vram.secondary_model_mb || 2200} MB
          </p>
        </div>

        <div className="space-y-0.5 p-2 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/60">
          <p className="text-[10px] text-gray-400 uppercase">KV Cache Headroom</p>
          <p className="text-gray-900 dark:text-gray-100 font-bold tabular-nums">
            {vram.kv_cache_mb || 600} MB
          </p>
        </div>
      </div>

      {/* Host System RAM Section (Distinct from GPU VRAM) */}
      {vram.system_ram_total_mb ? (
        <div className="pt-3 border-t border-gray-100 dark:border-gray-800 space-y-2 font-mono">
          <div className="flex items-baseline justify-between">
            <div className="flex items-baseline space-x-2">
              <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                Host System RAM:
              </span>
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 tabular-nums">
                {(vram.system_ram_used_mb || 0).toLocaleString()} MB
              </span>
              <span className="text-xs text-gray-500">
                / {(vram.system_ram_total_mb || 0).toLocaleString()} MB Physical DDR
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-900 dark:text-gray-200 tabular-nums">
                {Math.round(vram.system_ram_percent || 0)}% Used
              </span>
              <span className="text-[10px] text-gray-400">
                (Free: {(vram.system_ram_free_mb || 0).toLocaleString()} MB)
              </span>
            </div>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
            <div
              className="h-full bg-blue-600 rounded-full transition-all"
              style={{ width: `${Math.min(100, Math.round(vram.system_ram_percent || 0))}%` }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
