'use client';

import React, { useState } from 'react';
import { useDeliverableStore, DeliverableItem, DeliverableType } from '@/store/useDeliverableStore';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Download,
  FileText,
  FileSpreadsheet,
  Presentation,
  Code,
  ShieldCheck,
  Search,
  Layers,
  Sparkles,
  Check,
  Edit3
} from 'lucide-react';

export function getFileIcon(type: DeliverableType, className = "h-5 w-5") {
  switch (type) {
    case 'docx':
      return <FileText className={`${className} text-blue-600 dark:text-blue-400`} />;
    case 'xlsx':
      return <FileSpreadsheet className={`${className} text-emerald-600 dark:text-emerald-400`} />;
    case 'pptx':
      return <Presentation className={`${className} text-orange-600 dark:text-orange-400`} />;
    case 'py':
      return <Code className={`${className} text-purple-600 dark:text-cyan-400`} />;
    default:
      return <FileText className={`${className} text-blue-600 dark:text-purple-400`} />;
  }
}

export function getBadgeColor(type: DeliverableType) {
  switch (type) {
    case 'docx':
      return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/30';
    case 'xlsx':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/30';
    case 'pptx':
      return 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/30';
    case 'py':
      return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-cyan-500/10 dark:text-cyan-400 dark:border-cyan-500/30';
    default:
      return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/30';
  }
}

interface ArtifactsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ArtifactsModal({ isOpen, onClose }: ArtifactsModalProps) {
  const {
    deliverables,
    selectedDeliverable,
    selectDeliverable,
    downloadDeliverable,
    renameDeliverable,
    filterType,
    setFilterType,
  } = useDeliverableStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);
  const [isEditingModalName, setIsEditingModalName] = useState(false);
  const [editModalNameVal, setEditModalNameVal] = useState('');

  if (!isOpen) return null;

  const filteredItems = deliverables.filter((item) => {
    const matchesType = filterType === 'ALL' || item.type === filterType;
    const matchesSearch =
      item.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.generating_model.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const activeItem: DeliverableItem =
    selectedDeliverable || filteredItems[0] || deliverables[0];

  const handleCopyHash = (hash: string) => {
    if (typeof navigator !== 'undefined') {
      navigator.clipboard.writeText(hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 select-none">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-md"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2, ease: [0.2, 0, 0, 1] }}
          className="relative w-full max-w-5xl h-[85vh] bg-white dark:bg-[#0c0c0e] border border-slate-200 dark:border-[#222226] rounded-3xl shadow-2xl overflow-hidden flex flex-col z-10"
        >
          {/* Top Bar Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-[#1e1e22] bg-slate-50 dark:bg-[#08080a]">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-xl bg-blue-500/10 border border-blue-400/30 flex items-center justify-center">
                <Layers className="h-5 w-5 text-blue-600 dark:text-[#a8c7fa]" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-[#f1f3f4] flex items-center gap-2">
                  MRPL Enterprise Artifacts Vault
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/30">
                    Air-Gapped Sovereign Storage
                  </span>
                </h2>
                <p className="text-xs text-slate-500 dark:text-[#8e918f]">
                  Automated Word (.docx), Excel (.xlsx), PowerPoint (.pptx), and Python (.py) deliverables
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="h-9 w-9 rounded-full hover:bg-slate-200 dark:hover:bg-[#1e1e22] flex items-center justify-center text-slate-500 hover:text-slate-900 dark:text-[#8e918f] dark:hover:text-[#e3e3e3] transition-colors cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Main Layout: Left File Explorer + Right Detail Inspector */}
          <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
            {/* Left Column: Filter & File List */}
            <div className="w-full md:w-80 border-r border-slate-200 dark:border-[#1e1e22] bg-slate-50/50 dark:bg-[#080809] flex flex-col shrink-0">
              {/* Search Box */}
              <div className="p-3 border-b border-slate-200 dark:border-[#18181c]">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400 dark:text-[#8e918f]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search deliverables..."
                    className="w-full pl-8.5 pr-3 py-1.5 text-xs rounded-xl bg-white dark:bg-[#121215] border border-slate-200 dark:border-[#222228] text-slate-900 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#6e7175] focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Type Filter Tabs */}
              <div className="flex items-center gap-1 p-2 border-b border-slate-200 dark:border-[#18181c] overflow-x-auto text-[11px]">
                {(['ALL', 'docx', 'xlsx', 'pptx', 'py'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilterType(t)}
                    className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                      filterType === t
                        ? 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-[#1e1f20] dark:text-[#a8c7fa] dark:border-[#3c4043]'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-[#8e918f] dark:hover:bg-[#121215] dark:hover:text-[#c4c7c5]'
                    }`}
                  >
                    {t === 'py' ? 'CODE' : t.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* File Cards Scroll Area */}
              <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
                {filteredItems.length === 0 ? (
                  <div className="py-12 text-center text-xs text-slate-500 dark:text-[#8e918f]">
                    No artifacts found matching query.
                  </div>
                ) : (
                  filteredItems.map((item) => {
                    const isSelected = activeItem?.id === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => selectDeliverable(item.id)}
                        className={`w-full text-left p-3 rounded-2xl border transition-all flex items-start gap-3 cursor-pointer ${
                          isSelected
                            ? 'bg-blue-50/70 border-blue-500/60 shadow-xs dark:bg-[#16161a] dark:border-blue-500/40'
                            : 'bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300 dark:bg-[#0f0f12] dark:border-[#1c1c20] dark:hover:bg-[#141418]'
                        }`}
                      >
                        <div className="p-2 rounded-xl bg-slate-100 dark:bg-[#18181e] shrink-0 mt-0.5">
                          {getFileIcon(item.type, "h-5 w-5")}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-bold text-xs text-slate-900 dark:text-[#e3e3e3] truncate">
                              {item.filename}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 dark:text-[#8e918f] line-clamp-1 mt-0.5">
                            {item.summary}
                          </p>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400 dark:text-[#6e7175] mt-1.5 font-mono">
                            <span className={`px-1.5 py-0.2 rounded font-sans uppercase font-bold ${getBadgeColor(item.type)}`}>
                              {item.type}
                            </span>
                            <span>{item.size_formatted}</span>
                          </div>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            {/* Right Column: Detailed Preview & Actions */}
            {activeItem ? (
              <div className="flex-1 bg-white dark:bg-[#0c0c0e] flex flex-col min-h-0 overflow-y-auto p-6 space-y-6">
                {/* Title & Download Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-[#1e1e22]">
                  <div className="flex items-start gap-4">
                    <div className="p-3.5 rounded-2xl bg-slate-100 dark:bg-[#141418] border border-slate-200 dark:border-[#26262e] shrink-0 shadow-xs">
                      {getFileIcon(activeItem.type, "h-8 w-8")}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        {isEditingModalName ? (
                          <div className="flex items-center gap-1.5">
                            <input
                              type="text"
                              value={editModalNameVal}
                              onChange={(e) => setEditModalNameVal(e.target.value)}
                              onKeyDown={async (e) => {
                                if (e.key === 'Enter') {
                                  if (editModalNameVal.trim() && editModalNameVal.trim() !== activeItem.filename) {
                                    await renameDeliverable(activeItem.id, editModalNameVal.trim());
                                  }
                                  setIsEditingModalName(false);
                                }
                                if (e.key === 'Escape') setIsEditingModalName(false);
                              }}
                              autoFocus
                              className="px-2.5 py-1 text-sm font-bold rounded-lg border-2 border-blue-500 bg-white dark:bg-[#121215] text-slate-900 dark:text-white outline-none w-56 sm:w-72"
                            />
                            <button
                              onClick={async () => {
                                if (editModalNameVal.trim() && editModalNameVal.trim() !== activeItem.filename) {
                                  await renameDeliverable(activeItem.id, editModalNameVal.trim());
                                }
                                setIsEditingModalName(false);
                              }}
                              className="p-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100 cursor-pointer"
                              title="Save filename"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => setIsEditingModalName(false)}
                              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-white/10 cursor-pointer"
                              title="Cancel"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 group/title">
                            <h3
                              onClick={() => {
                                setEditModalNameVal(activeItem.filename);
                                setIsEditingModalName(true);
                              }}
                              className="text-base sm:text-lg font-extrabold text-slate-900 dark:text-[#f1f3f4] break-all cursor-pointer hover:text-blue-600 transition-colors"
                              title="Click to rename document"
                            >
                              {activeItem.filename}
                            </h3>
                            <button
                              onClick={() => {
                                setEditModalNameVal(activeItem.filename);
                                setIsEditingModalName(true);
                              }}
                              className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50/80 transition-all cursor-pointer"
                              title="Rename Document"
                            >
                              <Edit3 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        )}
                        <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-md border ${getBadgeColor(activeItem.type)}`}>
                          .{activeItem.type}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-[#8e918f] mt-1">
                        Generated by <span className="text-blue-600 dark:text-[#a8c7fa] font-bold">{activeItem.generating_model}</span> &bull; {activeItem.size_formatted}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => {
                        const { useCanvasStore } = require('@/store/useCanvasStore');
                        useCanvasStore.getState().openCanvas(activeItem);
                        onClose();
                      }}
                      className="flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 active:scale-95 transition-all min-h-[44px] cursor-pointer"
                    >
                      <Sparkles className="h-4 w-4 text-white" />
                      <span>Open & Edit Live</span>
                    </button>

                    <button
                      onClick={() => downloadDeliverable(activeItem.id)}
                      className="flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-100 dark:bg-[#1c1c24] dark:hover:bg-[#252530] text-slate-800 dark:text-[#e3e3e3] border border-slate-200 dark:border-[#2e2e3c] text-xs font-semibold active:scale-95 transition-all min-h-[44px] cursor-pointer"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download</span>
                    </button>
                  </div>
                </div>

                {/* Summary Box */}
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-[#121216] border border-slate-200 dark:border-[#1e1e24] space-y-2">
                  <div className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa] uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" />
                    Executive Purpose & Technical Overview
                  </div>
                  <p className="text-xs text-slate-700 dark:text-[#d1d5db] leading-relaxed">
                    {activeItem.summary}
                  </p>
                </div>

                {/* Key Metrics Grid */}
                {activeItem.key_metrics && activeItem.key_metrics.length > 0 && (
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold text-slate-500 dark:text-[#8e918f] uppercase tracking-wider">
                      Extracted Parameters & Metrics
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      {activeItem.key_metrics.map((km, i) => (
                        <div key={i} className="p-3 rounded-xl bg-slate-50 dark:bg-[#111114] border border-slate-200 dark:border-[#1c1c20]">
                          <div className="text-[10px] text-slate-500 dark:text-[#8e918f] truncate font-medium">{km.label}</div>
                          <div className="text-xs font-bold text-slate-900 dark:text-[#e3e3e3] mt-1 font-mono">{km.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SOP Citations */}
                {activeItem.sop_citations && activeItem.sop_citations.length > 0 && (
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold text-slate-500 dark:text-[#8e918f] uppercase tracking-wider">
                      SOP & Compliance Standards
                    </h4>
                    <div className="space-y-1.5">
                      {activeItem.sop_citations.map((cite, i) => (
                        <div key={i} className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-[#0f0f12] border border-slate-200 dark:border-[#1b1b1f] text-xs text-blue-600 dark:text-[#a8c7fa]">
                          <ShieldCheck className="h-4 w-4 text-emerald-500 dark:text-emerald-400 shrink-0" />
                          <span className="font-semibold">{cite}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SHA-256 Tamper-Evident Hash Block */}
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-[#0a0a0c] border border-slate-200 dark:border-[#1c1c20] space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-[#8e918f]">
                    <span className="font-mono flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-bold">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      SHA-256 Cryptographic Signature
                    </span>
                    <button
                      onClick={() => handleCopyHash(activeItem.sha256_hash)}
                      className="text-[10px] text-blue-600 dark:text-[#a8c7fa] hover:underline flex items-center gap-1 cursor-pointer font-semibold"
                    >
                      {copiedHash ? <Check className="h-3 w-3 text-emerald-500 dark:text-emerald-400" /> : 'Copy Hash'}
                    </button>
                  </div>
                  <div className="font-mono text-[10px] text-slate-600 dark:text-[#6e7175] break-all bg-white dark:bg-[#050507] p-2 rounded-lg border border-slate-200 dark:border-[#151518]">
                    {activeItem.sha256_hash}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-xs text-slate-500 dark:text-[#8e918f]">
                Select an artifact to inspect details.
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
