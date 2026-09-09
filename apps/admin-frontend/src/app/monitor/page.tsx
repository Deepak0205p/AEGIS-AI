'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert,
  Search,
  RefreshCw,
  UserX,
  UserCheck,
  AlertTriangle,
  FileText,
  MessageSquare,
  Upload,
  Lock,
  CheckCircle2,
  Filter,
  Eye,
  Activity,
  Terminal,
  Clock,
  Radio,
  Download
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export interface ActivityLog {
  id: number;
  username: string;
  role: string;
  activity_type: 'CHAT_QUERY' | 'SEARCH_RAG' | 'FILE_UPLOAD' | 'FILE_DOWNLOAD' | 'CHANNEL_MSG' | 'LOGIN' | 'SECURITY_TRIGGER';
  channel_or_chat_id?: string;
  query_text?: string;
  details?: string;
  file_meta?: any;
  ip_address?: string;
  risk_level: 'NORMAL' | 'SUSPICIOUS' | 'CRITICAL';
  created_at: string;
}

export default function SecurityMonitorPage() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [selectedUserToBlock, setSelectedUserToBlock] = useState<string | null>(null);
  const [blockReason, setBlockReason] = useState('Suspicious query detected during Sovereign Audit');
  const [isProcessingBlock, setIsProcessingBlock] = useState(false);
  const [toastMsg, setToastMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<any>('/api/v1/audit/activity-logs?limit=200');
      if (data && Array.isArray(data.logs)) {
        setLogs(data.logs);
      }
    } catch (e: any) {
      console.error('Failed to load audit logs:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleBlockUser = async (username: string, action: 'BLOCK' | 'UNBLOCK' = 'BLOCK') => {
    setIsProcessingBlock(true);
    try {
      await api.post('/api/v1/audit/block-user', {
        username,
        action,
        reason: blockReason,
      });
      setToastMsg({
        type: 'success',
        text: `User '${username}' has been successfully ${action === 'BLOCK' ? 'BLOCKED & FROZEN' : 'UNBLOCKED'}.`,
      });
      setSelectedUserToBlock(null);
      fetchLogs();
    } catch (err: any) {
      setToastMsg({
        type: 'error',
        text: err.message || 'Failed to update user security status',
      });
    } finally {
      setIsProcessingBlock(false);
    }
  };

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesSearch =
        !searchQuery.trim() ||
        log.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (log.query_text && log.query_text.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (log.details && log.details.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesRisk = riskFilter === 'ALL' || log.risk_level === riskFilter;
      const matchesType = typeFilter === 'ALL' || log.activity_type === typeFilter;

      return matchesSearch && matchesRisk && matchesType;
    });
  }, [logs, searchQuery, riskFilter, typeFilter]);

  const suspiciousCount = useMemo(
    () => logs.filter((l) => l.risk_level === 'SUSPICIOUS' || l.risk_level === 'CRITICAL').length,
    [logs]
  );

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'CHAT_QUERY':
        return <MessageSquare className="w-3.5 h-3.5 text-blue-500" />;
      case 'SEARCH_RAG':
        return <Search className="w-3.5 h-3.5 text-indigo-500" />;
      case 'FILE_UPLOAD':
        return <Upload className="w-3.5 h-3.5 text-emerald-500" />;
      case 'SECURITY_TRIGGER':
        return <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400 border border-rose-300 dark:border-rose-800 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
            CRITICAL
          </span>
        );
      case 'SUSPICIOUS':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400 border border-amber-300 dark:border-amber-800 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            SUSPICIOUS
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-[#1e1f20] dark:text-slate-400">
            NORMAL
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-900 dark:bg-[#000000] dark:text-white font-sans">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {/* Toast Feedback */}
        <AnimatePresence>
          {toastMsg && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`p-3.5 rounded-xl border text-xs font-mono flex items-center justify-between shadow-sm ${
                toastMsg.type === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : 'bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-300'
              }`}
            >
              <div className="flex items-center gap-2">
                {toastMsg.type === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600" />
                )}
                <span>{toastMsg.text}</span>
              </div>
              <button onClick={() => setToastMsg(null)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Top Header Card */}
        <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500/20 to-amber-500/20 border border-rose-500/30 flex items-center justify-center text-rose-600 dark:text-rose-400 shadow-xs">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-gray-900 dark:text-white">
                  User Search &amp; Chat Monitoring Sentinel
                </h1>
                {suspiciousCount > 0 && (
                  <Badge variant="destructive" className="text-[10px] font-mono animate-pulse">
                    {suspiciousCount} Suspicious Events
                  </Badge>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5">
                Live audit ledger tracking all operator search queries, chats, files, and emergency block controls.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 font-mono">
            <Button
              size="sm"
              variant="outline"
              onClick={fetchLogs}
              disabled={isLoading}
              className="h-8.5 text-xs border-gray-200 dark:border-gray-700"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
              Auto-Syncing
            </Button>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-gray-400 uppercase">Total Activity Events</span>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{logs.length}</p>
            </div>
            <Activity className="w-6 h-6 text-blue-500/40" />
          </div>

          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-emerald-500 uppercase">Normal Activity</span>
              <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                {logs.filter((l) => l.risk_level === 'NORMAL').length}
              </p>
            </div>
            <CheckCircle2 className="w-6 h-6 text-emerald-500/40" />
          </div>

          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-amber-500 uppercase">Suspicious Flagged</span>
              <p className="text-lg font-bold text-amber-600 dark:text-amber-400">
                {logs.filter((l) => l.risk_level === 'SUSPICIOUS').length}
              </p>
            </div>
            <AlertTriangle className="w-6 h-6 text-amber-500/40" />
          </div>

          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-rose-500 uppercase">Critical Interventions</span>
              <p className="text-lg font-bold text-rose-600 dark:text-rose-400">
                {logs.filter((l) => l.risk_level === 'CRITICAL').length}
              </p>
            </div>
            <Lock className="w-6 h-6 text-rose-500/40" />
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search user query text, username, details, or prompts..."
              className="w-full pl-9 pr-4 py-2 text-xs bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="px-3 py-2 text-xs bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl text-gray-900 dark:text-white font-mono"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="NORMAL">Normal Only</option>
              <option value="SUSPICIOUS">Suspicious Only</option>
              <option value="CRITICAL">Critical Only</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2 text-xs bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl text-gray-900 dark:text-white font-mono"
            >
              <option value="ALL">All Event Types</option>
              <option value="CHAT_QUERY">Chat Queries</option>
              <option value="SEARCH_RAG">SOP / RAG Searches</option>
              <option value="FILE_UPLOAD">File Uploads</option>
              <option value="SECURITY_TRIGGER">Security Interventions</option>
            </select>
          </div>
        </div>

        {/* Activity Logs Table */}
        <Card className="border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] shadow-sm overflow-hidden">
          <CardHeader className="pb-3 border-b border-gray-200 dark:border-[#262c3a] flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-mono uppercase tracking-wider text-gray-600 dark:text-gray-400 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-blue-500" />
              <span>Real-Time Audit Stream ({filteredLogs.length} entries)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-gray-50 dark:bg-[#181a20] text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-[#262c3a]">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Timestamp</th>
                    <th className="py-2.5 px-4 font-semibold">Operator</th>
                    <th className="py-2.5 px-4 font-semibold">Event Type</th>
                    <th className="py-2.5 px-4 font-semibold">Query / Prompt Content</th>
                    <th className="py-2.5 px-4 font-semibold">Risk Level</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-[#262c3a]">
                  {filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-400">
                        No activity records found matching filters.
                      </td>
                    </tr>
                  ) : (
                    filteredLogs.map((log) => (
                      <tr
                        key={log.id}
                        className={`hover:bg-gray-50/50 dark:hover:bg-[#181b22] transition-colors ${
                          log.risk_level === 'SUSPICIOUS' ? 'bg-amber-500/5' : log.risk_level === 'CRITICAL' ? 'bg-rose-500/10' : ''
                        }`}
                      >
                        <td className="py-3 px-4 text-gray-400 whitespace-nowrap text-[11px]">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : 'Now'}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            <span className="font-bold text-gray-900 dark:text-gray-200">
                              {log.username}
                            </span>
                            <span className="text-[10px] text-gray-500">({log.role})</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            {getActivityIcon(log.activity_type)}
                            <span>{log.activity_type}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 max-w-md">
                          <p className="truncate font-medium text-gray-900 dark:text-gray-100">
                            {log.query_text || log.details || '—'}
                          </p>
                          {log.details && log.query_text && (
                            <p className="text-[10px] text-gray-400 truncate mt-0.5">{log.details}</p>
                          )}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">{getRiskBadge(log.risk_level)}</td>
                        <td className="py-3 px-4 text-right whitespace-nowrap">
                          {log.username !== 'admin' && (
                            <button
                              onClick={() => setSelectedUserToBlock(log.username)}
                              className="px-2.5 py-1 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 dark:bg-rose-950/60 dark:text-rose-300 dark:hover:bg-rose-900/60 border border-rose-300 dark:border-rose-800 transition-colors"
                            >
                              <UserX className="w-3 h-3 inline mr-1" />
                              Block User
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Modal: Confirm Block User */}
      <AnimatePresence>
        {selectedUserToBlock && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-mono">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-white dark:bg-[#11141c] rounded-2xl border border-gray-200 dark:border-[#262c3a] p-6 shadow-2xl"
            >
              <div className="flex items-center gap-3 pb-3 border-b border-gray-200 dark:border-[#262c3a]">
                <div className="w-9 h-9 rounded-xl bg-rose-500/20 text-rose-600 flex items-center justify-center">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                    Emergency User Freeze / Block
                  </h3>
                  <p className="text-xs text-gray-400">Suspend operator account access immediately</p>
                </div>
              </div>

              <div className="space-y-4 my-4">
                <div className="p-3 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 rounded-xl text-xs text-rose-800 dark:text-rose-300">
                  Are you sure you want to block <strong className="font-bold">@{selectedUserToBlock}</strong>? The user will immediately be barred from logging in, chatting with AEGIS, and accessing SOPs.
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Reason for Suspension
                  </label>
                  <input
                    type="text"
                    value={blockReason}
                    onChange={(e) => setBlockReason(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-gray-50 dark:bg-[#181a20] border border-gray-200 dark:border-[#333] rounded-xl text-gray-900 dark:text-white focus:outline-none focus:border-rose-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setSelectedUserToBlock(null)}
                  className="px-4 py-2 rounded-xl text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleBlockUser(selectedUserToBlock, 'BLOCK')}
                  disabled={isProcessingBlock}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-md transition-all"
                >
                  {isProcessingBlock ? 'Freezing...' : 'Confirm Freeze & Block'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
