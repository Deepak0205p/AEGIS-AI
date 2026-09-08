'use client';

import React, { useId } from 'react';
import { useThemeStore } from '@/store/useThemeStore';

interface RevealLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  animated?: boolean;
  className?: string;
}

export function RevealLogoIcon({
  className = "h-5 w-5",
  animated = false
}: {
  className?: string;
  animated?: boolean;
}) {
  const id = useId().replace(/:/g, '');
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <div className={`relative inline-flex items-center justify-center shrink-0 ${className}`}>
      <svg
        viewBox="0 0 44 44"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`w-full h-full transition-all duration-300 ${
          isDark
            ? 'filter drop-shadow-[0_0_14px_rgba(56,189,248,0.5)]'
            : 'filter drop-shadow-[0_4px_12px_rgba(37,99,235,0.25)]'
        }`}
      >
        <defs>
          {/* Light Mode: Royal Cobalt to Vivid Indigo to Purple Gradient */}
          <linearGradient id={`gradMainLight_${id}`} x1="4" y1="2" x2="40" y2="42" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#2563eb" />
            <stop offset="50%" stopColor="#4f46e5" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>

          <linearGradient id={`gradCyanLight_${id}`} x1="40" y1="2" x2="4" y2="42" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="50%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>

          {/* Dark Mode: Electric Cyan to Cyber Blue to Neon Purple */}
          <linearGradient id={`gradMainDark_${id}`} x1="4" y1="2" x2="40" y2="42" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="50%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>

          <linearGradient id={`gradCyanDark_${id}`} x1="40" y1="2" x2="4" y2="42" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#c084fc" />
          </linearGradient>

          {/* Radial Ambient Glow */}
          <radialGradient id={`glowLight_${id}`} cx="22" cy="22" r="18" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#93c5fd" stopOpacity="0.7" />
            <stop offset="60%" stopColor="#c7d2fe" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#e0e7ff" stopOpacity="0" />
          </radialGradient>

          <radialGradient id={`glowDark_${id}`} cx="22" cy="22" r="18" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.45" />
            <stop offset="55%" stopColor="#6366f1" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Ambient Halo Background */}
        <circle
          cx="22"
          cy="22"
          r="18"
          fill={isDark ? `url(#glowDark_${id})` : `url(#glowLight_${id})`}
          className={animated ? 'animate-pulse' : ''}
        />

        {/* AEGIS Sovereign Shield Outer Hull */}
        <path
          d="M22 3.5 L39 9.5 V22 C39 31.5 31.8 38.5 22 41.5 C12.2 38.5 5 31.5 5 22 V9.5 Z"
          stroke={isDark ? `url(#gradMainDark_${id})` : `url(#gradMainLight_${id})`}
          strokeWidth={isDark ? "2.4" : "2.6"}
          strokeLinejoin="round"
          fill={isDark ? "rgba(10, 14, 26, 0.7)" : "rgba(244, 248, 255, 0.8)"}
        />

        {/* Inner Shield Bevel Accent */}
        <path
          d="M22 7.5 L35 12 V21.5 C35 29 29.5 34.5 22 37 C14.5 34.5 9 29 9 21.5 V12 Z"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
          strokeWidth="1.2"
          strokeOpacity={isDark ? "0.6" : "0.4"}
          fill="none"
        />

        {/* Stylized AEGIS 'A' Monogram Chevron */}
        {/* Left 'A' Wing Leg */}
        <path
          d="M22 11 L14 29"
          stroke={isDark ? `url(#gradMainDark_${id})` : `url(#gradMainLight_${id})`}
          strokeWidth="3.2"
          strokeLinecap="round"
        />
        
        {/* Right 'A' Wing Leg */}
        <path
          d="M22 11 L30 29"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
          strokeWidth="3.2"
          strokeLinecap="round"
        />

        {/* 'A' Bridge Horizontal Beam / Crossbar */}
        <path
          d="M17 23.5 H27"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradMainLight_${id})`}
          strokeWidth="2.6"
          strokeLinecap="round"
        />

        {/* Apex Core Glow & Spark */}
        <circle
          cx="22"
          cy="11"
          r="2.2"
          fill="#ffffff"
          className={isDark ? "filter drop-shadow-[0_0_4px_#38bdf8]" : "filter drop-shadow-[0_1px_2px_rgba(0,0,0,0.2)]"}
        />
        <circle
          cx="22"
          cy="11"
          r="1.1"
          fill={isDark ? "#38bdf8" : "#2563eb"}
        />

        {/* Center Quantum AI Nexus Node */}
        <circle
          cx="22"
          cy="23.5"
          r="2"
          fill="#ffffff"
          className={isDark ? "filter drop-shadow-[0_0_5px_#c084fc]" : "filter drop-shadow-[0_1px_2px_rgba(0,0,0,0.2)]"}
        />
        <circle
          cx="22"
          cy="23.5"
          r="1"
          fill={isDark ? "#c084fc" : "#7c3aed"}
        />
      </svg>
    </div>
  );
}

export function RevealBrand({
  size = 'md',
  showBadge = true,
  className = ""
}: {
  size?: 'sm' | 'md' | 'lg';
  showBadge?: boolean;
  className?: string;
}) {
  const iconSize = size === 'sm' ? 'h-5 w-5' : size === 'lg' ? 'h-8 w-8' : 'h-6 w-6';
  const textSize = size === 'sm' ? 'text-[13px]' : size === 'lg' ? 'text-lg' : 'text-sm';
  const badgeSize = size === 'sm' ? 'text-[8.5px] px-1.5 py-0.2' : 'text-[9.5px] px-2 py-0.5';

  return (
    <div className={`flex items-center space-x-2 select-none ${className}`}>
      <RevealLogoIcon className={iconSize} animated={true} />
      <div className="flex items-center space-x-1.5 font-sans">
        <span className={`font-black tracking-tight text-slate-900 dark:text-white ${textSize}`}>
          AEGIS
        </span>
        {showBadge && (
          <span className={`font-black uppercase tracking-wider rounded-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xs ${badgeSize}`}>
            AI
          </span>
        )}
      </div>
    </div>
  );
}
