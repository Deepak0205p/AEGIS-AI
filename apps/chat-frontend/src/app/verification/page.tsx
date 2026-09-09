'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  Edit3,
  UserCheck,
  AlertTriangle,
  FileSpreadsheet,
  Presentation,
  Code2,
  RefreshCw,
  BadgeCheck,
  Search,
  ArrowLeft,
  Filter,
  Check,
  X,
  Lock,
  Download,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import { SearchChatsModal } from '@/components/SearchChatsModal';
import { useVerificationStore, PendingVerificationItem } from '@/store/useVerificationStore';
import { useAuthStore } from '@/store/useAuthStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import { useDeliverableStore } from '@/store/useDeliverableStore';
import { DocumentCanvasPanel } from '@/components/canvas/DocumentCanvasPanel';

export default function VerificationPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuthStore();
  const {
    pendingItems,
    fetchPendingVerifications,
    approveStage1,
    approveStage2,
    rejectItem,
    isActing,
    isLoading,
    stage1Count,
    stage2Count,
    totalPending,
    selectedFilter,
    setSelectedFilter
  } = useVerificationStore();

  const { openCanvas, isOpen: isCanvasOpen } = useCanvasStore();
  const { downloadDeliverable } = useDeliverableStore();

  const [showSearchModal, setShowSearchModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeItem, setActiveItem] = useState<PendingVerificationItem | null>(null);
  const [notesInput, setNotesInput] = useState('');
  const [rejectPromptItem, setRejectPromptItem] = useState<PendingVerificationItem | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  // Access check: User must be authenticated and have verification authorization via Admin or Role
  const userRole = user?.role || '';
  const hasVerificationAccess = Boolean(
    user?.can_verify ||
    ['SUPER_ADMIN', 'PROCESS_LEAD', 'MAINTENANCE_ENG'].includes(userRole)
  );

  useEffect(() => {
    if (hasVerificationAccess) {
      fetchPendingVerifications();
    }
  }, [hasVerificationAccess, fetchPendingVerifications]);

  useEffect(() => {
    if (pendingItems.length > 0) {
      if (!activeItem || !pendingItems.some(i => i.file_id === activeItem.file_id)) {
        setActiveItem(pendingItems[0]);
      }
    } else {
      setActiveItem(null);
    }
  }, [pendingItems, activeItem]);

  const filteredItems = pendingItems.filter((item) => {
    const matchesFilter =
      selectedFilter === 'ALL' ? true : item.verification_status === selectedFilter;
    const matchesSearch =
      item.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.chat_id || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleApprove = async (item: PendingVerificationItem) => {
    let success = false;
    if (item.verification_status === 'PENDING_STAGE_1') {
      success = await approveStage1(
        item.file_id,
        notesInput.trim() || 'Step 1: Technical & process integrity approved'
      );
      if (success) {
        setActionSuccessMsg('Stage 1 Approval successful! Document promoted to Step 2.');
      }
    } else {
      success = await approveStage2(
        item.file_id,
        notesInput.trim() || 'Step 2: Executive compliance & regulatory sign-off certified'
      );
      if (success) {
        setActionSuccessMsg('Stage 2 Final Sign-Off complete! Document marked VERIFIED.');
      }
    }
    setNotesInput('');
    setTimeout(() => setActionSuccessMsg(null), 3500);
  };

  const handleConfirmReject = async () => {
    if (!rejectPromptItem || !rejectReason.trim()) return;
    const success = await rejectItem(rejectPromptItem.file_id, rejectReason.trim());
    if (success) {
      setActionSuccessMsg(`Document ${rejectPromptItem.filename} marked as REJECTED.`);
    }
    setRejectPromptItem(null);
    setRejectReason('');
    setTimeout(() => setActionSuccessMsg(null), 3500);
  };

  const getDocIcon = (type: string) => {
    const t = (type || '').toLowerCase();
    if (['xlsx', 'xls', 'csv'].includes(t)) {
      return <FileSpreadsheet className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />;
    }
    if (['pptx', 'ppt'].includes(t)) {
      return <Presentation className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
    }
    if (['py', 'ipynb', 'sql'].includes(t)) {
      return <Code2 className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
    }
    return <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 dark:bg-[#050507] dark:text-[#e3e3e3] font-sans antialiased selection:bg-blue-500/20 dark:selection:bg-[#4285f4]/30">
      {/* 1. App Sidebar */}
      <AppSidebar
        onOpenSearchModal={() => setShowSearchModal(true)}
        activePage="artifacts"
      />

      {/* 2. Main Verification Workstation */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-100/60 dark:bg-[#07070a] relative">
        {/* Top Header Bar */}
        <header className="flex items-center justify-between px-4 sm:px-6 py-3.5 bg-white dark:bg-[#0c0c0e] border-b border-slate-200 dark:border-[#1f1f26] shrink-0 z-10">
          <div className="flex items-center space-x-3 sm:space-x-4 min-w-0">
            <button
              onClick={() => router.push('/chat')}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#181820] dark:hover:bg-[#22222c] text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-[#282834] transition-colors cursor-pointer shrink-0"
            >
              <ArrowLeft className="h-3.5 w-3.5 text-blue-600 dark:text-[#a8c7fa]" />
              <span className="hidden sm:inline">Back to Chat</span>
            </button>

            <div className="flex items-center space-x-2.5 sm:space-x-3 min-w-0">
              <div className="h-9 w-9 rounded-xl bg-blue-500/10 dark:bg-blue-500/20 border border-blue-500/30 flex items-center justify-center shrink-0">
                <ShieldCheck className="h-5 w-5 text-blue-600 dark:text-[#a8c7fa]" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-sm sm:text-base font-bold text-slate-900 dark:text-[#f1f3f4] truncate">
                    2-Step Human Verification Hub
                  </h1>
                  {user && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-50 text-blue-700 dark:bg-[#181a24] dark:text-[#a8c7fa] border border-blue-200 dark:border-[#2f354a] shrink-0">
                      @{user.username} ({user.role})
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 dark:text-[#8e918f] truncate hidden sm:block">
                  Authorized regulatory sign-off, peer review & canvas modifications for industrial deliverables
                </p>
              </div>
            </div>
          </div>

          {/* Right Action: Refresh queue */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => fetchPendingVerifications()}
              disabled={isLoading || !hasVerificationAccess}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#181820] dark:hover:bg-[#22222c] text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] border border-slate-200 dark:border-[#282834] transition-colors cursor-pointer disabled:opacity-50"
              title="Refresh queue"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden md:inline">Refresh</span>
            </button>
          </div>
        </header>

        {/* Access Denial Guard if user lacks role authority */}
        {!isAuthLoading && !hasVerificationAccess ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <div className="h-16 w-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-600 dark:text-amber-400 mb-4 shadow-sm">
              <Lock className="h-8 w-8" />
            </div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Restricted Access: Verification Authority Required
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mt-2">
              The 2-Step Document Verification hub is restricted to authorized roles (e.g. <strong>Process Lead</strong>, <strong>Maintenance Engineer</strong>, or <strong>Super Administrator</strong>). Contact your refinery system administrator to grant verification privileges.
            </p>
            <button
              onClick={() => router.push('/chat')}
              className="mt-5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-md cursor-pointer"
            >
              Return to Sovereign Chat
            </button>
          </div>
        ) : (
          /* Main Two-Column Clean Workstation */
          <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
            {/* -------------------------------------------------------------
                LEFT COLUMN: Clean Queue List with Search & Stage Pills
               ------------------------------------------------------------- */}
            <div className="w-full md:w-[360px] lg:w-[400px] border-r border-slate-200 dark:border-[#1f1f26] flex flex-col bg-white dark:bg-[#0a0a0d] shrink-0">
              {/* Search & Filter Header */}
              <div className="p-3.5 border-b border-slate-200 dark:border-[#181820] space-y-2.5">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400 dark:text-[#8e918f]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search documents by name or session..."
                    className="w-full pl-8 pr-8 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-[#121217] border border-slate-200 dark:border-[#22222d] text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-2.5 top-2 text-[10px] text-slate-400 hover:text-slate-600 dark:hover:text-white"
                    >
                      &times;
                    </button>
                  )}
                </div>

                {/* Filter Pills */}
                <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-0.5">
                  <button
                    onClick={() => setSelectedFilter('ALL')}
                    className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                      selectedFilter === 'ALL'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-[#15151c] dark:text-[#8e918f] dark:hover:text-white'
                    }`}
                  >
                    All ({totalPending})
                  </button>
                  <button
                    onClick={() => setSelectedFilter('PENDING_STAGE_1')}
                    className={`px-2.5 py-1 rounded-lg font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                      selectedFilter === 'PENDING_STAGE_1'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-[#15151c] dark:text-[#8e918f] dark:hover:text-white'
                    }`}
                  >
                    <span>Step 1 ({stage1Count})</span>
                  </button>
                  <button
                    onClick={() => setSelectedFilter('PENDING_STAGE_2')}
                    className={`px-2.5 py-1 rounded-lg font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                      selectedFilter === 'PENDING_STAGE_2'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-[#15151c] dark:text-[#8e918f] dark:hover:text-white'
                    }`}
                  >
                    <span>Step 2 ({stage2Count})</span>
                  </button>
                </div>
              </div>

              {/* Queue List Items */}
              <div className="flex-1 overflow-y-auto p-2.5 space-y-1.5">
                {filteredItems.length === 0 ? (
                  <div className="py-20 text-center text-xs text-slate-400 dark:text-[#8e918f]">
                    <BadgeCheck className="h-8 w-8 mx-auto mb-2 opacity-40 text-blue-500" />
                    No documents awaiting verification in this filter.
                  </div>
                ) : (
                  filteredItems.map((item) => {
                    const isSelected = activeItem?.file_id === item.file_id;
                    const isStage1 = item.verification_status === 'PENDING_STAGE_1';
                    return (
                      <div
                        key={item.file_id}
                        onClick={() => setActiveItem(item)}
                        className={`p-3 rounded-xl border transition-all cursor-pointer text-left ${
                          isSelected
                            ? 'bg-blue-50/70 dark:bg-[#141724] border-blue-500/60 shadow-xs'
                            : 'bg-white hover:bg-slate-50 dark:bg-[#0c0c10] dark:hover:bg-[#111116] border-slate-200 dark:border-[#1a1a22]'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2.5">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="p-2 rounded-lg bg-slate-100 dark:bg-[#181822] border border-slate-200 dark:border-[#22222f] shrink-0">
                              {getDocIcon(item.file_type)}
                            </div>
                            <div className="min-w-0 flex-1">
                              <h4 className="text-xs font-bold text-slate-900 dark:text-[#f1f3f4] truncate" title={item.filename}>
                                {item.filename}
                              </h4>
                              <div className="text-[10px] text-slate-500 dark:text-[#8e918f] mt-0.5 flex items-center gap-1.5">
                                <span className="uppercase font-mono font-semibold">{item.file_type}</span>
                                <span>&bull;</span>
                                <span>{item.created_at?.slice(0, 16)}</span>
                              </div>
                            </div>
                          </div>

                          {/* Minimalist Stage Badge */}
                          <span
                            className={`text-[9px] font-bold font-mono px-2 py-0.5 rounded-full border shrink-0 ${
                              isStage1
                                ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/25'
                                : 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/25'
                            }`}
                          >
                            {isStage1 ? 'Step 1' : 'Step 2'}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* -------------------------------------------------------------
                RIGHT COLUMN: Clean Document Verification Reviewer Workstation
               ------------------------------------------------------------- */}
            <div className="flex-1 flex flex-col bg-slate-50/50 dark:bg-[#07070a] overflow-y-auto">
              {actionSuccessMsg && (
                <div className="mx-4 sm:mx-6 mt-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 dark:bg-emerald-500/10 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-semibold flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    <span>{actionSuccessMsg}</span>
                  </div>
                  <button onClick={() => setActionSuccessMsg(null)} className="text-xs font-bold">&times;</button>
                </div>
              )}

              {activeItem ? (
                <div className="p-4 sm:p-6 lg:p-8 flex-1 flex flex-col justify-between max-w-4xl">
                  <div className="space-y-6">
                    {/* Document Header Card */}
                    <div className="p-5 rounded-2xl bg-white dark:bg-[#0c0c10] border border-slate-200 dark:border-[#1a1a22] shadow-xs">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-center gap-3.5">
                          <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#141724] border border-slate-200 dark:border-[#22283c]">
                            {getDocIcon(activeItem.file_type)}
                          </div>
                          <div>
                            <h2 className="text-base font-bold text-slate-900 dark:text-[#f1f3f4]">
                              {activeItem.filename}
                            </h2>
                            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-[#8e918f] mt-1">
                              <span>Format: <strong className="uppercase">{activeItem.file_type}</strong></span>
                              <span>&bull;</span>
                              <span>File ID: <code className="font-mono">{activeItem.file_id}</code></span>
                              <span>&bull;</span>
                              <span>Created: {activeItem.created_at?.slice(0, 16)}</span>
                            </div>
                          </div>
                        </div>

                        {/* Top Direct Action: Open Canvas & Download */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => openCanvas(activeItem.file_id)}
                            className="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-600 dark:bg-blue-500/10 dark:hover:bg-blue-500/20 dark:text-[#a8c7fa] border border-blue-200 dark:border-blue-500/30 text-xs font-bold transition-colors cursor-pointer flex items-center gap-1.5"
                            title="Open in Univer document canvas editor"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                            <span>Canvas Edit</span>
                          </button>
                          <button
                            onClick={() => downloadDeliverable(activeItem.file_id)}
                            className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#15151c] dark:hover:bg-[#1e1e28] text-slate-600 dark:text-[#8e918f] border border-slate-200 dark:border-[#22222d] transition-colors cursor-pointer"
                            title="Download original file"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* 2-Step Sequential Verification Progress Box */}
                    <div className="p-5 rounded-2xl bg-white dark:bg-[#0c0c10] border border-slate-200 dark:border-[#1a1a22] shadow-xs space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-[#8e918f]">
                          Multi-Stage Human Verification Status
                        </h3>
                        <span className="text-[11px] font-semibold text-slate-500 dark:text-[#8e918f]">
                          Current Stage: {activeItem.verification_status === 'PENDING_STAGE_1' ? '1 of 2' : '2 of 2'}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {/* Step 1 Box */}
                        <div
                          className={`p-4 rounded-xl border ${
                            activeItem.stage_1_verifier
                              ? 'bg-emerald-50/70 border-emerald-200 dark:bg-emerald-500/10 dark:border-emerald-500/25'
                              : activeItem.verification_status === 'PENDING_STAGE_1'
                              ? 'bg-blue-50/70 border-blue-200 dark:bg-blue-500/10 dark:border-blue-500/25'
                              : 'bg-slate-50 dark:bg-[#111116] border-slate-200 dark:border-[#1e1e28]'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs font-bold text-slate-900 dark:text-[#f1f3f4] flex items-center gap-1.5">
                              {activeItem.stage_1_verifier ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                              ) : (
                                <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                              )}
                              Step 1: Technical & Process Review
                            </span>
                            <span className="text-[10px] font-mono font-bold">
                              {activeItem.stage_1_verifier ? 'COMPLETED' : 'AWAITING'}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-[#8e918f]">
                            {activeItem.stage_1_verifier
                              ? `Approved by @${activeItem.stage_1_verifier} on ${activeItem.stage_1_at?.slice(0, 16)}`
                              : 'Pending evaluation by Process Lead or Maintenance Engineer'}
                          </p>
                          {activeItem.stage_1_notes && (
                            <div className="mt-2 text-[11px] italic bg-white/60 dark:bg-black/20 p-2 rounded-lg text-slate-700 dark:text-[#c4c7c5]">
                              &quot;{activeItem.stage_1_notes}&quot;
                            </div>
                          )}
                        </div>

                        {/* Step 2 Box */}
                        <div
                          className={`p-4 rounded-xl border ${
                            activeItem.stage_2_verifier
                              ? 'bg-emerald-50/70 border-emerald-200 dark:bg-emerald-500/10 dark:border-emerald-500/25'
                              : activeItem.verification_status === 'PENDING_STAGE_2'
                              ? 'bg-purple-50/70 border-purple-200 dark:bg-purple-500/10 dark:border-purple-500/25'
                              : 'bg-slate-50 dark:bg-[#111116] border-slate-200 dark:border-[#1e1e28]'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs font-bold text-slate-900 dark:text-[#f1f3f4] flex items-center gap-1.5">
                              {activeItem.stage_2_verifier ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                              ) : (
                                <UserCheck className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                              )}
                              Step 2: Regulatory Compliance Sign-Off
                            </span>
                            <span className="text-[10px] font-mono font-bold">
                              {activeItem.stage_2_verifier ? 'VERIFIED' : 'LOCKED'}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-[#8e918f]">
                            {activeItem.stage_2_verifier
                              ? `Signed off by @${activeItem.stage_2_verifier} on ${activeItem.stage_2_at?.slice(0, 16)}`
                              : 'Unlocked after Step 1 approval. Authorized by Compliance Chief'}
                          </p>
                          {activeItem.stage_2_notes && (
                            <div className="mt-2 text-[11px] italic bg-white/60 dark:bg-black/20 p-2 rounded-lg text-slate-700 dark:text-[#c4c7c5]">
                              &quot;{activeItem.stage_2_notes}&quot;
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Review Notes Input */}
                    <div className="p-5 rounded-2xl bg-white dark:bg-[#0c0c10] border border-slate-200 dark:border-[#1a1a22] shadow-xs space-y-2">
                      <label className="block text-xs font-bold text-slate-800 dark:text-[#f1f3f4]">
                        Reviewer Sign-off Notes (Optional)
                      </label>
                      <input
                        type="text"
                        value={notesInput}
                        onChange={(e) => setNotesInput(e.target.value)}
                        placeholder="e.g., Validated calculations, engineering SOP compliance, and boundary constraints."
                        className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-[#121217] border border-slate-200 dark:border-[#22222d] text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  {/* Bottom Action Footer */}
                  <div className="mt-8 pt-5 border-t border-slate-200 dark:border-[#1a1a22] flex flex-wrap items-center justify-between gap-3">
                    {/* Make Edits and Open Canvas */}
                    <button
                      onClick={() => openCanvas(activeItem.file_id)}
                      className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#15151c] dark:hover:bg-[#1e1e28] text-slate-700 dark:text-[#c4c7c5] hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-[#22222d] text-xs font-semibold transition-all cursor-pointer flex items-center gap-2"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                      <span>Make Edits in Canvas Editor ↗</span>
                    </button>

                    {/* Reject & Approve Action Buttons */}
                    <div className="flex items-center gap-2.5">
                      <button
                        onClick={() => setRejectPromptItem(activeItem)}
                        className="px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-rose-500/10 dark:hover:bg-rose-500/20 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/30 text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        <span>Reject</span>
                      </button>

                      {/* Dynamic Role-Aware Action Buttons */}
                      {(() => {
                        const isStage1 = activeItem.verification_status === 'PENDING_STAGE_1';
                        const isHigherPost = userRole === 'SUPER_ADMIN';

                        if (isStage1) {
                          return (
                            <button
                              onClick={() => handleApprove(activeItem)}
                              disabled={isActing}
                              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-98 text-white text-xs font-bold shadow-xs shadow-blue-500/20 transition-all cursor-pointer flex items-center gap-2 disabled:opacity-50"
                            >
                              <Check className="h-4 w-4" />
                              <span>Approve Step 1 (Lower Post Review) →</span>
                            </button>
                          );
                        }

                        // Step 2 is strictly reserved for Higher Post (SUPER_ADMIN)
                        if (!isHigherPost) {
                          return (
                            <div className="flex items-center gap-2">
                              <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 px-3 py-2 rounded-xl border border-amber-200 dark:border-amber-500/20">
                                🔒 Locked: Awaiting Higher Post (Compliance Chief) Sign-Off
                              </span>
                            </div>
                          );
                        }

                        return (
                          <button
                            onClick={() => handleApprove(activeItem)}
                            disabled={isActing}
                            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-98 text-white text-xs font-bold shadow-xs shadow-emerald-500/20 transition-all cursor-pointer flex items-center gap-2 disabled:opacity-50"
                          >
                            <BadgeCheck className="h-4 w-4" />
                            <span>Sign-Off Step 2 (Higher Post Final Approval)</span>
                          </button>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 dark:text-[#8e918f]">
                  <ShieldCheck className="h-12 w-12 mb-3 text-blue-500/30" />
                  <h3 className="text-sm font-bold text-slate-700 dark:text-[#f1f3f4]">
                    Select a deliverable from the queue
                  </h3>
                  <p className="text-xs max-w-sm mt-1">
                    Inspect document contents, verify process calculations, or provide formal peer-review sign-off.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Rejection Prompt Modal */}
        <AnimatePresence>
          {rejectPromptItem && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
              <motion.div
                initial={{ scale: 0.96, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.96, opacity: 0 }}
                className="w-full max-w-md p-5 rounded-2xl bg-white dark:bg-[#101014] border border-rose-500/30 shadow-2xl"
              >
                <div className="flex items-center gap-2.5 text-rose-600 dark:text-rose-400 mb-3">
                  <AlertTriangle className="h-5 w-5" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Reject Deliverable
                  </h4>
                </div>
                <p className="text-xs text-slate-600 dark:text-[#8e918f] mb-3">
                  State the specific engineering reason for rejecting <strong>{rejectPromptItem.filename}</strong>:
                </p>
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Operating pressure units incorrect in Section 2, safety limits not adhered to..."
                  rows={3}
                  className="w-full p-3 rounded-xl bg-slate-50 dark:bg-[#15151c] border border-slate-200 dark:border-[#22222d] text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-rose-500 resize-none mb-4"
                />
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => setRejectPromptItem(null)}
                    className="px-3.5 py-1.5 rounded-xl text-xs font-semibold hover:bg-slate-100 dark:hover:bg-[#1a1a22] text-slate-600 dark:text-[#8e918f]"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmReject}
                    disabled={!rejectReason.trim()}
                    className="px-4 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all disabled:opacity-50"
                  >
                    Confirm Rejection
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* univer canvas modal */}
        <DocumentCanvasPanel />
      </main>

      {/* global search */}
      <SearchChatsModal
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
      />
    </div>
  );
}
