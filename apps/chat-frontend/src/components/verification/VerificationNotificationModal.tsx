'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  Edit3,
  ExternalLink,
  ChevronRight,
  UserCheck,
  AlertTriangle,
  X,
  FileSpreadsheet,
  Presentation,
  Code2,
  RefreshCw,
  Info,
  BadgeCheck,
  Send,
  SlidersHorizontal
} from 'lucide-react';
import { useVerificationStore, PendingVerificationItem } from '@/store/useVerificationStore';
import { useAuthStore } from '@/store/useAuthStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import { useDeliverableStore } from '@/store/useDeliverableStore';

export function VerificationNotificationModal() {
  const {
    isModalOpen,
    closeVerificationModal,
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

  const { user } = useAuthStore();
  const { openCanvas } = useCanvasStore();
  const { downloadDeliverable } = useDeliverableStore();

  const [activeItem, setActiveItem] = useState<PendingVerificationItem | null>(null);
  const [rejectPromptItem, setRejectPromptItem] = useState<PendingVerificationItem | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [notesInput, setNotesInput] = useState('');

  useEffect(() => {
    if (isModalOpen) {
      fetchPendingVerifications();
    }
  }, [isModalOpen, fetchPendingVerifications]);

  useEffect(() => {
    if (pendingItems.length > 0 && !activeItem) {
      setActiveItem(pendingItems[0]);
    } else if (pendingItems.length === 0) {
      setActiveItem(null);
    }
  }, [pendingItems, activeItem]);

  if (!isModalOpen) return null;

  // Role permissions check
  const userRole = user?.role || 'FIELD_OPERATOR';
  const canVerifyStage1 = ['PROCESS_LEAD', 'MAINTENANCE_ENG', 'SUPER_ADMIN'].includes(userRole);
  const canVerifyStage2 = ['SUPER_ADMIN', 'FIELD_OPERATOR'].includes(userRole);

  const filteredItems = pendingItems.filter((item) => {
    if (selectedFilter === 'ALL') return true;
    return item.verification_status === selectedFilter;
  });

  const handleApprove = async (item: PendingVerificationItem) => {
    if (item.verification_status === 'PENDING_STAGE_1') {
      await approveStage1(item.file_id, notesInput || 'Stage 1 Quality and Content Approved');
    } else if (item.verification_status === 'PENDING_STAGE_2') {
      await approveStage2(item.file_id, notesInput || 'Stage 2 Regulatory & Compliance Sign-Off Confirmed');
    }
    setNotesInput('');
  };

  const handleOpenInCanvasAndReview = (item: PendingVerificationItem) => {
    // Open in interactive canvas editor so reviewer can modify/inspect live
    openCanvas(item.file_id);
    closeVerificationModal();
  };

  const handleConfirmReject = async () => {
    if (!rejectPromptItem || !rejectReason.trim()) return;
    await rejectItem(rejectPromptItem.file_id, rejectReason.trim());
    setRejectPromptItem(null);
    setRejectReason('');
  };

  const getDocIcon = (type: string) => {
    const t = (type || '').toLowerCase();
    if (['xlsx', 'xls', 'csv'].includes(t)) {
      return <FileSpreadsheet className="h-5 w-5 text-emerald-500" />;
    }
    if (['pptx', 'ppt'].includes(t)) {
      return <Presentation className="h-5 w-5 text-orange-500" />;
    }
    if (['py', 'ipynb'].includes(t)) {
      return <Code2 className="h-5 w-5 text-purple-500" />;
    }
    return <FileText className="h-5 w-5 text-blue-500" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/70 backdrop-blur-md transition-all">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 12 }}
        className="relative w-full max-w-5xl h-[88vh] max-h-[800px] flex flex-col rounded-2xl bg-white dark:bg-[#0c0e14] border border-slate-200 dark:border-[#1e2333] shadow-2xl overflow-hidden"
      >
        {/* =========================================================================
            1. TOP HEADER & VERIFICATION PIPELINE STATUS
            ========================================================================= */}
        <div className="px-5 py-4 bg-slate-50/80 dark:bg-[#10131d] border-b border-slate-200 dark:border-[#1a1f2e] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-500/10 dark:bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-[#a8c7fa] shadow-xs">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight">
                  2-Step Human Verification & Review Panel
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-[#a8c7fa] border border-blue-200 dark:border-blue-500/30">
                  Role: {userRole}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Multi-stage regulatory sign-off & technical peer approval for industrial documents
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchPendingVerifications()}
              disabled={isLoading}
              className="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-[#1e2333] text-slate-600 dark:text-slate-300 transition-colors cursor-pointer"
              title="Refresh Queue"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={closeVerificationModal}
              className="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-[#1e2333] text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors cursor-pointer"
              title="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. TWO-COLUMN WORKFLOW LAYOUT
            ========================================================================= */}
        <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
          {/* Left Column: Documents Awaiting Action List */}
          <div className="w-full md:w-[380px] border-r border-slate-200 dark:border-[#1a1f2e] flex flex-col bg-slate-50/50 dark:bg-[#0a0c12] shrink-0">
            {/* Filter Tabs */}
            <div className="p-3 border-b border-slate-200 dark:border-[#1a1f2e] flex items-center justify-between gap-1.5 overflow-x-auto text-xs">
              <button
                onClick={() => setSelectedFilter('ALL')}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                  selectedFilter === 'ALL'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-200 dark:text-slate-400 dark:hover:bg-[#151926]'
                }`}
              >
                All ({totalPending})
              </button>
              <button
                onClick={() => setSelectedFilter('PENDING_STAGE_1')}
                className={`px-2.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                  selectedFilter === 'PENDING_STAGE_1'
                    ? 'bg-amber-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-200 dark:text-slate-400 dark:hover:bg-[#151926]'
                }`}
              >
                <Clock className="h-3 w-3" />
                <span>Step 1 ({stage1Count})</span>
              </button>
              <button
                onClick={() => setSelectedFilter('PENDING_STAGE_2')}
                className={`px-2.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                  selectedFilter === 'PENDING_STAGE_2'
                    ? 'bg-purple-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-200 dark:text-slate-400 dark:hover:bg-[#151926]'
                }`}
              >
                <UserCheck className="h-3 w-3" />
                <span>Step 2 ({stage2Count})</span>
              </button>
            </div>

            {/* Document Queue List */}
            <div className="flex-1 overflow-y-auto p-2.5 space-y-1.5">
              {filteredItems.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-400 dark:text-slate-500">
                  <BadgeCheck className="h-8 w-8 mx-auto mb-2 opacity-40 text-emerald-500" />
                  No documents in this queue.
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
                          ? 'bg-white dark:bg-[#151926] border-blue-500 shadow-md ring-1 ring-blue-500/20'
                          : 'bg-white/60 dark:bg-[#0e111a] border-slate-200 dark:border-[#1a1f2e] hover:border-slate-300 dark:hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-[#1c2234] shrink-0">
                            {getDocIcon(item.file_type)}
                          </div>
                          <div className="min-w-0">
                            <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate" title={item.filename}>
                              {item.filename}
                            </h4>
                            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                              {item.created_at?.slice(0, 16)}
                            </div>
                          </div>
                        </div>

                        {/* Status Stage Pill */}
                        <span
                          className={`text-[9px] font-bold px-2 py-0.5 rounded-full shrink-0 uppercase tracking-wider ${
                            isStage1
                              ? 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/30'
                              : 'bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/30'
                          }`}
                        >
                          {isStage1 ? 'Step 1: L1 Review' : 'Step 2: Sign-Off'}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Column: Selected Document Inspection & Action Canvas */}
          <div className="flex-1 flex flex-col bg-white dark:bg-[#0c0e14] overflow-y-auto">
            {activeItem ? (
              <div className="p-6 flex-1 flex flex-col justify-between">
                <div>
                  {/* Item Header */}
                  <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-200 dark:border-[#1a1f2e]">
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-2xl bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-blue-600 dark:text-[#a8c7fa]">
                        {getDocIcon(activeItem.file_type)}
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                          {activeItem.filename}
                        </h3>
                        <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                          <span>Format: <strong className="uppercase">{activeItem.file_type}</strong></span>
                          <span>&bull;</span>
                          <span>File ID: <code className="font-mono text-[11px]">{activeItem.file_id}</code></span>
                          <span>&bull;</span>
                          <span>Session: {activeItem.chat_id}</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => downloadDeliverable(activeItem.file_id)}
                      className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-[#151926] hover:bg-slate-200 dark:hover:bg-[#1c2234] text-xs font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                    >
                      Download Copy ⤓
                    </button>
                  </div>

                  {/* 2-Step Verification Timeline Progress */}
                  <div className="my-6 p-4 rounded-2xl bg-slate-50 dark:bg-[#111420] border border-slate-200 dark:border-[#1e2333]">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
                      Verification Pipeline Status
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Step 1 Box */}
                      <div
                        className={`p-3.5 rounded-xl border ${
                          activeItem.stage_1_verifier
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
                            : activeItem.verification_status === 'PENDING_STAGE_1'
                            ? 'bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400'
                            : 'bg-slate-100 dark:bg-[#151926] border-slate-200 dark:border-slate-800 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold flex items-center gap-1.5">
                            {activeItem.stage_1_verifier ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <Clock className="h-4 w-4 text-amber-500" />
                            )}
                            Step 1: Process & Technical Review
                          </span>
                          <span className="text-[10px] font-mono font-semibold">
                            {activeItem.stage_1_verifier ? 'COMPLETED' : 'AWAITING'}
                          </span>
                        </div>
                        <p className="text-[11px] opacity-90">
                          {activeItem.stage_1_verifier
                            ? `Approved by @${activeItem.stage_1_verifier} on ${activeItem.stage_1_at?.slice(0, 16)}`
                            : 'Requires review by Process Lead or Maintenance Engineer'}
                        </p>
                        {activeItem.stage_1_notes && (
                          <div className="mt-2 text-[11px] italic bg-white/50 dark:bg-black/20 p-1.5 rounded-md">
                            &quot;{activeItem.stage_1_notes}&quot;
                          </div>
                        )}
                      </div>

                      {/* Step 2 Box */}
                      <div
                        className={`p-3.5 rounded-xl border ${
                          activeItem.stage_2_verifier
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
                            : activeItem.verification_status === 'PENDING_STAGE_2'
                            ? 'bg-purple-500/10 border-purple-500/30 text-purple-700 dark:text-purple-400'
                            : 'bg-slate-100 dark:bg-[#151926] border-slate-200 dark:border-slate-800 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold flex items-center gap-1.5">
                            {activeItem.stage_2_verifier ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <UserCheck className="h-4 w-4 text-purple-500" />
                            )}
                            Step 2: Executive Compliance Sign-Off
                          </span>
                          <span className="text-[10px] font-mono font-semibold">
                            {activeItem.stage_2_verifier ? 'VERIFIED' : 'PENDING'}
                          </span>
                        </div>
                        <p className="text-[11px] opacity-90">
                          {activeItem.stage_2_verifier
                            ? `Signed off by @${activeItem.stage_2_verifier} on ${activeItem.stage_2_at?.slice(0, 16)}`
                            : 'Unlocked after Step 1. Final approval by Refinery Compliance Chief'}
                        </p>
                        {activeItem.stage_2_notes && (
                          <div className="mt-2 text-[11px] italic bg-white/50 dark:bg-black/20 p-1.5 rounded-md">
                            &quot;{activeItem.stage_2_notes}&quot;
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Verification Notes Input */}
                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                      Approval / Reviewer Notes (Optional)
                    </label>
                    <input
                      type="text"
                      value={notesInput}
                      onChange={(e) => setNotesInput(e.target.value)}
                      placeholder="e.g. Verified operating pressures, temperatures, and compliance with SOP-04..."
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#121522] border border-slate-200 dark:border-[#1e2333] text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                {/* Bottom Action Triggers */}
                <div className="pt-6 border-t border-slate-200 dark:border-[#1a1f2e] flex flex-wrap items-center justify-between gap-3">
                  {/* Left: Make Edits & Proceed */}
                  <button
                    onClick={() => handleOpenInCanvasAndReview(activeItem)}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-50 hover:bg-blue-100 dark:bg-blue-500/10 dark:hover:bg-blue-500/20 text-blue-700 dark:text-[#a8c7fa] border border-blue-200 dark:border-blue-500/30 text-xs font-bold transition-all cursor-pointer"
                    title="Open live in canvas editor to edit document contents"
                  >
                    <Edit3 className="h-4 w-4" />
                    <span>Make Edits in Canvas Editor ↗</span>
                  </button>

                  {/* Right: Reject or Approve Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setRejectPromptItem(activeItem)}
                      className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-rose-500/10 dark:hover:bg-rose-500/20 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/30 text-xs font-bold transition-all cursor-pointer"
                    >
                      <XCircle className="h-4 w-4" />
                      <span>Reject Document</span>
                    </button>

                    <button
                      onClick={() => handleApprove(activeItem)}
                      disabled={isActing}
                      className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-98 text-white text-xs font-bold shadow-md shadow-emerald-500/20 transition-all cursor-pointer disabled:opacity-50"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      <span>
                        {activeItem.verification_status === 'PENDING_STAGE_1'
                          ? 'Approve Step 1 (Proceed to Step 2)'
                          : 'Final Sign-Off & Mark Verified'}
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 dark:text-slate-500">
                <ShieldCheck className="h-12 w-12 mb-3 text-blue-500/40" />
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Select a document from the queue
                </h4>
                <p className="text-xs max-w-sm mt-1">
                  Inspect content, perform peer-review, make necessary modifications in canvas, or proceed with authorization.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* =========================================================================
            3. REJECTION CONFIRMATION MODAL POPUP
            ========================================================================= */}
        <AnimatePresence>
          {rejectPromptItem && (
            <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="w-full max-w-md p-5 rounded-2xl bg-white dark:bg-[#121522] border border-rose-500/30 shadow-2xl"
              >
                <div className="flex items-center gap-3 text-rose-600 dark:text-rose-400 mb-3">
                  <AlertTriangle className="h-6 w-6" />
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Reject Deliverable Document
                  </h4>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 mb-4">
                  Please provide the technical or procedural reason for rejecting{' '}
                  <strong className="text-slate-900 dark:text-white">{rejectPromptItem.filename}</strong>.
                </p>

                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Specify why this document is rejected (e.g., Incomplete Hazard Analysis, Wrong Pressure Units)..."
                  rows={3}
                  className="w-full p-3 rounded-xl bg-slate-50 dark:bg-[#0c0e14] border border-slate-200 dark:border-[#1e2333] text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-rose-500 resize-none mb-4"
                />

                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => setRejectPromptItem(null)}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold hover:bg-slate-100 dark:hover:bg-[#1a1f2e] text-slate-600 dark:text-slate-300 cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmReject}
                    disabled={!rejectReason.trim()}
                    className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-md shadow-rose-600/20 cursor-pointer disabled:opacity-50"
                  >
                    Confirm Rejection
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
