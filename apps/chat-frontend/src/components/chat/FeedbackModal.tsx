'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  Lightbulb,
  X,
  Send,
  Loader2,
  CheckCircle2,
  HelpCircle,
  FileCode,
  Layers,
  Sparkles
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialType?: 'ERROR' | 'SUGGESTION';
  messageId?: string;
  chatId?: string;
  messageContent?: string;
}

export const CATEGORIES = [
  { id: 'GENERAL', label: 'General / Interface' },
  { id: 'CALCULATIONS', label: 'Calculations & Formula' },
  { id: 'SOP_COMPLIANCE', label: 'SOP & Safety Accuracy' },
  { id: 'DELIVERABLE', label: 'Document / Export Quality' },
  { id: 'HALLUCINATION', label: 'Fact Inaccuracy / Hallucination' },
  { id: 'FEATURE_REQUEST', label: 'Feature or Tool Request' },
];

export function FeedbackModal({
  isOpen,
  onClose,
  initialType = 'ERROR',
  messageId,
  chatId,
  messageContent,
}: FeedbackModalProps) {
  const { user, token } = useAuthStore();
  const [reportType, setReportType] = useState<'ERROR' | 'SUGGESTION'>(initialType);
  const [category, setCategory] = useState<string>('GENERAL');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [suggestedFix, setSuggestedFix] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync initial type when opened
  React.useEffect(() => {
    if (isOpen) {
      setReportType(initialType);
      setIsSuccess(false);
      setErrorMsg(null);
      if (!title) {
        setTitle(initialType === 'ERROR' ? 'Inaccuracy in AI Response' : 'Suggested Improvement');
      }
    }
  }, [isOpen, initialType]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setErrorMsg('Please fill in both the title and details.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          report_type: reportType,
          title: title.trim(),
          description: description.trim(),
          category,
          suggested_fix: suggestedFix.trim() || null,
          chat_id: chatId || null,
          message_id: messageId || null,
          message_content: messageContent ? messageContent.slice(0, 1500) : null,
          username: user?.username || 'operator',
          user_id: user?.id ? String(user.id) : null,
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to submit report');
      }

      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        setTitle('');
        setDescription('');
        setSuggestedFix('');
        onClose();
      }, 1400);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error communicating with server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm select-none">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ duration: 0.18 }}
        className="w-full max-w-lg bg-white dark:bg-[#121214] border border-slate-200 dark:border-[#282a2c] rounded-2xl shadow-2xl overflow-hidden text-slate-900 dark:text-[#ededed]"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-[#222226] bg-slate-50/70 dark:bg-[#18181c]/50">
          <div className="flex items-center gap-2.5">
            <div className={`p-2 rounded-xl border ${
              reportType === 'ERROR'
                ? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/50'
                : 'bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/50'
            }`}>
              {reportType === 'ERROR' ? <AlertTriangle className="h-4 w-4" /> : <Lightbulb className="h-4 w-4" />}
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight">
                {reportType === 'ERROR' ? 'Report AI Error to Admin' : 'Submit Improvement Suggestion'}
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Directly reviewed by Super Admin & Process Leads in the Admin Panel
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/[0.06] transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Success Splash */}
        {isSuccess ? (
          <div className="p-8 flex flex-col items-center justify-center text-center space-y-3">
            <div className="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h4 className="text-base font-bold text-slate-900 dark:text-white">Report Logged Successfully</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Your feedback has been saved to the XAMPP database and queued for Admin review.
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
            {/* Type Selector Tabs */}
            <div className="flex gap-2 p-1 rounded-xl bg-slate-100 dark:bg-[#1a1a1e] border border-slate-200 dark:border-[#2b2b32]">
              <button
                type="button"
                onClick={() => setReportType('ERROR')}
                className={`flex-1 py-1.5 px-3 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all ${
                  reportType === 'ERROR'
                    ? 'bg-rose-600 text-white shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                Report Error / Inaccuracy
              </button>
              <button
                type="button"
                onClick={() => setReportType('SUGGESTION')}
                className={`flex-1 py-1.5 px-3 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all ${
                  reportType === 'SUGGESTION'
                    ? 'bg-amber-500 text-slate-950 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Lightbulb className="h-3.5 w-3.5" />
                Feature / Content Suggestion
              </button>
            </div>

            {/* Referenced Message Context Preview if any */}
            {messageContent && (
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#18181c] border border-slate-200/80 dark:border-[#282a2e] space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                  Target AI Response Snippet:
                </span>
                <p className="text-[11px] text-slate-600 dark:text-slate-300 line-clamp-2 italic font-mono bg-white dark:bg-[#101012] p-1.5 rounded border border-slate-200/50 dark:border-[#222226]">
                  "{messageContent}"
                </p>
              </div>
            )}

            {/* Category Dropdown & Title */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-1 space-y-1">
                <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-2.5 py-2 rounded-xl bg-slate-50 dark:bg-[#18181c] border border-slate-200 dark:border-[#2d2d34] text-xs focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-200"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300">
                  Subject / Short Title
                </label>
                <input
                  type="text"
                  required
                  placeholder={reportType === 'ERROR' ? "e.g., Wrong temperature unit in CDU output" : "e.g., Add direct PDF generation button"}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#18181c] border border-slate-200 dark:border-[#2d2d34] text-xs focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-200"
                />
              </div>
            </div>

            {/* Description */}
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300">
                Detailed Description <span className="text-rose-500">*</span>
              </label>
              <textarea
                required
                rows={3}
                placeholder={
                  reportType === 'ERROR'
                    ? "Explain what is incorrect or what went wrong in the response..."
                    : "Describe your suggestion or how this response/feature could be improved..."
                }
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#18181c] border border-slate-200 dark:border-[#2d2d34] text-xs focus:ring-2 focus:ring-blue-500 outline-none resize-none text-slate-800 dark:text-slate-200"
              />
            </div>

            {/* Suggested Fix (Optional) */}
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                <span>Proposed Correction / Fix (Optional)</span>
                <span className="text-[10px] text-slate-400">Helps admin correct it faster</span>
              </label>
              <textarea
                rows={2}
                placeholder="What should the correct response or behavior have been?"
                value={suggestedFix}
                onChange={(e) => setSuggestedFix(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#18181c] border border-slate-200 dark:border-[#2d2d34] text-xs focus:ring-2 focus:ring-blue-500 outline-none resize-none text-slate-800 dark:text-slate-200"
              />
            </div>

            {errorMsg && (
              <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 text-rose-600 dark:text-rose-400 text-[11px]">
                {errorMsg}
              </div>
            )}

            {/* Actions */}
            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.06] transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className={`px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 text-white shadow-md transition-all ${
                  reportType === 'ERROR'
                    ? 'bg-rose-600 hover:bg-rose-700 active:bg-rose-800'
                    : 'bg-amber-600 hover:bg-amber-700 active:bg-amber-800'
                }`}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Sending to Admin...
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    Submit to Admin
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  );
}
