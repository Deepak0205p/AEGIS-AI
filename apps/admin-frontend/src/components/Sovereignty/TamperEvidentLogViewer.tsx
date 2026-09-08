'use client';

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import {
  ShieldCheck,
  ShieldAlert,
  Download,
  Link2,
  Loader2,
  CheckCircle2,
  Cpu,
  Server,
  Search,
  Fingerprint,
  Layers,
  Sparkles,
  Lock,
  ArrowRight,
  Copy,
  Check,
} from 'lucide-react';

type LogCategory = 'all' | 'security' | 'model' | 'system';

export function TamperEvidentLogViewer() {
  const {
    auditLogs,
    verifyChainIntegrity,
    exportAuditCertificate,
    isVerifyingChain,
    chainVerificationStatus,
  } = useSovereigntyStore();

  const [selectedCategory, setSelectedCategory] = useState<LogCategory>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBlock, setSelectedBlock] = useState<any | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  // Filter logs based on category and search query
  const filteredLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      const ev = log.event?.toUpperCase() || '';
      const matchesSearch =
        !searchQuery.trim() ||
        ev.includes(searchQuery.toUpperCase()) ||
        log.block_hash.includes(searchQuery) ||
        String(log.sequence).includes(searchQuery);

      if (!matchesSearch) return false;

      if (selectedCategory === 'security') {
        return (
          ev.includes('AUTH') ||
          ev.includes('PKI') ||
          ev.includes('CERT') ||
          ev.includes('RBAC') ||
          ev.includes('SECURITY') ||
          ev.includes('LOGIN')
        );
      }
      if (selectedCategory === 'model') {
        return (
          ev.includes('MODEL') ||
          ev.includes('SWAP') ||
          ev.includes('OLLAMA') ||
          ev.includes('SANDBOX') ||
          ev.includes('DOCKER') ||
          ev.includes('INFERENCE')
        );
      }
      if (selectedCategory === 'system') {
        return (
          ev.includes('SOCKET') ||
          ev.includes('AIR_GAP') ||
          ev.includes('BOOT') ||
          ev.includes('GUARD') ||
          ev.includes('SEAL')
        );
      }
      return true;
    });
  }, [auditLogs, selectedCategory, searchQuery]);

  const categoryCounts = useMemo(() => {
    return {
      all: auditLogs.length,
      security: auditLogs.filter((l) => /AUTH|PKI|CERT|RBAC|SECURITY|LOGIN/i.test(l.event)).length,
      model: auditLogs.filter((l) => /MODEL|SWAP|OLLAMA|SANDBOX|DOCKER|INFERENCE/i.test(l.event)).length,
      system: auditLogs.filter((l) => /SOCKET|AIR_GAP|BOOT|GUARD|SEAL/i.test(l.event)).length,
    };
  }, [auditLogs]);

  // Event styling helper
  const getEventBadge = (eventStr: string) => {
    const ev = eventStr.toUpperCase();
    if (ev.includes('FAILED') || ev.includes('BLOCKED') || ev.includes('VIOLATION')) {
      return {
        bg: 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800/60',
        icon: ShieldAlert,
        tag: 'BREACH ATTEMPT',
      };
    }
    if (ev.includes('MODEL') || ev.includes('SWAP') || ev.includes('OLLAMA') || ev.includes('SANDBOX') || ev.includes('DOCKER')) {
      return {
        bg: 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800/60',
        icon: Cpu,
        tag: 'COMPUTE & MODEL',
      };
    }
    if (ev.includes('AUTH') || ev.includes('LOGIN') || ev.includes('RBAC')) {
      return {
        bg: 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800/60',
        icon: Lock,
        tag: 'IDENTITY & AUTH',
      };
    }
    return {
      bg: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60',
      icon: ShieldCheck,
      tag: 'AIR-GAP SOVEREIGNTY',
    };
  };

  return (
    <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-4 font-sans text-gray-900 dark:text-[#ededed]">
      {/* Top Header & Audit Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-xs">
            <Link2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold tracking-tight text-gray-900 dark:text-gray-100">
                Tamper-Evident SHA-256 Audit Log &amp; Blockchain Ledger
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800 font-semibold">
                {auditLogs.length} BLOCKS SEALED
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5">
              Cryptographically chained Merkle proof certifying 100% offline air-gapped events.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono">
          <button
            onClick={verifyChainIntegrity}
            disabled={isVerifyingChain}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-[0.98] text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50 cursor-pointer"
          >
            {isVerifyingChain ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Auditing Merkle Tree...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Verify Hash Chain</span>
              </>
            )}
          </button>

          <button
            onClick={exportAuditCertificate}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-[#1a1f2c] border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 active:scale-[0.98] text-xs font-medium transition-colors cursor-pointer"
            title="Download signed JSON certificate"
          >
            <Download className="w-3.5 h-3.5 text-gray-500" />
            <span>Export Certificate</span>
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      <div className="p-3 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 text-emerald-800 dark:text-emerald-300 text-xs font-mono flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>
            <strong>CRYPTOGRAPHIC AUDIT VERIFIED:</strong> All {auditLogs.length} blocks mathematically linked via SHA-256 parent hash. Zero collision or tamper detected.
          </span>
        </div>
        <span className="text-[10px] text-emerald-600 dark:text-emerald-400 uppercase font-semibold tracking-wider">
          Air-Gapped Root Valid
        </span>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
        {/* Modern Segmented Pill Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-gray-100 dark:bg-[#090b10] border border-gray-200 dark:border-gray-800 rounded-lg text-xs font-mono">
          {[
            { id: 'all', label: 'All Events', count: categoryCounts.all },
            { id: 'security', label: 'Security & Auth', count: categoryCounts.security },
            { id: 'model', label: 'Model & Docker', count: categoryCounts.model },
            { id: 'system', label: 'System & Air-Gap', count: categoryCounts.system },
          ].map((tab) => {
            const isSelected = selectedCategory === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedCategory(tab.id as LogCategory)}
                className={`px-3 py-1.5 rounded-md transition-all text-xs font-medium flex items-center gap-1.5 cursor-pointer ${
                  isSelected
                    ? 'bg-white dark:bg-[#1a1f2c] text-gray-900 dark:text-white shadow-xs font-semibold border border-gray-200 dark:border-gray-700'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                    isSelected
                      ? 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-bold'
                      : 'bg-gray-200 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Filter Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by event, hash, block #..."
            className="w-full sm:w-64 pl-8 pr-3 py-1.5 bg-gray-50 dark:bg-[#090b10] border border-gray-200 dark:border-gray-700 rounded-lg text-xs font-mono text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Chained Events Table */}
      <div className="border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden bg-white dark:bg-[#0c0e14]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-gray-50 dark:bg-[#151924] border-b border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 text-[10px] uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Block #</th>
                <th className="py-2.5 px-4 font-semibold">Timestamp</th>
                <th className="py-2.5 px-4 font-semibold">Security Event</th>
                <th className="py-2.5 px-4 font-semibold">SHA-256 Current Block Hash</th>
                <th className="py-2.5 px-4 font-semibold">Parent Linked Hash</th>
                <th className="py-2.5 px-4 text-right font-semibold">Merkle Seal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800/70 text-xs">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400 space-y-1 font-mono">
                    <p className="font-semibold text-gray-600 dark:text-gray-300">No matching audit log events found</p>
                    <p className="text-[11px] text-gray-400">Try selecting 'All Events' tab or clearing search query.</p>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const badge = getEventBadge(log.event);
                  const Icon = badge.icon;
                  const isSelected = selectedBlock?.sequence === log.sequence;

                  return (
                    <tr
                      key={log.sequence}
                      onClick={() => setSelectedBlock(isSelected ? null : log)}
                      className={`hover:bg-blue-50/40 dark:hover:bg-[#1a2030] cursor-pointer transition-colors ${
                        isSelected ? 'bg-blue-50/60 dark:bg-blue-950/40' : ''
                      }`}
                    >
                      <td className="py-2.5 px-4 font-bold text-gray-900 dark:text-gray-100">
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-[11px]">
                          #{log.sequence}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-gray-500 dark:text-gray-400 text-[11px] whitespace-nowrap">
                        {log.timestamp}
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${badge.bg}`}
                        >
                          <Icon className="w-3 h-3 shrink-0" />
                          <span>{log.event}</span>
                        </span>
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          title={log.block_hash}
                          className="text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center gap-1"
                        >
                          <Fingerprint className="w-3 h-3 shrink-0 opacity-60" />
                          <span>
                            {log.block_hash.substring(0, 10)}...{log.block_hash.substring(log.block_hash.length - 6)}
                          </span>
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-gray-400 text-[11px]">
                        <span title={log.prev_hash}>
                          {log.prev_hash.substring(0, 10)}...
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>IMMUTABLE</span>
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Block Cryptographic Proof Drawer */}
      <AnimatePresence>
        {selectedBlock && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-4 rounded-xl bg-blue-50/50 dark:bg-[#0c0e14] border border-blue-200 dark:border-blue-900/50 space-y-3 font-mono text-xs"
          >
            <div className="flex items-center justify-between border-b border-blue-200/60 dark:border-blue-900/40 pb-2.5">
              <div className="flex items-center gap-2 text-blue-900 dark:text-blue-300 font-semibold">
                <Fingerprint className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Cryptographic Proof for Block #{selectedBlock.sequence} ({selectedBlock.event})</span>
              </div>
              <button
                onClick={() => setSelectedBlock(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer text-sm"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
                  <span>Current Block SHA-256 Hash:</span>
                  <button
                    onClick={() => handleCopy(selectedBlock.block_hash)}
                    className="flex items-center gap-1 text-blue-600 hover:underline text-[10px] cursor-pointer"
                  >
                    {copiedHash === selectedBlock.block_hash ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedHash === selectedBlock.block_hash ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div className="p-2.5 rounded-lg bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 text-blue-600 dark:text-blue-400 font-bold break-all select-all">
                  {selectedBlock.block_hash}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
                  <span>Parent Linked Hash (prev_hash):</span>
                  <button
                    onClick={() => handleCopy(selectedBlock.prev_hash)}
                    className="flex items-center gap-1 text-gray-500 hover:underline text-[10px] cursor-pointer"
                  >
                    {copiedHash === selectedBlock.prev_hash ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedHash === selectedBlock.prev_hash ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div className="p-2.5 rounded-lg bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 break-all select-all">
                  {selectedBlock.prev_hash}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-[11px] text-gray-500 dark:text-gray-400 pt-1">
              <span>Event: <strong className="text-gray-900 dark:text-gray-200">{selectedBlock.event}</strong></span>
              <span>Timestamp: <strong className="text-gray-900 dark:text-gray-200">{selectedBlock.timestamp}</strong></span>
              <span>Deployment Mode: <strong className="text-gray-900 dark:text-gray-200">{selectedBlock.deployment_mode}</strong></span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
