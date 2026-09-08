'use client';

import React, { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Shield,
  User,
  Trash2,
  Loader2,
  RefreshCw,
  Plus,
  Edit2,
  Snowflake,
  Play,
  KeyRound,
  Building2,
  CheckCircle2,
  AlertTriangle,
  Search,
  Lock,
  UserCheck,
  UserX,
  Sparkles,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export interface OperatorUser {
  id: number;
  username: string;
  role: string;
  full_name: string;
  department: string;
  status: 'ACTIVE' | 'FROZEN';
  created_at?: string;
}

const ROLES = [
  { id: 'SUPER_ADMIN', label: 'Super Admin (Full Sovereign Control)', color: 'border-red-300 text-red-700 bg-red-50 dark:bg-red-950/40 dark:text-red-300' },
  { id: 'PROCESS_LEAD', label: 'Process Lead (CDU / Flare Operations)', color: 'border-cyan-300 text-cyan-700 bg-cyan-50 dark:bg-cyan-950/40 dark:text-cyan-300' },
  { id: 'MAINTENANCE_ENG', label: 'Maintenance Engineer (Reliability & SOP)', color: 'border-emerald-300 text-emerald-700 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-300' },
  { id: 'FIELD_OPERATOR', label: 'Field Operator (Execution & Shift Log)', color: 'border-blue-300 text-blue-700 bg-blue-50 dark:bg-blue-950/40 dark:text-blue-300' },
  { id: 'AUDITOR_VIEWER', label: 'Auditor Viewer (Read-only Air-Gap Inspect)', color: 'border-gray-300 text-gray-700 bg-gray-50 dark:bg-gray-800 dark:text-gray-300' },
];

export default function UsersPage() {
  const [users, setUsers] = useState<OperatorUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');

  // Modal / Form States
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<OperatorUser | null>(null);

  // Form Fields
  const [formUsername, setFormUsername] = useState('');
  const [formPassword, setFormPassword] = useState('');
  const [formFullName, setFormFullName] = useState('');
  const [formRole, setFormRole] = useState('FIELD_OPERATOR');
  const [formDepartment, setFormDepartment] = useState('Refinery Operations');
  const [formStatus, setFormStatus] = useState<'ACTIVE' | 'FROZEN'>('ACTIVE');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<any>('/api/v1/auth/users');
      if (data && Array.isArray(data.users)) {
        setUsers(data.users);
      } else if (Array.isArray(data)) {
        setUsers(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load user registry');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const triggerToast = (text: string, type: 'success' | 'error' = 'success') => {
    setFeedbackMsg({ type, text });
    setTimeout(() => setFeedbackMsg(null), 4000);
  };

  // Open Create Modal
  const openCreateModal = () => {
    setFormUsername('');
    setFormPassword('');
    setFormFullName('');
    setFormRole('FIELD_OPERATOR');
    setFormDepartment('Refinery Operations');
    setShowCreateModal(true);
  };

  // Open Edit Modal
  const openEditModal = (u: OperatorUser) => {
    setSelectedUser(u);
    setFormUsername(u.username);
    setFormPassword(''); // blank unless changing
    setFormFullName(u.full_name);
    setFormRole(u.role);
    setFormDepartment(u.department);
    setFormStatus(u.status || 'ACTIVE');
    setShowEditModal(true);
  };

  // Open Delete Modal
  const openDeleteModal = (u: OperatorUser) => {
    setSelectedUser(u);
    setShowDeleteModal(true);
  };

  // Handle Create User
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formUsername.trim() || !formPassword.trim()) return;

    setIsSubmitting(true);
    try {
      await api.post('/api/v1/auth/users', {
        username: formUsername.trim(),
        password: formPassword.trim(),
        full_name: formFullName.trim() || formUsername.trim(),
        role: formRole,
        department: formDepartment.trim() || 'Operations',
      });
      triggerToast(`Account '${formUsername}' successfully provisioned with ${formRole} privileges.`);
      setShowCreateModal(false);
      fetchUsers();
    } catch (err: any) {
      triggerToast(err.message || 'Failed to create user', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Update User
  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      const payload: any = {
        full_name: formFullName.trim(),
        role: formRole,
        department: formDepartment.trim(),
        status: formStatus,
      };
      if (formPassword.trim()) {
        payload.password = formPassword.trim();
      }

      await api.put(`/api/v1/auth/users/${selectedUser.username}`, payload);
      triggerToast(`User '${selectedUser.username}' updated successfully.`);
      setShowEditModal(false);
      fetchUsers();
    } catch (err: any) {
      triggerToast(err.message || 'Failed to update user', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Toggle Freeze Status
  const handleToggleFreeze = async (u: OperatorUser) => {
    const nextStatus = u.status === 'FROZEN' ? 'ACTIVE' : 'FROZEN';
    try {
      await api.post(`/api/v1/auth/users/${u.username}/freeze`, { status: nextStatus });
      triggerToast(`User '${u.username}' is now ${nextStatus}.`);
      fetchUsers();
    } catch (err: any) {
      triggerToast(err.message || 'Failed to toggle freeze state', 'error');
    }
  };

  // Handle Delete User
  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    setIsSubmitting(true);
    try {
      await api.delete(`/api/v1/auth/users/${selectedUser.username}`);
      triggerToast(`Account '${selectedUser.username}' purged from registry.`);
      setShowDeleteModal(false);
      fetchUsers();
    } catch (err: any) {
      triggerToast(err.message || 'Failed to delete user', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filtered Users List
  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      !searchQuery.trim() ||
      u.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.department.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-900 font-sans">
      <Header />
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {/* Toast / Alert Feedback */}
        <AnimatePresence>
          {feedbackMsg && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`p-3.5 rounded-xl border text-xs font-mono flex items-center justify-between shadow-sm ${
                feedbackMsg.type === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : 'bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-300'
              }`}
            >
              <div className="flex items-center gap-2">
                {feedbackMsg.type === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                )}
                <span>{feedbackMsg.text}</span>
              </div>
              <button onClick={() => setFeedbackMsg(null)} className="text-gray-400 hover:text-gray-600 cursor-pointer">
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Page Top Header with Quick Actions */}
        <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-xs">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-gray-900 dark:text-white">
                  Operator Accounts &amp; RBAC Registry
                </h1>
                <Badge variant="active" className="text-[10px] font-mono">
                  {users.length} Active Accounts
                </Badge>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5">
                Provision new operators, assign granular RBAC roles, freeze access, or edit credentials.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 font-mono">
            <Button
              size="sm"
              variant="outline"
              onClick={fetchUsers}
              disabled={isLoading}
              className="h-8.5 text-xs border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>

            <Button
              size="sm"
              onClick={openCreateModal}
              className="h-8.5 text-xs bg-blue-600 hover:bg-blue-500 active:scale-[0.98] text-white font-semibold shadow-xs flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Provision New Operator</span>
            </Button>
          </div>
        </div>

        {/* Search, Stats & Filter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          {/* Quick Stat: Total Accounts */}
          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-gray-400 uppercase">Total Operators</span>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{users.length}</p>
            </div>
            <Users className="w-6 h-6 text-blue-500/40" />
          </div>

          {/* Quick Stat: Active */}
          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-emerald-500 uppercase">Active Status</span>
              <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                {users.filter(u => u.status !== 'FROZEN').length}
              </p>
            </div>
            <UserCheck className="w-6 h-6 text-emerald-500/40" />
          </div>

          {/* Quick Stat: Suspended/Frozen */}
          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-amber-500 uppercase">Frozen / Suspended</span>
              <p className="text-lg font-bold text-amber-600 dark:text-amber-400">
                {users.filter(u => u.status === 'FROZEN').length}
              </p>
            </div>
            <Snowflake className="w-6 h-6 text-amber-500/40" />
          </div>

          {/* Quick Stat: Super Admins */}
          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] flex items-center justify-between font-mono">
            <div>
              <span className="text-[10px] text-rose-500 uppercase">Super Admins</span>
              <p className="text-lg font-bold text-rose-600 dark:text-rose-400">
                {users.filter(u => u.role === 'SUPER_ADMIN' || u.role === 'admin').length}
              </p>
            </div>
            <Shield className="w-6 h-6 text-rose-500/40" />
          </div>
        </div>

        {/* Filter Controls & Search */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 font-mono text-xs">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by username, full name, or department..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8.5 pr-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Role Filter Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-gray-500 text-[11px] whitespace-nowrap">Filter Role:</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Roles ({users.length})</option>
              <option value="SUPER_ADMIN">Super Admins</option>
              <option value="PROCESS_LEAD">Process Leads</option>
              <option value="MAINTENANCE_ENG">Maintenance Engineers</option>
              <option value="FIELD_OPERATOR">Field Operators</option>
              <option value="AUDITOR_VIEWER">Auditor Viewers</option>
            </select>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl overflow-hidden shadow-sm font-sans">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-7 h-7 animate-spin text-blue-500" />
            </div>
          ) : error ? (
            <div className="p-6 text-center text-rose-600 font-mono text-xs">{error}</div>
          ) : filteredUsers.length === 0 ? (
            <div className="py-12 text-center text-gray-400 font-mono text-xs">
              No matching operator accounts found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-gray-50 dark:bg-[#0c0e14] border-b border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 text-[10px] uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Operator / Username</th>
                    <th className="py-3 px-4 font-semibold">RBAC Role</th>
                    <th className="py-3 px-4 font-semibold">Department &amp; Scope</th>
                    <th className="py-3 px-4 font-semibold">Account State</th>
                    <th className="py-3 px-4 text-right font-semibold">Management Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800/70 text-xs">
                  {filteredUsers.map((u) => {
                    const isFrozen = u.status === 'FROZEN';
                    const roleConfig = ROLES.find(r => r.id === u.role) || {
                      label: u.role,
                      color: 'border-gray-200 text-gray-700 bg-gray-50',
                    };

                    return (
                      <tr
                        key={u.username}
                        className={`hover:bg-gray-50/80 dark:hover:bg-[#151924] transition-colors ${
                          isFrozen ? 'opacity-65 bg-gray-50/50 dark:bg-gray-950/20' : ''
                        }`}
                      >
                        {/* User Identity */}
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                              isFrozen
                                ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                                : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                            }`}>
                              {u.full_name?.charAt(0) || u.username.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-gray-900 dark:text-white flex items-center gap-1.5 font-sans">
                                <span>{u.full_name || u.username}</span>
                                {isFrozen && (
                                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                                    FROZEN
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-gray-400 font-mono">@{u.username}</div>
                            </div>
                          </div>
                        </td>

                        {/* RBAC Role */}
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-semibold border ${roleConfig.color}`}
                          >
                            <Shield className="w-3 h-3 shrink-0" />
                            <span>{u.role}</span>
                          </span>
                        </td>

                        {/* Department */}
                        <td className="py-3 px-4 text-gray-700 dark:text-gray-300 text-[11px]">
                          <div className="flex items-center gap-1.5">
                            <Building2 className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                            <span>{u.department || 'Refinery Operations'}</span>
                          </div>
                        </td>

                        {/* State Pill */}
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${
                              isFrozen
                                ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800'
                                : 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isFrozen ? 'bg-amber-500' : 'bg-emerald-500 animate-pulse'
                              }`}
                            />
                            <span>{isFrozen ? 'SUSPENDED' : 'AUTHORIZED'}</span>
                          </span>
                        </td>

                        {/* Actions Toolbar */}
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* Freeze/Unfreeze Toggle Button */}
                            <button
                              onClick={() => handleToggleFreeze(u)}
                              disabled={u.username === 'admin'}
                              title={isFrozen ? 'Unfreeze / Restore Access' : 'Freeze / Suspend Account'}
                              className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
                                isFrozen
                                  ? 'bg-emerald-50 dark:bg-emerald-950/50 border-emerald-300 dark:border-emerald-800 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-100'
                                  : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-500 hover:text-amber-600 hover:bg-amber-50'
                              } disabled:opacity-40 disabled:cursor-not-allowed`}
                            >
                              {isFrozen ? <Play className="w-3.5 h-3.5" /> : <Snowflake className="w-3.5 h-3.5" />}
                            </button>

                            {/* Edit Button */}
                            <button
                              onClick={() => openEditModal(u)}
                              title="Edit Role, Department or Reset Password"
                              className="p-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:text-blue-600 hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>

                            {/* Delete Button */}
                            {u.username !== 'admin' && (
                              <button
                                onClick={() => openDeleteModal(u)}
                                title="Delete Operator Account"
                                className="p-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-400 hover:text-rose-600 hover:border-rose-300 dark:hover:border-rose-800 transition-colors cursor-pointer"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* CREATE OPERATOR MODAL */}
      <AnimatePresence>
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl p-6 space-y-4 font-sans text-xs"
            >
              <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
                <div className="flex items-center gap-2 text-blue-600 font-semibold text-sm">
                  <Plus className="w-4 h-4" />
                  <span>Provision New Operator Account</span>
                </div>
                <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600 cursor-pointer">
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateUser} className="space-y-3 font-mono">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Username (Login ID):</label>
                    <input
                      type="text"
                      placeholder="e.g. shift_lead_02"
                      value={formUsername}
                      onChange={(e) => setFormUsername(e.target.value)}
                      required
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Full Operator Name:</label>
                    <input
                      type="text"
                      placeholder="e.g. Rajesh Sharma"
                      value={formFullName}
                      onChange={(e) => setFormFullName(e.target.value)}
                      required
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] text-gray-500">Initial Password:</label>
                  <input
                    type="password"
                    placeholder="Enter secure master password"
                    value={formPassword}
                    onChange={(e) => setFormPassword(e.target.value)}
                    required
                    className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Assign RBAC Role:</label>
                    <select
                      value={formRole}
                      onChange={(e) => setFormRole(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    >
                      <option value="FIELD_OPERATOR">FIELD_OPERATOR</option>
                      <option value="MAINTENANCE_ENG">MAINTENANCE_ENG</option>
                      <option value="PROCESS_LEAD">PROCESS_LEAD</option>
                      <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                      <option value="AUDITOR_VIEWER">AUDITOR_VIEWER</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Department / Unit:</label>
                    <input
                      type="text"
                      placeholder="e.g. Flare & Utility Section"
                      value={formDepartment}
                      onChange={(e) => setFormDepartment(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowCreateModal(false)}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting || !formUsername.trim() || !formPassword.trim()}
                    className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold"
                  >
                    {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Plus className="w-3.5 h-3.5 mr-1" />}
                    Provision Account
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* EDIT OPERATOR MODAL */}
      <AnimatePresence>
        {showEditModal && selectedUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl p-6 space-y-4 font-sans text-xs"
            >
              <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
                <div className="flex items-center gap-2 text-blue-600 font-semibold text-sm">
                  <Edit2 className="w-4 h-4" />
                  <span>Modify Account: @{selectedUser.username}</span>
                </div>
                <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-gray-600 cursor-pointer">
                  ✕
                </button>
              </div>

              <form onSubmit={handleUpdateUser} className="space-y-3 font-mono">
                <div className="space-y-1">
                  <label className="text-[11px] text-gray-500">Full Operator Name:</label>
                  <input
                    type="text"
                    value={formFullName}
                    onChange={(e) => setFormFullName(e.target.value)}
                    required
                    className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Assign RBAC Role:</label>
                    <select
                      value={formRole}
                      onChange={(e) => setFormRole(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    >
                      <option value="FIELD_OPERATOR">FIELD_OPERATOR</option>
                      <option value="MAINTENANCE_ENG">MAINTENANCE_ENG</option>
                      <option value="PROCESS_LEAD">PROCESS_LEAD</option>
                      <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                      <option value="AUDITOR_VIEWER">AUDITOR_VIEWER</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Department:</label>
                    <input
                      type="text"
                      value={formDepartment}
                      onChange={(e) => setFormDepartment(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Account Access State:</label>
                    <select
                      value={formStatus}
                      onChange={(e) => setFormStatus(e.target.value as any)}
                      disabled={selectedUser.username === 'admin'}
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    >
                      <option value="ACTIVE">ACTIVE (Authorized)</option>
                      <option value="FROZEN">FROZEN (Suspended / Blocked)</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-gray-500">Reset Password (Optional):</label>
                    <input
                      type="password"
                      placeholder="Leave blank to keep current"
                      value={formPassword}
                      onChange={(e) => setFormPassword(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowEditModal(false)}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold"
                  >
                    {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <CheckCircle2 className="w-3.5 h-3.5 mr-1" />}
                    Save Changes
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* DELETE CONFIRMATION MODAL */}
      <AnimatePresence>
        {showDeleteModal && selectedUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-white dark:bg-[#11141c] border border-rose-200 dark:border-rose-900/60 rounded-2xl shadow-2xl p-6 space-y-4 font-sans text-xs"
            >
              <div className="flex items-center gap-2.5 text-rose-600 font-semibold text-sm">
                <AlertTriangle className="w-5 h-5" />
                <span>Confirm Account Deletion</span>
              </div>

              <p className="text-gray-600 dark:text-gray-400 font-mono text-[11px] leading-relaxed">
                Are you sure you want to permanently delete operator account <strong>@{selectedUser.username}</strong> ({selectedUser.full_name})? This action cannot be undone.
              </p>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowDeleteModal(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDeleteUser}
                  disabled={isSubmitting}
                  className="text-xs bg-rose-600 hover:bg-rose-500 text-white font-semibold"
                >
                  {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Trash2 className="w-3.5 h-3.5 mr-1" />}
                  Confirm Permanent Delete
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
