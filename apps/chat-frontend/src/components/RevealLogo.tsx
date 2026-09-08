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
            ? 'filter drop-shadow-[0_0_12px_rgba(99,102,241,0.45)]'
            : 'filter drop-shadow-[0_4px_10px_rgba(37,99,235,0.22)]'
        }`}
      >
        <defs>
          {/* Light Mode: Deep High-Contrast Royal Sapphire to Vivid Amethyst Gradient */}
          <linearGradient id={`gradMainLight_${id}`} x1="4" y1="4" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#1d4ed8" />
            <stop offset="45%" stopColor="#4338ca" />
            <stop offset="100%" stopColor="#7e22ce" />
          </linearGradient>

          <linearGradient id={`gradCyanLight_${id}`} x1="40" y1="4" x2="4" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0284c7" />
            <stop offset="55%" stopColor="#2563eb" />
            <stop offset="100%" stopColor="#6d28d9" />
          </linearGradient>

          {/* Dark Mode: Radiant Neon Cyan to Electric Indigo to Cyber Purple */}
          <linearGradient id={`gradMainDark_${id}`} x1="4" y1="4" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="45%" stopColor="#818cf8" />
            <stop offset="100%" stopColor="#c084fc" />
          </linearGradient>

          <linearGradient id={`gradCyanDark_${id}`} x1="40" y1="4" x2="4" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="55%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>

          {/* Radial Ambient Glow */}
          <radialGradient id={`glowLight_${id}`} cx="22" cy="22" r="18" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#bfdbfe" stopOpacity="0.8" />
            <stop offset="60%" stopColor="#e0e7ff" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#f3e8ff" stopOpacity="0" />
          </radialGradient>

          <radialGradient id={`glowDark_${id}`} cx="22" cy="22" r="18" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.5" />
            <stop offset="55%" stopColor="#6366f1" stopOpacity="0.25" />
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

        {/* Outer Sovereign Hex Shield Frame */}
        <polygon
          points="22,4 38,13 38,31 22,40 6,31 6,13"
          stroke={isDark ? `url(#gradMainDark_${id})` : `url(#gradMainLight_${id})`}
          strokeWidth={isDark ? "2.5" : "2.8"}
          strokeLinejoin="round"
          fill={isDark ? "rgba(10, 12, 18, 0.55)" : "rgba(240, 245, 255, 0.75)"}
        />

        {/* Internal Faceted Prism Lines */}
        <line
          x1="22"
          y1="4"
          x2="22"
          y2="14"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
          strokeWidth="1.6"
          strokeOpacity={isDark ? "0.7" : "0.5"}
          strokeLinecap="round"
        />
        <line
          x1="6"
          y1="31"
          x2="15"
          y2="25"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
          strokeWidth="1.6"
          strokeOpacity={isDark ? "0.7" : "0.5"}
          strokeLinecap="round"
        />
        <line
          x1="38"
          y1="31"
          x2="29"
          y2="25"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
          strokeWidth="1.6"
          strokeOpacity={isDark ? "0.7" : "0.5"}
          strokeLinecap="round"
        />

        {/* Stylized 'R' Monogram Core */}
        {/* Left vertical pillar */}
        <rect
          x="14.5"
          y="13.5"
          width="3.4"
          height="17"
          rx="1.7"
          fill={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
        />
        
        {/* Upper rounded loop */}
        <path
          d="M16.5 13.5H24C27.3 13.5 29.5 15.7 29.5 19C29.5 22.3 27.3 24.5 24 24.5H16.5V13.5Z"
          stroke={isDark ? `url(#gradMainDark_${id})` : `url(#gradMainLight_${id})`}
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />

        {/* Dynamic diagonal forward strike */}
        <path
          d="M21.5 23.5L29 30.5"
          stroke={isDark ? `url(#gradCyanDark_${id})` : `url(#gradCyanLight_${id})`}
          strokeWidth="3.4"
          strokeLinecap="round"
        />

        {/* Central Brilliant Core Spark */}
        <circle
          cx="22"
          cy="19"
          r="2.2"
          fill="#ffffff"
          className={isDark ? "filter drop-shadow-[0_0_3px_#ffffff]" : "filter drop-shadow-[0_1px_2px_rgba(0,0,0,0.15)]"}
        />
        <circle
          cx="22"
          cy="19"
          r="1.1"
          fill={isDark ? "#38bdf8" : "#1d4ed8"}
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
