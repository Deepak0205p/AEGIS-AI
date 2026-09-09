'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import { useNetworkStore } from '@/store/useNetworkStore';
import { useAuthStore } from '@/store/useAuthStore';
import { socketManager } from '@/lib/socket';
import {
  Shield,
  ArrowLeft,
  Sun,
  Moon,
  LogOut,
  User,
  CreditCard,
  Building2,
  Key,
  ShieldCheck,
  ChevronDown,
} from 'lucide-react';

export function Header() {
  const pathname = usePathname();
  const { metrics } = useSovereigntyStore();
  const { deploymentMode, hostIp, port } = useNetworkStore();
  const { user, authMethod, logout, isAuthenticated } = useAuthStore();
  
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    socketManager.connectAuditStream();

    // Initialize theme from localStorage or document element
    const savedTheme = localStorage.getItem('reveal_theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    } else {
      const isDark = document.documentElement.classList.contains('dark');
      setTheme(isDark ? 'dark' : 'light');
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    localStorage.setItem('reveal_theme', nextTheme);
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const isSubpage = pathname !== '/';

  // Role badge color helper
  const getRoleBadgeColor = (role?: string) => {
    switch (role?.toUpperCase()) {
      case 'SUPER_ADMIN':
      case 'PLANT_SECURITY_OFFICER':
        return 'bg-purple-950/60 text-purple-300 border-purple-700/50';
      case 'PROCESS_LEAD':
        return 'bg-cyan-950/60 text-cyan-300 border-cyan-700/50';
      case 'HSE_AUDITOR':
        return 'bg-amber-950/60 text-amber-300 border-amber-700/50';
      default:
        return 'bg-blue-950/60 text-blue-300 border-blue-700/50';
    }
  };

  return (
    <header className="border-b border-gray-200 dark:border-[#262626] bg-white dark:bg-[#000000] px-6 py-2.5 sticky top-0 z-50 transition-colors duration-200">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left: Brand & Navigation */}
        <div className="flex items-center space-x-3">
          {isSubpage ? (
            <Link
              href="/"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-gray-100 dark:bg-[#111111] border border-gray-200 dark:border-[#333333] hover:border-gray-300 dark:hover:border-[#555555] text-xs text-gray-900 dark:text-[#ededed] transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-emerald-600 dark:text-[#00e599]" />
              <span className="font-mono text-[11px]">Overview</span>
            </Link>
          ) : (
            <Link href="/" className="h-5 w-5 rounded bg-gradient-to-tr from-blue-600 to-indigo-600 border border-blue-400/30 flex items-center justify-center font-mono text-[11px] text-white font-bold shadow-xs">
              A
            </Link>
          )}

          <Link href="/" className="text-xs font-semibold tracking-tight text-gray-900 dark:text-[#ededed] hover:text-gray-700 dark:hover:text-white transition-colors">
            A E G I S &nbsp; A I &nbsp; Workbench
          </Link>
          <span className="text-gray-300 dark:text-[#333333]">/</span>
          <span className="text-xs font-mono text-gray-500 dark:text-[#888888]">
            {deploymentMode} ({hostIp}:{port})
          </span>
          <span className="text-gray-300 dark:text-[#333333]">/</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800/60 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
            MULTI-DOMAIN ACTIVE
          </span>
          <Link
            href="/monitor"
            className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800/60 flex items-center gap-1 transition-colors"
          >
            <Shield className="w-3 h-3 text-rose-500" />
            SENTINEL MONITOR
          </Link>
        </div>

        {/* Right: User Badge, Auth Method, Theme Switcher & Air-Gap Pill */}
        <div className="flex items-center space-x-2.5">
          {/* Authenticated User Pill & Dropdown */}
          {isAuthenticated && user && (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-gray-50 dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] hover:border-gray-300 dark:hover:border-cyan-500/40 text-xs font-mono transition-all cursor-pointer"
              >
                {/* Auth Method Icon */}
                {authMethod === 'PKI_SMARTCARD' ? (
                  <span title="SmartCard X.509 PKI Authenticated">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                  </span>
                ) : authMethod === 'INTRANET_LDAP' ? (
                  <span title="Intranet Active Directory Authenticated">
                    <Building2 className="w-3.5 h-3.5 text-blue-400" />
                  </span>
                ) : (
                  <span title="Local Console Session">
                    <Key className="w-3.5 h-3.5 text-purple-400" />
                  </span>
                )}

                <span className="font-semibold text-gray-900 dark:text-gray-200 text-[11px]">
                  {user.username}
                </span>

                <span
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${getRoleBadgeColor(
                    user.role
                  )}`}
                >
                  {user.role}
                </span>

                <ChevronDown className="w-3 h-3 text-gray-400" />
              </button>

              {/* User Dropdown Menu */}
              <AnimatePresence>
                {showUserMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 6 }}
                    className="absolute right-0 mt-1.5 w-64 bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 rounded-lg shadow-xl p-3 space-y-2.5 z-50 text-xs font-mono"
                  >
                    

                    

                    <div className="border-t border-gray-100">
                      <button
                        onClick={() => {
                          setShowUserMenu(false);
                          logout();
                        }}
                        className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60 hover:bg-rose-100 dark:hover:bg-rose-900/40 transition-colors cursor-pointer text-xs"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Logout</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Light / Dark Theme Switcher Button */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-100 dark:bg-[#111111] border border-gray-200 dark:border-[#262626] hover:bg-gray-200 dark:hover:bg-[#1f1f1f] text-xs font-mono text-gray-900 dark:text-[#ededed] transition-colors cursor-pointer"
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Theme`}
          >
            {theme === 'light' ? (
              <Moon className="h-3.5 w-3.5 text-indigo-600" />
            ) : (
              <Sun className="h-3.5 w-3.5 text-amber-400" />
            )}
          </button>

          {/* Air Gap Status Pill */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-gray-50 dark:bg-[#111111] border border-gray-200 dark:border-[#262626] text-xs font-mono">
            <motion.span
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
              className="h-1.5 w-1.5 rounded-full bg-emerald-500 dark:bg-[#00e599] inline-block"
            />
            <Shield className="h-3 w-3 text-emerald-600 dark:text-[#00e599]" />
            <span className="text-gray-900 dark:text-[#ededed] font-medium text-[11px]">
              0 External Egress
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
