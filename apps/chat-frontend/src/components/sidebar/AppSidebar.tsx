'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import {
  FileText,
  MessageSquare,
  Search,
  Plus,
  PanelLeftClose,
  PanelLeft,
  Sun,
  Moon,
  Monitor,
  Menu,
  ChevronDown,
  Trash2,
  X,
  LogOut,
  UserCheck,
  Cpu,
  Sparkles,
  ShieldCheck,
  Bell,
  AlertTriangle,
  Lightbulb,
  Users
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { useChatStore } from '@/store/useChatStore';
import { useDeliverableStore } from '@/store/useDeliverableStore';
import { useThemeStore } from '@/store/useThemeStore';
import { useSidebarStore } from '@/store/useSidebarStore';
import { useCustomAgentStore } from '@/store/useCustomAgentStore';
import { useVerificationStore } from '@/store/useVerificationStore';
import { VerificationNotificationModal } from '@/components/verification/VerificationNotificationModal';
import { FeedbackModal } from '@/components/chat/FeedbackModal';
import { RevealBrand, RevealLogoIcon } from '@/components/RevealLogo';
import { motion, AnimatePresence, useDragControls } from 'framer-motion';

export function GeminiSparkleIcon({ className = "h-5 w-5", animated = false }: { className?: string; animated?: boolean }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={`${className} ${animated ? 'animate-pulse' : ''}`}>
      <path d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4771 12 22C12 16.4771 16.4771 12 22 12C16.4771 12 12 7.52285 12 2Z" fill="url(#gemini-sparkle-grad-sidebar)" />
      <defs>
        <linearGradient id="gemini-sparkle-grad-sidebar" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4285F4" />
          <stop offset="0.5" stopColor="#9B72CF" />
          <stop offset="1" stopColor="#D96570" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function SidebarTooltip({
  text,
  children,
  position = 'right'
}: {
  text: string;
  children: React.ReactNode;
  position?: 'right' | 'top';
}) {
  const [show, setShow] = useState(false);
  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div
          className={`absolute ${
            position === 'right'
              ? 'left-full ml-3 top-1/2 -translate-y-1/2'
              : 'bottom-full mb-2 left-1/2 -translate-x-1/2'
          } z-50 pointer-events-none whitespace-nowrap rounded-md bg-slate-900 text-white text-[11px] font-medium px-2 py-1 shadow-lg border border-slate-700/50`}
        >
          {text}
        </div>
      )}
    </div>
  );
}

// ─── Time-grouped chat helpers ──────────────────────────────────────────────
function groupChatsByTime(sessions: any[]) {
  const now = new Date();
  const today: any[] = [];
  const yesterday: any[] = [];
  const prev7: any[] = [];
  const older: any[] = [];

  sessions.forEach((s) => {
    const d = new Date(s.updated_at || s.created_at || now);
    const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) today.push(s);
    else if (diffDays === 1) yesterday.push(s);
    else if (diffDays < 7) prev7.push(s);
    else older.push(s);
  });

  const groups: { label: string; items: any[] }[] = [];
  if (today.length) groups.push({ label: 'Today', items: today });
  if (yesterday.length) groups.push({ label: 'Yesterday', items: yesterday });
  if (prev7.length) groups.push({ label: 'Previous 7 days', items: prev7 });
  if (older.length) groups.push({ label: 'Older', items: older });
  return groups;
}

interface AppSidebarProps {
  onOpenSearchModal?: () => void;
  activePage?: 'chat' | 'artifacts' | 'agents' | 'verification' | 'team-chat';
  onOpenFeedbackModal?: (type: 'ERROR' | 'SUGGESTION') => void;
}

export function AppSidebar({ onOpenSearchModal, activePage = 'chat', onOpenFeedbackModal }: AppSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { sessions, activeSessionId, selectSession, createNewChat, fetchUserSessions } = useChatStore();
  const { deliverables } = useDeliverableStore();
  const { theme, toggleTheme } = useThemeStore();
  const { isOpen: isSidebarOpen, toggle: toggleSidebar, close: closeSidebar } = useSidebarStore();

  const [chatSearch, setChatSearch] = useState('');
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});
  const { user, logout } = useAuthStore();
  const { totalPending, fetchPendingVerifications, openVerificationModal } = useVerificationStore();

  // Local fallback feedback modal if not provided via props
  const [internalFeedbackModal, setInternalFeedbackModal] = useState<{
    isOpen: boolean;
    type: 'ERROR' | 'SUGGESTION';
  }>({
    isOpen: false,
    type: 'ERROR',
  });

  const handleTriggerFeedback = (type: 'ERROR' | 'SUGGESTION') => {
    if (onOpenFeedbackModal) {
      onOpenFeedbackModal(type);
    } else {
      setInternalFeedbackModal({ isOpen: true, type });
    }
  };

  useEffect(() => {
    fetchUserSessions(user?.username || 'operator');
    fetchPendingVerifications();
  }, [user, fetchUserSessions, fetchPendingVerifications]);

  // Keyboard shortcuts: Cmd+B toggle sidebar, Cmd+K search
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
      if (mod && e.key === 'k') {
        e.preventDefault();
        onOpenSearchModal?.();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [toggleSidebar, onOpenSearchModal]);

  const isArtifactsActive = activePage === 'artifacts' || pathname === '/artifacts';
  const isAgentsActive = activePage === 'agents' || pathname === '/agents';
  const isVerificationActive = activePage === 'verification' || pathname === '/verification';
  const isTeamChatActive = activePage === 'team-chat' || pathname === '/team-chat';
  const isChatActive = activePage === 'chat' && pathname !== '/artifacts' && pathname !== '/agents' && pathname !== '/verification' && pathname !== '/team-chat';

  const filteredSessions = useMemo(() => {
    if (!chatSearch.trim()) return sessions;
    const q = chatSearch.toLowerCase();
    return sessions.filter(
      (s) =>
        s.title?.toLowerCase().includes(q) ||
        s.messages?.some((m: any) => m.content?.toLowerCase().includes(q))
    );
  }, [sessions, chatSearch]);

  const groupedSessions = useMemo(() => groupChatsByTime(filteredSessions), [filteredSessions]);

  const handleNewChat = useCallback(async () => {
    const newId = await createNewChat(user?.username || 'operator');
    router.push(`/chat/${newId}`);
    if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar();
  }, [createNewChat, user, router, closeSidebar]);

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      selectSession(sessionId);
      router.push(`/chat/${sessionId}`);
      if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar();
    },
    [selectSession, router, closeSidebar]
  );

  const cycleTheme = useCallback(() => {
    toggleTheme();
  }, [toggleTheme]);

  const themeIcon = theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : theme === 'light' ? <Moon className="h-4 w-4 text-blue-600" /> : <Monitor className="h-4 w-4 text-slate-500" />;

  const toggleGroup = useCallback((label: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [label]: !prev[label] }));
  }, []);

  // ─── Collapsed Rail (desktop only) ────────────────────────────────────────
  const RailView = () => (
    <aside className="relative hidden md:flex flex-col items-center w-[68px] h-full bg-slate-50 border-r border-slate-200 dark:bg-[#080808] dark:border-[#1a1a1a]/80 shrink-0 select-none transition-all duration-300 z-50">
      {/* Brand / Expand */}
      <div className="flex flex-col items-center pt-4 pb-3 w-full">
        <button onClick={toggleSidebar} aria-label="Expand sidebar" className="h-11 w-11 rounded-full hover:bg-slate-200 active:bg-slate-300 dark:hover:bg-[#1e1f20] dark:active:bg-[#282a2c] flex items-center justify-center text-slate-600 hover:text-slate-900 dark:text-[#c4c7c5] dark:hover:text-white transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer">
          <RevealLogoIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Actions */}
      <div className="flex flex-col items-center space-y-3 flex-1 w-full">
        <SidebarTooltip text="New chat">
          <button onClick={handleNewChat} aria-label="New chat" className="h-10 w-10 rounded-full bg-white hover:bg-slate-100 border border-slate-200 dark:bg-[#1e1f20] dark:hover:bg-[#282a2c] dark:border-[#3c4043]/40 flex items-center justify-center text-slate-900 hover:text-blue-600 dark:text-[#e3e3e3] dark:hover:text-[#a8c7fa] transition-all duration-200 hover:scale-105 active:scale-95 shadow-sm cursor-pointer">
            <Plus className="h-4 w-4" />
          </button>
        </SidebarTooltip>

        <SidebarTooltip text="Search chats">
          <button onClick={() => onOpenSearchModal?.()} aria-label="Search chats" className="h-10 w-10 flex items-center justify-center rounded-full hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer">
            <Search className="h-4 w-4" />
          </button>
        </SidebarTooltip>

        <SidebarTooltip text="Chats">
          <Link href="/chat" aria-label="Chats" className={`h-10 w-10 flex items-center justify-center rounded-full transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer ${isChatActive ? 'bg-blue-50 text-blue-700 dark:bg-[#1e1f20] dark:text-[#a8c7fa]' : 'hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white'}`}>
            <MessageSquare className="h-4 w-4" />
          </Link>
        </SidebarTooltip>

        <SidebarTooltip text="Agent Builder">
          <Link
            href="/agents"
            aria-label="Agent Builder"
            className={`h-10 w-10 flex items-center justify-center rounded-full transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer ${
              isAgentsActive
                ? 'bg-blue-50 text-blue-700 dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                : 'hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white'
            }`}
          >
            <Cpu className="h-4 w-4" />
          </Link>
        </SidebarTooltip>

        <SidebarTooltip text="Team Collaboration">
          <Link
            href="/team-chat"
            aria-label="Team Collaboration"
            className={`relative h-10 w-10 flex items-center justify-center rounded-full transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer ${
              isTeamChatActive
                ? 'bg-blue-50 text-blue-700 dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                : 'hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white'
            }`}
          >
            <Users className="h-4 w-4" />
          </Link>
        </SidebarTooltip>

        <SidebarTooltip text="Artifacts">
          <Link href="/artifacts" aria-label="Artifacts" className={`relative h-10 w-10 flex items-center justify-center rounded-full transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer ${isArtifactsActive ? 'bg-blue-50 text-blue-700 dark:bg-[#1e1f20] dark:text-[#a8c7fa]' : 'hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white'}`}>
            <FileText className="h-4 w-4" />
          </Link>
        </SidebarTooltip>

        {/* 2-Step Verification Hub Icon (Role-Gated via Admin/Permissions) */}
        {Boolean(user?.can_verify || ['PROCESS_LEAD', 'MAINTENANCE_ENG', 'SUPER_ADMIN'].includes(user?.role || '')) && (
          <SidebarTooltip text={`Verification Hub (${totalPending} pending)`}>
            <Link
              href="/verification"
              aria-label="Human Verification Hub"
              className={`relative h-10 w-10 flex items-center justify-center rounded-full transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer ${
                isVerificationActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                  : 'hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white'
              }`}
            >
              <ShieldCheck className="h-4 w-4" />
              {totalPending > 0 && (
                <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-blue-600 text-[9px] font-bold text-white shadow-xs">
                  {totalPending > 9 ? '9+' : totalPending}
                </span>
              )}
            </Link>
          </SidebarTooltip>
        )}
      </div>

      {/* Footer */}
      <div className="flex flex-col items-center space-y-3 pb-4 w-full">
        {/* Quick Report Buttons (Rail) */}
        <SidebarTooltip text="Report Error (Triage)">
          <button
            onClick={() => handleTriggerFeedback('ERROR')}
            aria-label="Report Error"
            className="h-10 w-10 rounded-full hover:bg-rose-500/10 text-rose-500 hover:text-rose-600 dark:text-rose-400 dark:hover:text-rose-300 flex items-center justify-center transition-all hover:scale-105 active:scale-95 cursor-pointer border border-rose-500/20 dark:border-rose-500/30 shadow-xs"
          >
            <AlertTriangle className="h-4 w-4" />
          </button>
        </SidebarTooltip>

        <SidebarTooltip text="Suggest Improvement">
          <button
            onClick={() => handleTriggerFeedback('SUGGESTION')}
            aria-label="Suggest Improvement"
            className="h-10 w-10 rounded-full hover:bg-amber-500/10 text-amber-500 hover:text-amber-600 dark:text-amber-400 dark:hover:text-amber-300 flex items-center justify-center transition-all hover:scale-105 active:scale-95 cursor-pointer border border-amber-500/20 dark:border-amber-500/30 shadow-xs"
          >
            <Lightbulb className="h-4 w-4" />
          </button>
        </SidebarTooltip>

        {user && (
          <SidebarTooltip text={`Sign Out (@${user.username})`}>
            <button
              onClick={logout}
              aria-label="Sign Out"
              className="h-10 w-10 rounded-full hover:bg-rose-100 dark:hover:bg-rose-950/40 text-slate-700 hover:text-rose-600 dark:text-[#e3e3e3] dark:hover:text-rose-400 flex items-center justify-center transition-all hover:scale-105 active:scale-95 cursor-pointer border border-slate-200 dark:border-[#3c4043]"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </SidebarTooltip>
        )}

        <SidebarTooltip text={`Theme: ${theme}`}>
          <button onClick={cycleTheme} aria-label="Cycle theme" className="h-10 w-10 rounded-full hover:bg-slate-200 dark:hover:bg-[#1e1f20] flex items-center justify-center text-slate-700 dark:text-[#e3e3e3] transition-all hover:scale-105 active:scale-95 cursor-pointer border border-slate-200 dark:border-[#3c4043]">
            {themeIcon}
          </button>
        </SidebarTooltip>
      </div>
    </aside>
  );

  // ─── Expanded Panel ───────────────────────────────────────────────────────
  const ExpandedView = () => (
    <aside className="fixed md:relative inset-y-0 left-0 z-50 h-full w-[82vw] max-w-[290px] md:w-[280px] bg-slate-50 border-r border-slate-200 dark:bg-[#080808] dark:border-[#1a1a1a]/80 flex flex-col justify-between select-none transition-all duration-300 ease-in-out shrink-0 shadow-2xl md:shadow-none pointer-events-auto">
      {/* Top */}
      <div className="flex flex-col w-full min-w-0 flex-1 overflow-hidden">
        {/* Brand Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2 shrink-0">
          <Link href="/chat" onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar(); }} className="flex items-center space-x-2.5 group">
            <RevealBrand size="md" />
          </Link>
          <button onClick={toggleSidebar} aria-label="Collapse sidebar" className="h-8 w-8 rounded-full hover:bg-slate-200 active:bg-slate-300 dark:hover:bg-[#1e1f20] dark:active:bg-[#282a2c] flex items-center justify-center text-slate-500 hover:text-slate-900 dark:text-[#8e918f] dark:hover:text-[#e3e3e3] transition-colors cursor-pointer">
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>

        {/* Action Button: New Chat */}
        <div className="px-3 pt-2 pb-1 shrink-0">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center space-x-2.5 px-3.5 py-2.5 rounded-2xl bg-white hover:bg-slate-100 border border-slate-200 dark:bg-[#1a1a1e] dark:hover:bg-[#242428] dark:border-[#2a2a30] text-slate-800 dark:text-white text-xs font-semibold shadow-xs transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
          >
            <div className="h-6 w-6 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
              <Plus className="h-3.5 w-3.5 stroke-[2.5]" />
            </div>
            <span>New Chat</span>
          </button>
        </div>

        {/* Search Input in Sidebar */}
        <div className="px-3 py-1.5 shrink-0">
          <div className="relative flex items-center">
            <Search className="absolute left-3 h-3.5 w-3.5 text-slate-400 dark:text-[#8e918f]" />
            <input
              type="text"
              value={chatSearch}
              onChange={(e) => setChatSearch(e.target.value)}
              placeholder="Search conversations..."
              className="w-full bg-slate-200/60 dark:bg-[#141416] border border-slate-200/80 dark:border-[#222226] rounded-xl pl-8 pr-7 py-1.5 text-xs text-slate-800 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#8e918f] focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {chatSearch && (
              <button
                onClick={() => setChatSearch('')}
                className="absolute right-2 text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Core Nav Links */}
        <div className="px-3 py-1 space-y-0.5 shrink-0">
          <Link
            href="/chat"
            onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar(); }}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs transition-colors min-h-[38px] cursor-pointer ${
              isChatActive
                ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                : 'hover:bg-slate-200/80 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white font-medium'
            }`}
          >
            <MessageSquare className="h-4 w-4 shrink-0" />
            <span>Chats</span>
          </Link>
          <Link
            href="/team-chat"
            onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar(); }}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs transition-colors min-h-[38px] cursor-pointer ${
              isTeamChatActive
                ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                : 'hover:bg-slate-200/80 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white font-medium'
            }`}
          >
            <Users className="h-4 w-4 shrink-0" />
            <span>Team Collaboration</span>
          </Link>
          <Link
            href="/artifacts"
            onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar(); }}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs transition-colors min-h-[38px] cursor-pointer ${
              isArtifactsActive
                ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                : 'hover:bg-slate-200/80 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white font-medium'
            }`}
          >
            <FileText className="h-4 w-4 shrink-0" />
            <span>Artifacts</span>
          </Link>
          <Link
            href="/agents"
            onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar(); }}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs transition-colors min-h-[38px] cursor-pointer ${
              isAgentsActive
                ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                : 'hover:bg-slate-200/80 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white font-medium'
            }`}
          >
            <Cpu className="h-4 w-4 shrink-0" />
            <span>Agent Builder</span>
          </Link>

          {/* 2-Step Verification Hub Navigation Link */}
          {Boolean(user?.can_verify || ['PROCESS_LEAD', 'MAINTENANCE_ENG', 'SUPER_ADMIN'].includes(user?.role || '')) && (
            <Link
              href="/verification"
              onClick={() => { if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar(); }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-colors min-h-[38px] cursor-pointer ${
                isVerificationActive
                  ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                  : 'hover:bg-slate-200/80 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white font-medium'
              }`}
            >
              <div className="flex items-center space-x-3">
                <ShieldCheck className="h-4 w-4 shrink-0 text-blue-600 dark:text-[#a8c7fa]" />
                <span>Verification Hub</span>
              </div>
              {totalPending > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-600 dark:bg-blue-500/20 dark:text-[#a8c7fa] border border-blue-200 dark:border-blue-500/30">
                  {totalPending} pending
                </span>
              )}
            </Link>
          )}
        </div>

        {/* Recent Chats — Grouped */}
        <div className="flex-1 min-h-0 overflow-y-auto px-3 pt-2 border-t border-slate-200/60 dark:border-[#282a2c]/40">
          <div className="px-1 pb-1.5 text-[10px] font-bold text-slate-400 dark:text-[#8e918f] uppercase tracking-wider">
            Recent Chats
          </div>
          {groupedSessions.length === 0 ? (
            <div className="px-3 py-6 text-center">
              <MessageSquare className="h-8 w-8 text-slate-300 dark:text-[#3c4043] mx-auto mb-2" />
              <p className="text-[11px] text-slate-400 dark:text-[#8e918f] font-medium">
                {chatSearch ? 'No matches found' : 'No conversations yet'}
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {groupedSessions.map((group) => (
                <div key={group.label}>
                  <button
                    onClick={() => toggleGroup(group.label)}
                    className="w-full flex items-center justify-between px-2 py-1 text-[10px] font-bold text-slate-400 dark:text-[#8e918f] uppercase tracking-wider hover:text-slate-600 dark:hover:text-[#c4c7c5] cursor-pointer"
                  >
                    <span>{group.label}</span>
                    <ChevronDown className={`h-3 w-3 transition-transform ${collapsedGroups[group.label] ? '-rotate-90' : ''}`} />
                  </button>
                  {!collapsedGroups[group.label] && (
                    <div className="space-y-0.5">
                      {group.items.map((sess) => {
                        const isActive = sess.id === activeSessionId && isChatActive;
                        return (
                          <button
                            key={sess.id}
                            onClick={() => handleSelectSession(sess.id)}
                            className={`w-full text-left px-3 py-1.5 rounded-xl text-xs transition-all flex items-center space-x-2.5 truncate min-h-[34px] cursor-pointer ${
                              isActive
                                ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                                : 'text-slate-700 hover:bg-slate-200/70 hover:text-slate-900 dark:text-[#c4c7c5] dark:hover:bg-[#1e1f20]/60 dark:hover:text-white font-medium'
                            }`}
                          >
                            <MessageSquare className="h-3 w-3 shrink-0 opacity-60" />
                            <span className="truncate">{sess.title || 'New conversation'}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-3 pt-2 pb-3 border-t border-slate-200/60 dark:border-[#282a2c]/40 space-y-2">
        {/* Quick Error & Suggestion Triage Buttons */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleTriggerFeedback('ERROR')}
            className="flex items-center justify-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:hover:bg-rose-500/20 dark:text-rose-400 border border-rose-200 dark:border-rose-500/30 text-[11px] font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-xs"
            title="Report inaccurate AI answer or system issue"
          >
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            <span>Report Error</span>
          </button>
          <button
            onClick={() => handleTriggerFeedback('SUGGESTION')}
            className="flex items-center justify-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:hover:bg-amber-500/20 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30 text-[11px] font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-xs"
            title="Suggest prompt/SOP improvements or fixes"
          >
            <Lightbulb className="h-3.5 w-3.5 shrink-0" />
            <span>Suggest Fix</span>
          </button>
        </div>

        {/* Active Operator Pill */}
        {user && (
          <div className="flex items-center justify-between p-2 rounded-xl bg-white dark:bg-[#141416] border border-slate-200 dark:border-[#222228]">
            <div className="flex items-center space-x-2.5 min-w-0">
              <div className="h-7 w-7 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs shrink-0">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-800 dark:text-white truncate">
                  {user.full_name || user.username}
                </div>
                <div className="text-[10px] text-slate-400 font-mono truncate">
                  @{user.username} • {user.role}
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                logout();
                router.push('/login');
              }}
              title="Sign Out"
              className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 px-2">
            <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400">Theme</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 capitalize font-semibold">
              {theme}
            </span>
          </div>
          <SidebarTooltip text={`Switch theme`} position="top">
            <button onClick={cycleTheme} aria-label="Cycle theme" className="p-2 rounded-full hover:bg-slate-200 dark:hover:bg-[#1e1f20] text-slate-700 dark:text-[#e3e3e3] transition-all hover:scale-105 active:scale-95 cursor-pointer border border-slate-200 dark:border-[#3c4043]">
              {themeIcon}
            </button>
          </SidebarTooltip>
        </div>
      </div>
    </aside>
  );

  // ─── Mobile Drawer (off-canvas) ───────────────────────────────────────────
  const MobileDrawer = () => (
    <>
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeSidebar}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.aside
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 left-0 z-50 w-[80vw] max-w-[320px] bg-slate-50 border-r border-slate-200 dark:bg-[#080808] dark:border-[#1a1a1a] shadow-2xl flex flex-col justify-between md:hidden"
          >
            <div className="flex flex-col h-full p-4 overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between pb-3">
                <Link href="/chat" onClick={closeSidebar} className="flex items-center space-x-2">
                  <RevealBrand size="md" />
                </Link>
                <button onClick={closeSidebar} aria-label="Close sidebar" className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-[#1e1f20]">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Action Button: New Chat */}
              <button
                onClick={handleNewChat}
                className="w-full flex items-center space-x-3 px-4 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md transition-all active:scale-[0.98] mb-3"
              >
                <Plus className="h-4 w-4 stroke-[2.5]" />
                <span>New Chat</span>
              </button>

              {/* Search */}
              <div className="pb-3">
                <div className="relative flex items-center">
                  <Search className="absolute left-3.5 h-4 w-4 text-slate-400 dark:text-[#8e918f]" />
                  <input
                    type="text"
                    value={chatSearch}
                    onChange={(e) => setChatSearch(e.target.value)}
                    placeholder="Search conversations..."
                    className="w-full bg-white dark:bg-[#141416] border border-slate-200 dark:border-[#222226] rounded-xl pl-10 pr-8 py-2 text-sm text-slate-800 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#8e918f] focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  {chatSearch && (
                    <button
                      onClick={() => setChatSearch('')}
                      className="absolute right-3 text-slate-400 hover:text-slate-600 dark:hover:text-white"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>

              {/* Nav Links */}
              <div className="pb-2 space-y-0.5">
                <Link href="/chat" onClick={closeSidebar} className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm transition-colors min-h-[44px] cursor-pointer ${isChatActive ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]' : 'text-slate-700 hover:bg-slate-100 dark:text-[#c4c7c5] dark:hover:bg-[#1e1f20] font-medium'}`}>
                  <MessageSquare className="h-[18px] w-[18px] shrink-0" />
                  <span>Chats</span>
                </Link>
                <Link href="/artifacts" onClick={closeSidebar} className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm transition-colors min-h-[44px] cursor-pointer ${isArtifactsActive ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]' : 'text-slate-700 hover:bg-slate-100 dark:text-[#c4c7c5] dark:hover:bg-[#1e1f20] font-medium'}`}>
                  <FileText className="h-[18px] w-[18px] shrink-0" />
                  <span>Artifacts</span>
                </Link>
              </div>

              {/* Divider */}
              <div className="border-t border-slate-200 dark:border-[#282a2c]/60 my-1" />

              {/* Recent Chats */}
              <div className="flex-1 min-h-0 overflow-y-auto pt-1 pb-2">
                <div className="px-2 pb-2 text-[10px] font-bold text-slate-400 dark:text-[#8e918f] uppercase tracking-wider">
                  Recent
                </div>
                {groupedSessions.length === 0 ? (
                  <div className="px-3 py-8 text-center">
                    <MessageSquare className="h-10 w-10 text-slate-200 dark:text-[#282a2c] mx-auto mb-2" />
                    <p className="text-xs text-slate-400 dark:text-[#8e918f]">
                      {chatSearch ? 'No matches' : 'Start a new chat'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {groupedSessions.map((group) => (
                      <div key={group.label}>
                        <button onClick={() => toggleGroup(group.label)} className="w-full flex items-center justify-between px-2 py-1 text-[10px] font-bold text-slate-400 dark:text-[#8e918f] uppercase tracking-wider cursor-pointer">
                          <span>{group.label}</span>
                          <ChevronDown className={`h-3 w-3 transition-transform ${collapsedGroups[group.label] ? '-rotate-90' : ''}`} />
                        </button>
                        {!collapsedGroups[group.label] && (
                          <div className="space-y-0.5">
                            {group.items.map((sess) => {
                              const isActive = sess.id === activeSessionId && isChatActive;
                              return (
                                <button
                                  key={sess.id}
                                  onClick={() => handleSelectSession(sess.id)}
                                  className={`w-full text-left px-3 py-2 rounded-xl text-[13px] transition-all flex items-center space-x-2.5 truncate min-h-[40px] cursor-pointer ${
                                    isActive
                                      ? 'bg-blue-50 text-blue-700 font-bold dark:bg-[#1e1f20] dark:text-[#a8c7fa]'
                                      : 'text-slate-700 hover:bg-slate-100 dark:text-[#c4c7c5] dark:hover:bg-[#1e1f20]/60 font-medium'
                                  }`}
                                >
                                  <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-50" />
                                  <span className="truncate">{sess.title || 'New conversation'}</span>
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Mobile Drawer Footer Feedback Buttons & Operator Info */}
              <div className="shrink-0 pt-2 border-t border-slate-200 dark:border-[#282a2c]/60 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => {
                      closeSidebar();
                      handleTriggerFeedback('ERROR');
                    }}
                    className="flex items-center justify-center space-x-1.5 px-2.5 py-2 rounded-xl bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400 border border-rose-200 dark:border-rose-500/30 text-xs font-semibold"
                  >
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                    <span>Report Error</span>
                  </button>
                  <button
                    onClick={() => {
                      closeSidebar();
                      handleTriggerFeedback('SUGGESTION');
                    }}
                    className="flex items-center justify-center space-x-1.5 px-2.5 py-2 rounded-xl bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30 text-xs font-semibold"
                  >
                    <Lightbulb className="h-3.5 w-3.5 shrink-0" />
                    <span>Suggest Fix</span>
                  </button>
                </div>

                {user && (
                  <div className="p-3 flex items-center justify-between bg-white dark:bg-[#101014] rounded-xl border border-slate-200 dark:border-[#222228]">
                    <div className="flex items-center space-x-2 min-w-0">
                      <div className="h-7 w-7 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs shrink-0">
                        {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-800 dark:text-white truncate">
                          {user.full_name || user.username}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono truncate">
                          @{user.username}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        logout();
                        closeSidebar();
                        router.push('/login');
                      }}
                      className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-400 hover:text-rose-500 transition-colors"
                      title="Sign Out"
                    >
                      <LogOut className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );

  return (
    <>
      {/* Mobile: only show drawer, never show rail/expanded */}
      <div className="md:hidden">
        <MobileDrawer />
      </div>
      {/* Desktop: show rail or expanded, never show drawer */}
      <div className="hidden md:block">
        {isSidebarOpen ? <ExpandedView /> : <RailView />}
      </div>

      {/* Role-Gated 2-Step Verification Notification & Action Modal */}
      <VerificationNotificationModal />

      {/* Fallback internal Feedback Modal */}
      <FeedbackModal
        isOpen={internalFeedbackModal.isOpen}
        initialType={internalFeedbackModal.type}
        onClose={() => setInternalFeedbackModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </>
  );
}
