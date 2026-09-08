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
  Bot
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { useChatStore } from '@/store/useChatStore';
import { useDeliverableStore } from '@/store/useDeliverableStore';
import { useThemeStore } from '@/store/useThemeStore';
import { useSidebarStore } from '@/store/useSidebarStore';
import { useCustomAgentStore } from '@/store/useCustomAgentStore';
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

export function SidebarTooltip({ children, text, position = 'right' }: { children: React.ReactNode; text: string; position?: 'right' | 'top' }) {
  const [show, setShow] = useState(false);
  return (
    <div
      className="relative flex items-center justify-center"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <AnimatePresence>
        {show && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={`absolute z-[60] pointer-events-none px-2.5 py-1 text-[11px] font-semibold text-slate-900 bg-white border border-slate-200 dark:text-[#e3e3e3] dark:bg-[#1e1f20] dark:border-[#3c4043] rounded-lg shadow-xl whitespace-nowrap ${
              position === 'right' ? 'left-full ml-3 top-1/2 -translate-y-1/2' : 'bottom-full mb-2 left-1/2 -translate-x-1/2'
            }`}
          >
            {text}
          </motion.div>
        )}
      </AnimatePresence>
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
    if (!s.timestamp) { older.push(s); return; }
    const d = new Date(s.timestamp);
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays <= 0) today.push(s);
    else if (diffDays === 1) yesterday.push(s);
    else if (diffDays <= 7) prev7.push(s);
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
  activePage?: 'chat' | 'artifacts';
}

export function AppSidebar({ onOpenSearchModal, activePage = 'chat' }: AppSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { sessions, activeSessionId, selectSession, createNewChat, fetchUserSessions } = useChatStore();
  const { deliverables } = useDeliverableStore();
  const { theme, toggleTheme } = useThemeStore();
  const { isOpen: isSidebarOpen, toggle: toggleSidebar, close: closeSidebar } = useSidebarStore();

  const [chatSearch, setChatSearch] = useState('');
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});
  const { user, logout } = useAuthStore();

  useEffect(() => {
    fetchUserSessions(user?.username || 'operator');
  }, [user, fetchUserSessions]);

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
  const isChatActive = activePage === 'chat' && pathname !== '/artifacts';

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
          <button
            onClick={() => useCustomAgentStore.getState().openModal()}
            aria-label="Agent Builder"
            className="h-10 w-10 flex items-center justify-center rounded-full hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Bot className="h-4 w-4" />
          </button>
        </SidebarTooltip>

        <SidebarTooltip text="Artifacts">
          <Link href="/artifacts" aria-label="Artifacts" className={`relative h-10 w-10 flex items-center justify-center rounded-full transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer ${isArtifactsActive ? 'bg-blue-50 text-blue-700 dark:bg-[#1e1f20] dark:text-[#a8c7fa]' : 'hover:bg-slate-200 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white'}`}>
            <FileText className="h-4 w-4" />
          </Link>
        </SidebarTooltip>
      </div>

      {/* Footer */}
      <div className="flex flex-col items-center space-y-3 pb-4 w-full">
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

        {/* New Chat */}
        <div className="px-3 pb-2 shrink-0">
          <button onClick={handleNewChat} className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-bold transition-all hover:scale-[1.01] active:scale-[0.99] shadow-md min-h-[44px] cursor-pointer">
            <Plus className="h-4 w-4 shrink-0" />
            <span>New chat</span>
          </button>
        </div>

        {/* Inline Search */}
        <div className="px-3 pb-2 shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 dark:text-[#8e918f]" />
            <input
              type="text"
              placeholder="Search chats..."
              value={chatSearch}
              onChange={(e) => setChatSearch(e.target.value)}
              className="w-full pl-9 pr-8 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-900 placeholder-slate-400 dark:bg-[#1e1f20] dark:border-[#3c4043]/50 dark:text-[#e3e3e3] dark:placeholder-[#8e918f] focus:outline-none focus:ring-2 focus:ring-blue-500/30 dark:focus:ring-[#a8c7fa]/30 transition-all min-h-[36px]"
            />
            {chatSearch && (
              <button onClick={() => setChatSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 h-5 w-5 rounded-full hover:bg-slate-200 dark:hover:bg-[#3c4043] flex items-center justify-center text-slate-400 cursor-pointer">
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Navigation Links */}
        <div className="px-3 pb-2 space-y-0.5 shrink-0">
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
          <button
            onClick={() => {
              useCustomAgentStore.getState().openModal();
              if (typeof window !== 'undefined' && window.innerWidth < 768) closeSidebar();
            }}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs transition-colors min-h-[38px] hover:bg-slate-200/80 text-slate-700 hover:text-slate-900 dark:hover:bg-[#1e1f20] dark:text-[#c4c7c5] dark:hover:text-white font-medium cursor-pointer"
          >
            <Bot className="h-4 w-4 shrink-0" />
            <span>Agent Builder</span>
          </button>
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
              className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-400 hover:text-rose-500 transition-colors"
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
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.2}
            onDragEnd={(_, info) => { if (info.offset.x < -80) closeSidebar(); }}
            className="fixed inset-y-0 left-0 z-50 w-[85vw] max-w-[320px] bg-white dark:bg-[#0a0a0a] flex flex-col select-none shadow-2xl md:hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 pt-5 pb-3 shrink-0">
              <Link href="/chat" onClick={closeSidebar}>
                <RevealBrand size="md" />
              </Link>
              <button onClick={closeSidebar} aria-label="Close" className="h-9 w-9 rounded-full hover:bg-slate-100 dark:hover:bg-[#1e1f20] active:bg-slate-200 flex items-center justify-center text-slate-500 dark:text-[#8e918f] transition-colors cursor-pointer">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Body */}
            <div className="flex flex-col flex-1 min-h-0 overflow-hidden px-3">
              {/* New Chat */}
              <div className="pb-3">
                <button onClick={handleNewChat} className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-sm font-bold transition-all active:scale-[0.98] shadow-lg shadow-blue-600/20 min-h-[48px] cursor-pointer">
                  <Plus className="h-4 w-4" />
                  <span>New chat</span>
                </button>
              </div>

              {/* Search */}
              <div className="pb-3">
                <div className="relative">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-[#8e918f]" />
                  <input
                    type="text"
                    placeholder="Search chats..."
                    value={chatSearch}
                    onChange={(e) => setChatSearch(e.target.value)}
                    className="w-full pl-10 pr-9 py-2.5 rounded-xl bg-slate-100 border-0 text-sm text-slate-900 placeholder-slate-400 dark:bg-[#1e1f20] dark:text-[#e3e3e3] dark:placeholder-[#8e918f] focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all"
                  />
                  {chatSearch && (
                    <button onClick={() => setChatSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 rounded-full hover:bg-slate-200 dark:hover:bg-[#3c4043] flex items-center justify-center text-slate-400 cursor-pointer">
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

              {/* Mobile Drawer Footer with Operator & Logout */}
              {user && (
                <div className="shrink-0 p-3 border-t border-slate-200 dark:border-[#282a2c]/60 flex items-center justify-between bg-white dark:bg-[#101014] rounded-xl mt-2">
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
    </>
  );
}
