'use client';

import React, { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  Lightbulb,
  MessageSquare,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  XCircle,
  RefreshCw,
  Loader2,
  Edit3,
  Trash2,
  Send,
  User,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Building2,
  Check,
  FileCode,
  Layers,
  Sparkles
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/useAuthStore';

export interface FeedbackReport {
  id: number;
  report_type: 'ERROR' | 'SUGGESTION';
  user_id?: string;
  username: string;
  chat_id?: string;
  message_id?: string;
  message_content?: string;
  category: string;
  title: string;
  description: string;
  suggested_fix?: string;
  status: 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'REJECTED';
  admin_notes?: string;
  admin_response?: string;
  resolved_by?: string;
  resolved_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface FeedbackStats {
  total: number;
  errors: number;
  suggestions: number;
  open: number;
  in_review: number;
  resolved: number;
}

export default function AdminFeedbackPage() {
  const { user } = useAuthStore();
  const [reports, setReports] = useState<FeedbackReport[]>([]);
  const [stats, setStats] = useState<FeedbackStats>({
    total: 0,
    errors: 0,
    suggestions: 0,
    open: 0,
    in_review: 0,
    resolved: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<FeedbackReport | null>(null);
  
  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Resolution Form State
  const [adminNotes, setAdminNotes] = useState('');
  const [adminResponse, setAdminResponse] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      let queryParams = new URLSearchParams();
      if (typeFilter !== 'ALL') queryParams.append('type', typeFilter);
      if (statusFilter !== 'ALL') queryParams.append('status', statusFilter);
      if (searchQuery.trim()) queryParams.append('search', searchQuery.trim());

      const data = await api.get<any>(`/api/feedback/list?${queryParams.toString()}`);
      if (data && data.reports) {
        setReports(data.reports);
        if (data.stats) setStats(data.stats);
        
        // Auto select first report if current selected is null or not in list
        if (!selectedReport && data.reports.length > 0) {
          setSelectedReport(data.reports[0]);
          setAdminNotes(data.reports[0].admin_notes || '');
          setAdminResponse(data.reports[0].admin_response || '');
        } else if (selectedReport) {
          const updated = data.reports.find((r: FeedbackReport) => r.id === selectedReport.id);
          if (updated) {
            setSelectedReport(updated);
            setAdminNotes(updated.admin_notes || '');
            setAdminResponse(updated.admin_response || '');
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch feedback reports:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [typeFilter, statusFilter]);

  const handleSelectReport = (r: FeedbackReport) => {
    setSelectedReport(r);
    setAdminNotes(r.admin_notes || '');
    setAdminResponse(r.admin_response || '');
    setActionSuccess(null);
    setActionError(null);
  };

  const handleUpdateStatus = async (newStatus: 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'REJECTED') => {
    if (!selectedReport) return;
    setIsUpdating(true);
    setActionSuccess(null);
    setActionError(null);

    try {
      const res = await api.patch<any>(`/api/feedback/${selectedReport.id}/status`, {
        status: newStatus,
        admin_notes: adminNotes.trim() || null,
        admin_response: adminResponse.trim() || null,
        resolved_by: user?.username || 'SuperAdmin'
      });

      if (res && res.status === 'SUCCESS') {
        setActionSuccess(`Report #${selectedReport.id} successfully updated to ${newStatus}`);
        fetchReports();
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to update report');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteReport = async (id: number) => {
    if (!confirm(`Are you sure you want to permanently delete report #${id}?`)) return;
    try {
      await api.delete<any>(`/api/feedback/${id}`);
      setSelectedReport(null);
      fetchReports();
    } catch (err: any) {
      alert(err.message || 'Failed to delete report');
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-[#000000] text-gray-900 dark:text-[#ededed] font-sans antialiased">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Module Header Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200 dark:border-[#262626]">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-purple-50 text-purple-600 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-400 dark:border-purple-800/40">
                <MessageSquare className="h-5 w-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight">Operator Feedback & Error Triage Hub</h1>
              <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/50 text-[10px] font-mono">
                XAMPP MySQL Live
              </Badge>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Directly review bug reports, mathematical/SOP inaccuracies, and operator improvement suggestions to tune the local AI system.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchReports}
              disabled={isLoading}
              className="text-xs h-9 gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Telemetry Stat Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] shadow-xs">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Total Reports</span>
            <div className="text-xl font-bold text-gray-900 dark:text-white mt-1">{stats.total}</div>
          </div>
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] shadow-xs">
            <span className="text-[10px] font-bold text-rose-500 uppercase tracking-wider">Errors Reported</span>
            <div className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-1">{stats.errors}</div>
          </div>
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] shadow-xs">
            <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider">Suggestions</span>
            <div className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">{stats.suggestions}</div>
          </div>
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] shadow-xs">
            <span className="text-[10px] font-bold text-blue-500 uppercase tracking-wider">Open / Pending</span>
            <div className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1">{stats.open}</div>
          </div>
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] shadow-xs">
            <span className="text-[10px] font-bold text-purple-500 uppercase tracking-wider">In Review</span>
            <div className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1">{stats.in_review}</div>
          </div>
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] shadow-xs">
            <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Resolved</span>
            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{stats.resolved}</div>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-xl bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626]">
          {/* Type Filters */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {['ALL', 'ERROR', 'SUGGESTION'].map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  typeFilter === t
                    ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-xs'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {t === 'ALL' ? 'All Types' : t === 'ERROR' ? '⚠️ Errors Only' : '💡 Suggestions Only'}
              </button>
            ))}
          </div>

          {/* Status Filters & Search */}
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg text-xs bg-gray-50 dark:bg-[#18181c] border border-gray-200 dark:border-[#333333] text-gray-800 dark:text-gray-200 outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="RESOLVED">Resolved</option>
              <option value="REJECTED">Rejected</option>
            </select>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                fetchReports();
              }}
              className="relative flex-1 sm:w-64"
            >
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
              <input
                type="text"
                placeholder="Search reports..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg text-xs bg-gray-50 dark:bg-[#18181c] border border-gray-200 dark:border-[#333333] text-gray-800 dark:text-gray-200 outline-none focus:ring-1 focus:ring-purple-500"
              />
            </form>
          </div>
        </div>

        {/* Main 2-Column Workstation */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Report Items Queue */}
          <div className="lg:col-span-5 space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase tracking-wider px-1">
              <span>Feedback Queue ({reports.length})</span>
            </div>

            {isLoading && reports.length === 0 ? (
              <div className="p-12 text-center bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] rounded-2xl">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400 mb-2" />
                <p className="text-xs text-gray-500">Loading feedback records from XAMPP MySQL...</p>
              </div>
            ) : reports.length === 0 ? (
              <div className="p-12 text-center bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] rounded-2xl space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
                <h4 className="text-sm font-bold text-gray-800 dark:text-gray-200">No Feedback Reports Found</h4>
                <p className="text-xs text-gray-500 max-w-sm mx-auto">
                  There are no reports matching your current filter criteria.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[720px] overflow-y-auto pr-1">
                {reports.map((r) => {
                  const isSelected = selectedReport?.id === r.id;
                  const isError = r.report_type === 'ERROR';

                  return (
                    <div
                      key={r.id}
                      onClick={() => handleSelectReport(r)}
                      className={`p-3.5 rounded-xl border transition-all cursor-pointer text-xs ${
                        isSelected
                          ? 'bg-blue-50/70 dark:bg-blue-950/20 border-blue-400 dark:border-blue-600 shadow-sm ring-1 ring-blue-400/50'
                          : 'bg-white dark:bg-[#111111] border-gray-200 dark:border-[#262626] hover:border-gray-300 dark:hover:border-[#444444]'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className={`p-1.5 rounded-lg border shrink-0 ${
                            isError
                              ? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/50'
                              : 'bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/50'
                          }`}>
                            {isError ? <AlertTriangle className="h-3.5 w-3.5" /> : <Lightbulb className="h-3.5 w-3.5" />}
                          </span>
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="font-bold text-gray-900 dark:text-white truncate">
                                #{r.id} {r.title}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-[10px] text-gray-400 mt-0.5 font-mono">
                              <span>@{r.username}</span>
                              <span>•</span>
                              <span>{r.category}</span>
                            </div>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase shrink-0 border ${
                          r.status === 'RESOLVED'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/40'
                            : r.status === 'IN_REVIEW'
                            ? 'bg-purple-50 text-purple-700 border-purple-300 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800/40'
                            : r.status === 'REJECTED'
                            ? 'bg-rose-50 text-rose-700 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/40'
                            : 'bg-blue-50 text-blue-700 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800/40'
                        }`}>
                          {r.status}
                        </span>
                      </div>

                      <p className="text-[11px] text-gray-600 dark:text-gray-300 line-clamp-2 mt-2 leading-relaxed">
                        {r.description}
                      </p>

                      <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-gray-100 dark:border-[#222222] text-[10px] text-gray-400 font-mono">
                        <span>{new Date(r.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</span>
                        <ChevronRight className="h-3 w-3 text-gray-400" />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Detailed Inspector & Resolution Action Pane */}
          <div className="lg:col-span-7">
            {selectedReport ? (
              <div className="bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] rounded-2xl p-5 space-y-5 shadow-xs">
                {/* Header of Inspector */}
                <div className="flex items-start justify-between gap-4 pb-4 border-b border-gray-200 dark:border-[#262626]">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase border ${
                        selectedReport.report_type === 'ERROR'
                          ? 'bg-rose-50 text-rose-700 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300'
                          : 'bg-amber-50 text-amber-700 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300'
                      }`}>
                        {selectedReport.report_type}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                        {selectedReport.category}
                      </span>
                      <span className="text-xs text-gray-400 font-mono">
                        Report #{selectedReport.id}
                      </span>
                    </div>
                    <h2 className="text-base font-bold text-gray-900 dark:text-white">
                      {selectedReport.title}
                    </h2>
                    <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 font-mono">
                      <span>Submitted by: <strong>@{selectedReport.username}</strong></span>
                      <span>•</span>
                      <span>{new Date(selectedReport.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteReport(selectedReport.id)}
                      className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 h-8 px-2 text-xs"
                      title="Delete Report"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>

                {/* Feedback Content Details */}
                <div className="space-y-4 text-xs">
                  {/* Operator's Description */}
                  <div className="space-y-1.5">
                    <h4 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                      Operator Description
                    </h4>
                    <div className="p-3 rounded-xl bg-gray-50 dark:bg-[#18181c] border border-gray-200 dark:border-[#2d2d34] text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                      {selectedReport.description}
                    </div>
                  </div>

                  {/* Operator's Proposed Fix if provided */}
                  {selectedReport.suggested_fix && (
                    <div className="space-y-1.5">
                      <h4 className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                        <Lightbulb className="h-3 w-3" />
                        Operator Proposed Correction / Solution
                      </h4>
                      <div className="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 text-emerald-900 dark:text-emerald-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                        {selectedReport.suggested_fix}
                      </div>
                    </div>
                  )}

                  {/* AI Response Snippet if tied to message */}
                  {selectedReport.message_content && (
                    <div className="space-y-1.5">
                      <h4 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                        Referenced Assistant Output
                      </h4>
                      <div className="p-3 rounded-xl bg-gray-100 dark:bg-[#151518] border border-gray-200 dark:border-[#282830] text-gray-700 dark:text-gray-300 font-mono text-[11px] max-h-40 overflow-y-auto whitespace-pre-wrap">
                        {selectedReport.message_content}
                      </div>
                    </div>
                  )}
                </div>

                {/* Admin Triage & Resolution Workbench */}
                <div className="pt-4 border-t border-gray-200 dark:border-[#262626] space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                      Admin Resolution & System Tuning
                    </h3>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-gray-400">Current Status:</span>
                      <span className="font-bold text-xs uppercase text-purple-600 dark:text-purple-400">
                        {selectedReport.status}
                      </span>
                    </div>
                  </div>

                  {/* Admin Internal Notes */}
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-gray-700 dark:text-gray-300">
                      Internal Admin Notes / Root Cause Analysis
                    </label>
                    <textarea
                      rows={2}
                      placeholder="e.g., Updated calculation formula in CDU prompt template, verified against MRPL standards..."
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-gray-50 dark:bg-[#18181c] border border-gray-200 dark:border-[#2d2d34] text-xs focus:ring-2 focus:ring-purple-500 outline-none text-gray-800 dark:text-gray-200"
                    />
                  </div>

                  {/* Action Success / Error Notifications */}
                  {actionSuccess && (
                    <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
                      <Check className="h-4 w-4 shrink-0" />
                      <span>{actionSuccess}</span>
                    </div>
                  )}
                  {actionError && (
                    <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span>{actionError}</span>
                    </div>
                  )}

                  {/* Status Action Buttons */}
                  <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleUpdateStatus('IN_REVIEW')}
                      disabled={isUpdating || selectedReport.status === 'IN_REVIEW'}
                      className="text-xs h-8 bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100 dark:bg-purple-950/30 dark:text-purple-300 dark:border-purple-800/40"
                    >
                      <Clock className="h-3.5 w-3.5 mr-1" />
                      Mark In Review
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleUpdateStatus('REJECTED')}
                      disabled={isUpdating || selectedReport.status === 'REJECTED'}
                      className="text-xs h-8 bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100 dark:bg-rose-950/30 dark:text-rose-300 dark:border-rose-800/40"
                    >
                      <XCircle className="h-3.5 w-3.5 mr-1" />
                      Reject Report
                    </Button>

                    <Button
                      type="button"
                      size="sm"
                      onClick={() => handleUpdateStatus('RESOLVED')}
                      disabled={isUpdating || selectedReport.status === 'RESOLVED'}
                      className="text-xs h-8 bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-xs"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      Resolve & Save Fix
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-16 text-center bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#262626] rounded-2xl space-y-2">
                <MessageSquare className="h-10 w-10 text-gray-300 dark:text-gray-700 mx-auto" />
                <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200">No Report Selected</h3>
                <p className="text-xs text-gray-500 max-w-sm mx-auto">
                  Select a report from the queue on the left to inspect full details, review proposed fixes, and apply resolutions.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
