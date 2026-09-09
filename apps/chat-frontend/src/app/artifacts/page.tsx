'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  Search,
  X,
  Sparkles,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useDeliverableStore, DeliverableItem } from '@/store/useDeliverableStore';
import { useChatStore } from '@/store/useChatStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import { DocumentCanvasPanel } from '@/components/canvas/DocumentCanvasPanel';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import { useSidebarStore } from '@/store/useSidebarStore';
import { SearchChatsModal } from '@/components/SearchChatsModal';
import { motion, AnimatePresence } from 'framer-motion';

// Premium Refined Vector Logos for Document Types
function ModernWordLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <defs>
        <linearGradient id="docBlueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#2563EB" />
          <stop offset="100%" stopColor="#1D4ED8" />
        </linearGradient>
      </defs>
      <rect x="3" y="3" width="22" height="22" rx="6" fill="url(#docBlueGrad)" />
      <path d="M8 8h12M8 12h12M8 16h8" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="15" y="14" width="7" height="6" rx="2" fill="#60A5FA" />
      <path d="M17 16l1.5 2 2.5-3" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ModernExcelLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <defs>
        <linearGradient id="sheetGreenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#059669" />
          <stop offset="100%" stopColor="#047857" />
        </linearGradient>
      </defs>
      <rect x="3" y="3" width="22" height="22" rx="6" fill="url(#sheetGreenGrad)" />
      <rect x="7" y="7" width="6.5" height="6.5" rx="1.5" fill="#FFFFFF" fillOpacity="0.9" />
      <rect x="14.5" y="7" width="6.5" height="6.5" rx="1.5" fill="#34D399" />
      <rect x="7" y="14.5" width="6.5" height="6.5" rx="1.5" fill="#34D399" />
      <rect x="14.5" y="14.5" width="6.5" height="6.5" rx="1.5" fill="#FFFFFF" fillOpacity="0.9" />
    </svg>
  );
}

function ModernPowerPointLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <defs>
        <linearGradient id="pptOrangeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#EA580C" />
          <stop offset="100%" stopColor="#C2410C" />
        </linearGradient>
      </defs>
      <rect x="3" y="3" width="22" height="22" rx="6" fill="url(#pptOrangeGrad)" />
      <path d="M7 17V8a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1Z" stroke="#FED7AA" strokeWidth="1.5" />
      <path d="M14 18v3m-3 0h6" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="14" cy="12.5" r="2.5" fill="#FFFFFF" />
      <path d="M14 10a2.5 2.5 0 0 1 2.5 2.5H14V10z" fill="#FB923C" />
    </svg>
  );
}

function ModernPythonLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <defs>
        <linearGradient id="pyPurpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#7C3AED" />
          <stop offset="100%" stopColor="#6D28D9" />
        </linearGradient>
      </defs>
      <rect x="3" y="3" width="22" height="22" rx="6" fill="url(#pyPurpleGrad)" />
      <path d="M9.5 10.5L6.5 14l3 3.5M18.5 10.5l3 3.5-3 3.5M15 9l-2 10" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function getProfessionalFileMeta(type: string) {
  switch (type.toLowerCase()) {
    case 'docx':
      return {
        label: 'Word Document',
        ext: 'DOCX',
        color: 'text-blue-600 dark:text-blue-400',
        badgeBg: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/25',
        glowColor: 'hover:border-blue-500/40 hover:shadow-[0_0_30px_rgba(59,130,246,0.12)]',
        icon: <ModernWordLogo className="h-5 w-5 sm:h-6 sm:w-6 shrink-0" />
      };
    case 'xlsx':
      return {
        label: 'Excel Spreadsheet',
        ext: 'XLSX',
        color: 'text-emerald-600 dark:text-emerald-400',
        badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/25',
        glowColor: 'hover:border-emerald-500/40 hover:shadow-[0_0_30px_rgba(16,185,129,0.12)]',
        icon: <ModernExcelLogo className="h-5 w-5 sm:h-6 sm:w-6 shrink-0" />
      };
    case 'pptx':
      return {
        label: 'PowerPoint Deck',
        ext: 'PPTX',
        color: 'text-orange-600 dark:text-orange-400',
        badgeBg: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/25',
        glowColor: 'hover:border-orange-500/40 hover:shadow-[0_0_30px_rgba(249,115,22,0.12)]',
        icon: <ModernPowerPointLogo className="h-5 w-5 sm:h-6 sm:w-6 shrink-0" />
      };
    case 'py':
      return {
        label: 'Python Simulation',
        ext: 'PYTHON',
        color: 'text-purple-600 dark:text-purple-400',
        badgeBg: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/25',
        glowColor: 'hover:border-purple-500/40 hover:shadow-[0_0_30px_rgba(124,58,237,0.12)]',
        icon: <ModernPythonLogo className="h-5 w-5 sm:h-6 sm:w-6 shrink-0" />
      };
    default:
      return {
        label: 'Document',
        ext: type.toUpperCase(),
        color: 'text-slate-600 dark:text-slate-300',
        badgeBg: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-500/10 dark:text-slate-300 dark:border-slate-500/25',
        glowColor: 'hover:border-slate-400',
        icon: <FileText className="h-5 w-5 sm:h-6 sm:w-6 text-slate-500 shrink-0" />
      };
  }
}

const CATEGORIES = [
  { id: 'ALL', label: 'All' },
  { id: 'docx', label: 'Docs' },
  { id: 'xlsx', label: 'Sheets' },
  { id: 'pptx', label: 'Slides' },
  { id: 'py', label: 'Code' }
];

export default function ArtifactsPage() {
  const router = useRouter();
  const {
    deliverables,
    downloadDeliverable,
    filterType,
    setFilterType,
    searchQuery,
    setSearchQuery,
    fetchDiskDeliverables,
  } = useDeliverableStore();

  const { openCanvas, isOpen: isCanvasOpen } = useCanvasStore();
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);

  const { open: openSidebar, toggle } = useSidebarStore();

  React.useEffect(() => {
    fetchDiskDeliverables();
  }, [fetchDiskDeliverables]);

  React.useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth >= 768) {
      openSidebar();
    }
  }, [openSidebar]);

  const filteredItems = deliverables.filter((item) => {
    const matchesType = filterType === 'ALL' || item.type.toLowerCase() === filterType.toLowerCase();
    const matchesSearch =
      item.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.generating_model.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const handleSendToAI = async (item: DeliverableItem) => {
    const sessionId = await useChatStore.getState().createNewChat();
    const promptText = `Please analyze and work with the deliverable "${item.filename}" (${item.type.toUpperCase()}).`;
    useChatStore.getState().setCurrentInput(promptText);
    router.push(`/chat/${sessionId}`);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 dark:bg-[#050507] dark:text-[#e3e3e3] font-sans antialiased selection:bg-blue-500/20 dark:selection:bg-[#4285f4]/30">
      {/* 1. Shared Modular Sidebar */}
      <AppSidebar
        onOpenSearchModal={() => setShowSearchModal(true)}
        activePage="artifacts"
      />

      {/* 2. Main Window & Side-by-Side Canvas Container */}
      <div className="flex-1 flex h-full min-h-0 overflow-hidden relative bg-slate-100/60 dark:bg-[#07070a]">
        <main className={`flex flex-col h-full min-h-0 overflow-hidden relative transition-all duration-300 ${
          isCanvasOpen
            ? 'hidden md:flex flex-1 md:w-[45vw] lg:w-[48vw] xl:w-[50vw]'
            : 'flex-1 w-full'
        }`}>

        {/* ============================================================
            MOBILE HEADER — Single compact bar (< md)
            ============================================================ */}
        <div className="md:hidden flex items-center justify-between px-3 py-2 bg-white/95 border-b border-slate-200 text-slate-900 dark:bg-[#080808]/95 dark:border-[#1a1a1a] dark:text-[#e3e3e3] backdrop-blur-xl z-20 shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={toggle}
              aria-label="Open sidebar"
              className="h-11 w-11 rounded-xl hover:bg-slate-100 dark:hover:bg-[#1e1f20] active:bg-slate-200 dark:active:bg-[#282a2c] flex items-center justify-center text-slate-700 dark:text-[#c4c7c5] transition-colors cursor-pointer touch-manipulation"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                <line x1="4" x2="20" y1="12" y2="12" />
                <line x1="4" x2="20" y1="6" y2="6" />
                <line x1="4" x2="20" y1="18" y2="18" />
              </svg>
            </button>
            <span className="text-sm font-bold text-slate-900 dark:text-[#e3e3e3]">
              Artifacts
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setMobileSearchOpen(!mobileSearchOpen)}
              className="h-11 w-11 rounded-xl hover:bg-slate-100 dark:hover:bg-[#1e1f20] text-slate-600 dark:text-[#c4c7c5] flex items-center justify-center cursor-pointer touch-manipulation"
              aria-label="Search"
            >
              <Search className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Mobile Collapsible Search Bar */}
        <AnimatePresence>
          {mobileSearchOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="md:hidden overflow-hidden border-b border-slate-200 dark:border-[#1a1a1a] bg-white/95 dark:bg-[#080808]/95 backdrop-blur-xl z-10 shrink-0"
            >
              <div className="px-3 py-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-[#8e918f]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search deliverables..."
                    autoFocus
                    className="w-full pl-10 pr-10 py-2.5 text-sm rounded-xl bg-slate-50 dark:bg-[#111116] border border-slate-200 dark:border-[#202028] text-slate-900 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#6e7175] focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 hover:text-slate-900 dark:text-[#8e918f] dark:hover:text-white cursor-pointer flex items-center justify-center"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ============================================================
            DESKTOP TOOLBAR — Filter tabs + Search (md+)
            ============================================================ */}
        <div className="hidden md:flex px-6 py-3.5 bg-white/95 dark:bg-[#0a0a0e]/95 backdrop-blur-xl border-b border-slate-200 dark:border-[#181820] items-center justify-between gap-3 shrink-0 z-10 shadow-xs">
          {/* Category Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs py-0.5 scrollbar-none">
            {CATEGORIES.map((cat) => {
              const isActive = filterType.toLowerCase() === cat.id.toLowerCase();
              return (
                <button
                  key={cat.id}
                  onClick={() => setFilterType(cat.id as any)}
                  className={`px-3.5 py-1.5 rounded-full text-[12px] font-bold transition-all duration-150 whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-xs dark:bg-[#181a24] dark:text-[#a8c7fa] dark:border-[#2f354a]'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-[#8e918f] dark:hover:bg-[#121217] dark:hover:text-[#e3e3e3] border border-transparent font-medium'
                  }`}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>

          {/* Right Controls */}
          <div className="flex items-center space-x-3">
            <div className="relative w-64">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400 dark:text-[#8e918f]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search deliverables..."
                className="w-full pl-8 pr-8 py-1.5 text-xs rounded-full bg-slate-50 dark:bg-[#111116] border border-slate-200 dark:border-[#202028] text-slate-900 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#6e7175] focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-2 text-[10px] text-slate-400 hover:text-slate-900 dark:text-[#8e918f] dark:hover:text-white cursor-pointer"
                >
                  &times;
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ============================================================
            MOBILE FILTER PILLS — Horizontal scroll (< md)
            ============================================================ */}
        <div className="md:hidden px-3 py-2 bg-white/95 dark:bg-[#080808]/95 border-b border-slate-200 dark:border-[#1a1a1a] shrink-0 z-10">
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none pb-0.5">
            {CATEGORIES.map((cat) => {
              const isActive = filterType.toLowerCase() === cat.id.toLowerCase();
              return (
                <button
                  key={cat.id}
                  onClick={() => setFilterType(cat.id as any)}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all duration-150 whitespace-nowrap cursor-pointer touch-manipulation ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-xs dark:bg-[#181a24] dark:text-[#a8c7fa] dark:border-[#2f354a]'
                      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-[#8e918f] dark:hover:bg-[#121217] dark:hover:text-[#e3e3e3] border border-transparent'
                  }`}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* ============================================================
            MAIN BODY VIEW (Clean Minimalist Grid Gallery)
            ============================================================ */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-8">
          <div className="max-w-7xl mx-auto">
            {filteredItems.length === 0 ? (
              <div className="py-24 text-center text-xs text-slate-500 dark:text-[#8e918f] bg-white dark:bg-[#0c0c10] rounded-2xl md:rounded-3xl border border-slate-200 dark:border-[#1a1a22]">
                No deliverables match the selected filter or search term.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-5">
                {filteredItems.map((item) => {
                  const meta = getProfessionalFileMeta(item.type);
                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.15 }}
                      onClick={() => openCanvas(item)}
                      className={`group relative flex flex-col justify-between rounded-xl md:rounded-2xl bg-white hover:bg-slate-50/90 border border-slate-200 dark:bg-[#0c0d14] dark:hover:bg-[#10121b] dark:border-[#1a1c28] ${meta.glowColor} transition-all duration-200 overflow-hidden shadow-xs hover:shadow-md cursor-pointer active:scale-[0.98] touch-manipulation`}
                    >
                      {/* Card Body: Only Doc Icon, File Name & Doc Type */}
                      <div className="p-4 sm:p-5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-3 min-w-0 flex-1">
                            <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#141724] border border-slate-200 dark:border-[#22283c] shadow-xs shrink-0 group-hover:scale-105 transition-transform duration-200">
                              {meta.icon}
                            </div>
                            <div className="min-w-0 flex-1">
                              <h3 className="text-sm font-bold text-slate-900 dark:text-[#f1f3f4] truncate tracking-tight group-hover:text-blue-600 dark:group-hover:text-[#a8c7fa] transition-colors" title={item.filename}>
                                {item.filename}
                              </h3>
                              <div className="text-[11px] text-slate-500 dark:text-[#8e918f] mt-0.5">
                                <span>{meta.label}</span>
                              </div>
                            </div>
                          </div>

                          {/* File Extension Badge */}
                          <span className={`text-[10px] font-mono font-bold tracking-wider px-2.5 py-0.5 rounded-full border shrink-0 ${meta.badgeBg}`}>
                            {meta.ext}
                          </span>
                        </div>
                      </div>

                      {/* Card Footer: Status Pill + Actions (Download & Use with AI) */}
                      <div className="px-4 sm:px-5 py-3 bg-slate-50 dark:bg-[#090a10] border-t border-slate-100 dark:border-[#151722] flex items-center justify-between gap-2">
                        {/* 2-Step Verification Live Status Badge */}
                        {(() => {
                          const status = item.verification_status || 'PENDING_STAGE_1';
                          if (status === 'VERIFIED') {
                            return (
                              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20 text-[11px] font-semibold" title={item.stage_2_verifier ? `Verified & signed by @${item.stage_2_verifier}` : 'Verified'}>
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                <span>VERIFIED</span>
                              </div>
                            );
                          }
                          if (status === 'PENDING_STAGE_2') {
                            return (
                              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200/80 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/20 text-[11px] font-semibold" title="Step 1 complete. Awaiting final sign-off (Step 2)">
                                <span className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />
                                <span>STEP 2: SIGN-OFF</span>
                              </div>
                            );
                          }
                          if (status === 'REJECTED') {
                            return (
                              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20 text-[11px] font-semibold" title={item.reject_reason ? `Rejected: ${item.reject_reason}` : 'Rejected'}>
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                                <span>REJECTED</span>
                              </div>
                            );
                          }
                          return (
                            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20 text-[11px] font-semibold" title="Awaiting Step 1 Technical Peer Review">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                              <span>STEP 1: REVIEW</span>
                            </div>
                          );
                        })()}

                        {/* Action Buttons: Download + Compact Ask AI Button */}
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              downloadDeliverable(item.id);
                            }}
                            aria-label="Download document"
                            className="h-7 w-7 sm:h-8 sm:w-8 rounded-lg bg-white hover:bg-slate-100 dark:bg-[#12141e] dark:hover:bg-[#1a1e2e] border border-slate-200 dark:border-[#22283a] text-slate-600 dark:text-[#8e918f] hover:text-slate-900 dark:hover:text-[#f1f3f4] transition-all cursor-pointer flex items-center justify-center touch-manipulation shadow-xs"
                            title="Download file"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                          
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSendToAI(item);
                            }}
                            className="h-7 sm:h-8 px-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-[11px] font-semibold shadow-xs shadow-blue-500/20 transition-all active:scale-[0.97] cursor-pointer flex items-center gap-1 touch-manipulation"
                            title="Work with this file in AI Chat"
                          >
                            <Sparkles className="h-3 w-3" />
                            <span>Ask AI</span>
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        </main>

        {/* Mount Live Univer Canvas Panel (Side-by-Side Flex) */}
        <DocumentCanvasPanel />
      </div>

      {/* Global Search Chats Command Palette Modal */}
      <SearchChatsModal
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
      />
    </div>
  );
}
