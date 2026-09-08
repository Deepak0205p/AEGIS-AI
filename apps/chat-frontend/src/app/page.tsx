'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { useChatStore } from '@/store/useChatStore';
import { socketManager } from '@/lib/socket';
import {
  Menu,
  Plus,
  MessageSquare,
  Sparkles,
  User,
  ArrowUp,
  Square,
  Paperclip,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  Download,
  ShieldCheck,
  Cpu,
  Flame,
  Calculator,
  Binary,
  Mic,
  MicOff,
  Volume2,
  Layers,
  Code,
  Eye,
  FileSpreadsheet,
  Presentation,
  ScanText,
  ArrowLeft,
  Search,
  Sun,
  Moon,
  RotateCcw,
  X,
  Image as ImageIcon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDeliverableStore } from '@/store/useDeliverableStore';
import { useThemeStore } from '@/store/useThemeStore';
import { ArtifactsModal, getFileIcon, getBadgeColor } from '@/components/ArtifactsModal';
import { SearchChatsModal } from '@/components/SearchChatsModal';
import { RevealBrand, RevealLogoIcon } from '@/components/RevealLogo';
import { useCanvasStore } from '@/store/useCanvasStore';
import { DocumentCanvasPanel } from '@/components/canvas/DocumentCanvasPanel';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import { useSidebarStore } from '@/store/useSidebarStore';
import { useAuthStore } from '@/store/useAuthStore';
import { PerplexityReasoningAccordion } from '@/components/chat/PerplexityReasoningAccordion';
import { MarkdownContent } from '@/components/MarkdownContent';

// Ultra-Modern Fluent / Glowing Brand 3D-Style Icon Components
function ExcelIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="exBack" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#107C41" />
          <stop offset="100%" stopColor="#0B552C" />
        </linearGradient>
        <linearGradient id="exFront" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#22C55E" />
          <stop offset="100%" stopColor="#15803D" />
        </linearGradient>
        <filter id="exGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#22C55E" floodOpacity="0.35" />
        </filter>
      </defs>
      <rect x="4" y="6" width="28" height="24" rx="5" fill="url(#exBack)" />
      <path d="M16 6h11a5 5 0 0 1 5 5v14a5 5 0 0 1-5 5H16V6z" fill="#0B552C" fillOpacity="0.4" />
      <g filter="url(#exGlow)">
        <rect x="2" y="10" width="16" height="16" rx="4" fill="url(#exFront)" />
        <path d="M7 14.5l2.6 3.5L7 21.5h2l1.6-2.4 1.6 2.4h2l-2.6-3.5 2.6-3.5h-2l-1.6 2.4-1.6-2.4H7z" fill="#FFFFFF" />
      </g>
    </svg>
  );
}

function PowerPointIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="pptBack" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#D83B01" />
          <stop offset="100%" stopColor="#A82B00" />
        </linearGradient>
        <linearGradient id="pptFront" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FB923C" />
          <stop offset="100%" stopColor="#EA580C" />
        </linearGradient>
        <filter id="pptGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#EA580C" floodOpacity="0.35" />
        </filter>
      </defs>
      <rect x="4" y="6" width="28" height="24" rx="5" fill="url(#pptBack)" />
      <path d="M16 6h11a5 5 0 0 1 5 5v14a5 5 0 0 1-5 5H16V6z" fill="#7A1D00" fillOpacity="0.4" />
      <g filter="url(#pptGlow)">
        <rect x="2" y="10" width="16" height="16" rx="4" fill="url(#pptFront)" />
        <path d="M7 14h3.8a2.5 2.5 0 0 1 0 5H8.7v2.5H7V14zm1.7 3.5h2a1 1 0 0 0 0-2H8.7v2z" fill="#FFFFFF" />
      </g>
    </svg>
  );
}

function WordDocsIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="wdBack" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#185ABD" />
          <stop offset="100%" stopColor="#0E3D85" />
        </linearGradient>
        <linearGradient id="wdFront" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#60A5FA" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
        <filter id="wdGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#3B82F6" floodOpacity="0.35" />
        </filter>
      </defs>
      <rect x="4" y="6" width="28" height="24" rx="5" fill="url(#wdBack)" />
      <path d="M16 6h11a5 5 0 0 1 5 5v14a5 5 0 0 1-5 5H16V6z" fill="#0A2A5E" fillOpacity="0.4" />
      <g filter="url(#wdGlow)">
        <rect x="2" y="10" width="16" height="16" rx="4" fill="url(#wdFront)" />
        <path d="M6 14.5l1.6 7h1.5l1.4-5.2 1.4 5.2h1.5l1.6-7h-1.6l-1 5-1.3-5H9.4l-1.3 5-1-5H6z" fill="#FFFFFF" />
      </g>
    </svg>
  );
}

function VSCodeIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="vsc1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>
        <linearGradient id="vsc2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#60A5FA" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
        <filter id="vscGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#38BDF8" floodOpacity="0.4" />
        </filter>
      </defs>
      <g filter="url(#vscGlow)">
        <path d="M26.5 4.5L18 12.5 10.5 6.5a1.8 1.8 0 0 0-2.5.2L4.5 10.5a1.8 1.8 0 0 0 0 2.5l5.5 5-5.5 5a1.8 1.8 0 0 0 0 2.5l3.5 3.8a1.8 1.8 0 0 0 2.5.2L18 23.5l8.5 8c1 .9 2.5.2 2.5-1.2V5.7c0-1.4-1.5-2.1-2.5-1.2z" fill="url(#vsc1)" />
        <path d="M26.5 4.5L18 12.5l8.5 8V5.7c0-1.4-1.5-2.1-2.5-1.2z" fill="#0369A1" />
        <path d="M26.5 31.5L18 23.5l8.5-8v14.8c0 1.4-1.5 2.1-2.5 1.2z" fill="url(#vsc2)" />
      </g>
    </svg>
  );
}

function VisionCamIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="visGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#34D399" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>
        <filter id="visGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#10B981" floodOpacity="0.4" />
        </filter>
      </defs>
      <g filter="url(#visGlow)">
        <rect x="4" y="7" width="28" height="22" rx="6" fill="url(#visGrad)" />
        <circle cx="18" cy="18" r="7" fill="#064E3B" fillOpacity="0.4" />
        <circle cx="18" cy="18" r="5" fill="#FFFFFF" />
        <circle cx="18" cy="18" r="2.5" fill="#047857" />
        <circle cx="26" cy="12" r="1.5" fill="#FFFFFF" fillOpacity="0.8" />
      </g>
    </svg>
  );
}

function OCRIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="ocrGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#A78BFA" />
          <stop offset="100%" stopColor="#7C3AED" />
        </linearGradient>
        <filter id="ocrGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#8B5CF6" floodOpacity="0.4" />
        </filter>
      </defs>
      <g filter="url(#ocrGlow)">
        <rect x="4" y="5" width="28" height="26" rx="6" fill="url(#ocrGrad)" />
        <path d="M9 13V9h4M27 13V9h-4M9 23v4h4M27 23v4h-4" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 23.5l4-11 4 11M15.5 20.5h5" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </svg>
  );
}

function MasterHubIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 36 36" fill="none" className={className}>
      <defs>
        <linearGradient id="orchCoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#60A5FA" />
          <stop offset="50%" stopColor="#A855F7" />
          <stop offset="100%" stopColor="#EC4899" />
        </linearGradient>
        <linearGradient id="orchRingGrad" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#818CF8" />
        </linearGradient>
        <filter id="orchGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#A855F7" floodOpacity="0.5" />
        </filter>
      </defs>
      <g filter="url(#orchGlow)">
        {/* Outer Orbiting Diamond Ring */}
        <rect x="18" y="2" width="22" height="22" rx="6" transform="rotate(45 18 2)" fill="none" stroke="url(#orchRingGrad)" strokeWidth="2" strokeDasharray="4 2" />
        
        {/* Core Quantum Orchestrator Poly-Prism */}
        <path d="M18 5L29 11.5V24.5L18 31L7 24.5V11.5L18 5Z" fill="url(#orchCoreGrad)" fillOpacity="0.85" />
        <path d="M18 5L29 11.5L18 18L7 11.5L18 5Z" fill="#FFFFFF" fillOpacity="0.3" />
        <path d="M18 18V31L7 24.5V11.5L18 18Z" fill="#000000" fillOpacity="0.2" />
        
        {/* Center Glowing Sparkle Core */}
        <circle cx="18" cy="18" r="3.5" fill="#FFFFFF" />
        <circle cx="18" cy="18" r="1.5" fill="#60A5FA" />
      </g>
    </svg>
  );
}

function GeminiSparkleIcon({ className = "h-5 w-5", animated = false }: { className?: string; animated?: boolean }) {
  return (
    <motion.svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      animate={animated ? { rotate: [0, 15, -10, 0], scale: [1, 1.08, 0.95, 1] } : {}}
      transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
    >
      <defs>
        <linearGradient id="geminiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4285f4" />
          <stop offset="50%" stopColor="#9b72cf" />
          <stop offset="100%" stopColor="#d96570" />
        </linearGradient>
      </defs>
      <path
        d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4771 12 22C12 16.4771 16.4771 12 22 12C16.4771 12 12 7.52285 12 2Z"
        fill="url(#geminiGrad)"
      />
    </motion.svg>
  );
}

// Fluid Motion Orb Ambient Light (Cinematic Aurora Animation)
function FluidAuroraGlow() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
      <motion.div
        animate={{
          scale: [1, 1.15, 0.95, 1],
          x: [0, 30, -25, 0],
          y: [0, -20, 20, 0],
          rotate: [0, 45, 90, 0],
        }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-[20%] left-[30%] w-[300px] sm:w-[600px] h-[225px] sm:h-[450px] bg-gradient-to-tr from-blue-400/10 via-purple-400/8 to-pink-400/6 dark:from-[#4285f4]/15 dark:via-[#9b72cf]/12 dark:to-[#d96570]/10 rounded-full blur-[80px] sm:blur-[110px] opacity-60 sm:opacity-75"
      />
      <motion.div
        animate={{
          scale: [1.1, 0.9, 1.05, 1.1],
          x: [0, -40, 35, 0],
          y: [0, 25, -20, 0],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[25%] right-[25%] w-[250px] sm:w-[500px] h-[190px] sm:h-[380px] bg-gradient-to-bl from-slate-200/30 via-purple-400/8 to-blue-400/8 dark:from-[#1a2333]/40 dark:via-[#9b72cf]/10 dark:to-[#4285f4]/10 rounded-full blur-[90px] sm:blur-[120px] opacity-40 sm:opacity-60"
      />
    </div>
  );
}

const STARTER_PROMPTS = [
  {
    id: 's1',
    title: 'SOP Compliance Audit',
    desc: 'Verify equipment limits & emergency actions',
    icon: <Flame className="h-5 w-5 text-amber-400" />,
    prompt: 'Review the uploaded inspection report and evaluate compliance against applicable SOPs.'
  },
  {
    id: 's2',
    title: 'Pump Efficiency Calculation',
    desc: 'Compute hydraulic power & generate calculation register',
    icon: <Calculator className="h-5 w-5 text-[#a8c7fa]" />,
    prompt: 'Write a Python script to calculate centrifugal pump hydraulic efficiency with the specified parameters. Execute in sandbox.'
  },
  {
    id: 's3',
    title: 'ISA 5.1 Tag Verification',
    desc: 'Analyze instrumentation symbols & pressure relief valves',
    icon: <Binary className="h-5 w-5 text-emerald-400" />,
    prompt: 'List the mandatory ISA 5.1 instrumentation tags and verification criteria for the specified unit.'
  },
  {
    id: 's4',
    title: 'Refinery Operating Inquiries',
    desc: 'Ask any engineering or operating procedure question',
    icon: <Sparkles className="h-5 w-5 text-purple-400" />,
    prompt: 'What are the main causes of high tube skin temperature in a crude refinery furnace and what corrective action is mandated?'
  }
];

function ChatThinkingAccordion({ steps }: { steps: any[] }) {
  const [isOpen, setIsOpen] = useState(false);
  if (!steps || steps.length === 0) return null;

  return (
    <div className="w-full my-2.5 rounded-2xl border border-slate-200 dark:border-[#222225] bg-slate-50 dark:bg-[#0c0c0e] overflow-hidden text-xs shadow-xs transition-all">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3.5 py-3 min-h-[44px] flex items-center justify-between hover:bg-slate-100 dark:hover:bg-[#161618] active:bg-slate-200 dark:active:bg-[#1a1a1c] text-slate-600 dark:text-[#9aa0a6] text-left transition-colors select-none cursor-pointer"
      >
        <div className="flex items-center space-x-2.5">
          <div className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse shrink-0" />
          <span className="font-bold text-slate-800 dark:text-[#e3e3e3] text-[13px] sm:text-xs">
            Reasoning Chain ({steps.length} {steps.length === 1 ? 'step' : 'steps'})
          </span>
        </div>
        <div className="h-6 w-6 rounded-full bg-slate-200/70 dark:bg-[#161618] flex items-center justify-center text-slate-500 dark:text-[#8e918f]">
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.2, 0, 0, 1] }}
            className="px-3 sm:px-4 py-3 border-t border-slate-200 dark:border-[#1e1e22] space-y-2.5 font-mono text-[11px] text-slate-600 dark:text-[#9aa0a6] leading-relaxed bg-white dark:bg-[#080808]"
          >
            {steps.map((step, idx) => (
              <div key={step.id || idx} className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#0e0e11] border border-slate-200 dark:border-[#1e1e22] overflow-hidden">
                <div className="flex items-center justify-between text-blue-600 dark:text-[#a8c7fa] pb-1.5 text-[10px] sm:text-[11px] gap-2">
                  <span className="font-bold uppercase tracking-wider truncate">
                    {step.type} {step.tool_name ? `(${step.tool_name})` : ''}
                  </span>
                  {step.duration_ms && <span className="text-slate-400 dark:text-[#8e918f] shrink-0">{step.duration_ms}ms</span>}
                </div>
                <div className="text-slate-800 dark:text-[#e3e3e3] whitespace-pre-wrap break-words overflow-x-auto max-w-full font-sans text-xs">
                  {step.content}
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function CustomTooltip({
  text,
  children,
  position = 'right',
  disabled = false,
  className = '',
}: {
  text: string;
  children: React.ReactNode;
  position?: 'right' | 'top' | 'bottom' | 'left';
  disabled?: boolean;
  className?: string;
}) {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const show = () => {
    if (disabled || !text) return;
    timeoutRef.current = setTimeout(() => setIsVisible(true), 250);
  };

  const hide = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  const positionClasses = {
    right: 'left-full top-1/2 -translate-y-1/2 ml-2.5',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2.5',
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  }[position];

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: position === 'top' ? 4 : position === 'bottom' ? -4 : 0, x: position === 'right' ? -4 : position === 'left' ? 4 : 0 }}
            animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.15, ease: [0.2, 0, 0, 1] }}
            className={`absolute ${positionClasses} z-50 pointer-events-none whitespace-nowrap`}
          >
            <div className="px-2.5 py-1 text-[11px] font-medium text-[#f1f3f4] bg-[#282a2c] border border-[#3c4043] rounded-lg shadow-xl shadow-black/40 backdrop-blur-md">
              {text}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function GeminiReplicaChatApp() {
  const router = useRouter();
  const urlParams = useParams();
  const initialSessionId = Array.isArray(urlParams?.id) ? urlParams.id[0] : (urlParams?.id as string | undefined);
  const {
    sessions,
    activeSessionId,
    isStreaming,
    regeneratingMsgId,
    currentInput,
    createNewChat,
    selectSession,
    fetchUserSessions,
    setCurrentInput,
    addMessage,
    setStreaming,
    activeTraceSteps
  } = useChatStore();
  const { toggle: toggleSidebar } = useSidebarStore();
  const { user, isAuthenticated, isLoading: isAuthLoading, initialize: initAuth } = useAuthStore();

  // Sync initialSessionId from dynamic route /chat/[id]
  useEffect(() => {
    if (initialSessionId && initialSessionId !== activeSessionId) {
      selectSession(initialSessionId);
    }
  }, [initialSessionId, activeSessionId, selectSession]);

  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const speechBaseTextRef = useRef<string>('');
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];
  const messages = activeSession ? activeSession.messages : [];
  const hasMessages = messages.length > 0;

  const lastUserMsgRef = useRef<HTMLDivElement>(null);

  // Auto-Scroll to keep latest query & live thinking steps right in comfortable view
  const scrollToActive = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (isStreaming && lastUserMsgRef.current) {
      lastUserMsgRef.current.scrollIntoView({ behavior, block: 'start' });
    } else if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior, block: 'end' });
    }
  }, [isStreaming]);

  useEffect(() => {
    if (hasMessages) {
      scrollToActive('smooth');
      const timer = setTimeout(() => scrollToActive('smooth'), 80);
      const timer2 = setTimeout(() => scrollToActive('smooth'), 250);
      return () => {
        clearTimeout(timer);
        clearTimeout(timer2);
      };
    }
  }, [messages.length, isStreaming, activeTraceSteps.length, scrollToActive, hasMessages]);

  // Cleanup speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
    };
  }, []);

  // Web Speech Recognition Audio Transcription Handler
  const toggleSpeechRecognition = () => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Google Chrome, Microsoft Edge, or Safari.');
      return;
    }

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      // Snapshot the exact text in the prompt box before recording started
      const currentVal = useChatStore.getState().currentInput;
      speechBaseTextRef.current = typeof currentVal === 'string' ? currentVal.trim() : '';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = 0; i < event.results.length; ++i) {
          const res = event.results[i];
          if (!res || !res[0]) continue;
          const text = (res[0].transcript || '').trim();
          if (!text) continue;

          if (res.isFinal) {
            if (!finalTranscript) {
              finalTranscript = text;
            } else {
              const lowerFinal = finalTranscript.toLowerCase();
              const lowerText = text.toLowerCase();
              if (lowerText.startsWith(lowerFinal)) {
                // Mobile Android Chrome sends accumulated string; take the newest full sentence
                finalTranscript = text;
              } else if (lowerFinal.endsWith(lowerText) || lowerFinal.includes(lowerText)) {
                // Duplicate fragment already present
              } else {
                // Desktop incremental chunk
                finalTranscript = `${finalTranscript} ${text}`;
              }
            }
          } else {
            interimTranscript = text;
          }
        }

        let sessionSpeech = finalTranscript;
        if (interimTranscript) {
          const lowerFinal = finalTranscript.toLowerCase().trim();
          const lowerInterim = interimTranscript.toLowerCase().trim();
          if (!lowerFinal) {
            sessionSpeech = interimTranscript;
          } else if (lowerInterim.startsWith(lowerFinal)) {
            sessionSpeech = interimTranscript;
          } else if (lowerFinal.endsWith(lowerInterim) || lowerFinal.includes(lowerInterim)) {
            sessionSpeech = finalTranscript;
          } else {
            sessionSpeech = `${finalTranscript} ${interimTranscript}`;
          }
        }

        sessionSpeech = sessionSpeech.trim();
        const base = speechBaseTextRef.current;
        const combined = base ? (sessionSpeech ? `${base} ${sessionSpeech}` : base) : sessionSpeech;

        setCurrentInput(combined);
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition status:', event.error);
        if (event.error !== 'no-speech') {
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setIsListening(false);
    }
  };

  // Dynamic auto-growing textarea logic (Gemini / Claude pattern)
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const nextHeight = Math.min(Math.max(textareaRef.current.scrollHeight, 24), 200);
      textareaRef.current.style.height = `${nextHeight}px`;
    }
  }, [currentInput]);

  const [pendingAttachments, setPendingAttachments] = useState<Array<{ name: string; base64: string; type: string; size: number }>>([]);

  const attachFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64Content = result.includes(',') ? result.split(',')[1] : result;
      setPendingAttachments((prev) => [
        ...prev,
        {
          name: file.name || `clipboard_item_${Date.now()}.${file.type.split('/')[1] || 'png'}`,
          base64: base64Content,
          type: file.type,
          size: file.size,
        }
      ]);
    };
    reader.readAsDataURL(file);
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    let foundFile = false;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          attachFile(file);
          foundFile = true;
        }
      }
    }
    if (foundFile) {
      e.preventDefault();
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;
    for (let i = 0; i < files.length; i++) {
      attachFile(files[i]);
    }
  };

  const handleSend = (textToSend?: string) => {
    const rawInput = typeof textToSend === 'string' ? textToSend : (typeof currentInput === 'string' ? currentInput : '');
    const prompt = rawInput.trim();
    if ((!prompt && pendingAttachments.length === 0) || isStreaming) return;

    const attachmentPayload = pendingAttachments.map(a => a.base64);
    const attachmentSummary = pendingAttachments.map(a => a.name).join(', ');
    const displayPrompt = prompt || (attachmentSummary ? `Analyze attached: ${attachmentSummary}` : '');

    setCurrentInput('');
    setPendingAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    addMessage({
      id: `usr-${Date.now()}`,
      role: 'user',
      content: displayPrompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    socketManager.sendChatTask(displayPrompt, attachmentPayload, activeModelRole);
    if (typeof window !== 'undefined' && window.location.pathname === '/') {
      const currentActiveId = useChatStore.getState().activeSessionId;
      if (currentActiveId) {
        window.history.replaceState(null, '', `/chat/${currentActiveId}`);
      }
    }
    scrollToActive('smooth');
    setTimeout(() => scrollToActive('smooth'), 60);
  };

  const handleStop = () => {
    setStreaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (id: string, text: string) => {
    if (typeof navigator !== 'undefined') {
      navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleRegenerate = (msgIndex: number) => {
    useChatStore.getState().regenerateMessage(msgIndex, activeModelRole);
    scrollToActive('smooth');
    setTimeout(() => scrollToActive('smooth'), 60);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    attachFile(file);
    if (e.target) e.target.value = '';
  };

  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [showArtifactsModal, setShowArtifactsModal] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [activeModelRole, setActiveModelRole] = useState<'orchestrator' | 'code' | 'vision' | 'docs' | 'excel' | 'ppt' | 'ocr'>('orchestrator');
  const [showModelBoard, setShowModelBoard] = useState(false);
  const [activeView, setActiveView] = useState<'chat' | 'artifacts'>('chat');
  const [artifactSearchQuery, setArtifactSearchQuery] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);
  const { theme, toggleTheme } = useThemeStore();
  const cycleTheme = toggleTheme;

  const {
    deliverables,
    selectedDeliverable,
    selectDeliverable,
    downloadDeliverable,
    filterType,
    setFilterType
  } = useDeliverableStore();
  const { openCanvas, isOpen: isCanvasOpen } = useCanvasStore();

  const MODEL_ROLES = [
    { id: 'orchestrator', label: 'Auto', icon: <MasterHubIcon className="h-6 w-6" />, color: 'text-[#a8c7fa]', glow: 'shadow-blue-500/20', border: 'border-blue-400/60' },
    { id: 'code', label: 'Code', icon: <VSCodeIcon className="h-6 w-6" />, color: 'text-blue-400', glow: 'shadow-blue-500/20', border: 'border-blue-400/60' },
    { id: 'vision', label: 'Vision', icon: <VisionCamIcon className="h-6 w-6" />, color: 'text-emerald-400', glow: 'shadow-emerald-500/20', border: 'border-emerald-400/60' },
    { id: 'docs', label: 'Docs', icon: <WordDocsIcon className="h-6 w-6" />, color: 'text-blue-500', glow: 'shadow-blue-600/20', border: 'border-blue-500/60' },
    { id: 'excel', label: 'Excel', icon: <ExcelIcon className="h-6 w-6" />, color: 'text-emerald-500', glow: 'shadow-emerald-600/20', border: 'border-emerald-500/60' },
    { id: 'ppt', label: 'PowerPoint', icon: <PowerPointIcon className="h-6 w-6" />, color: 'text-orange-500', glow: 'shadow-orange-600/20', border: 'border-orange-500/60' },
    { id: 'ocr', label: 'OCR', icon: <OCRIcon className="h-6 w-6" />, color: 'text-purple-400', glow: 'shadow-purple-500/20', border: 'border-purple-400/60' },
  ];


  useEffect(() => {
    initAuth();
    useDeliverableStore.getState().fetchDiskDeliverables();
  }, [initAuth]);

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthLoading, isAuthenticated, router]);

  const filteredSessions = searchQuery.trim()
    ? sessions.filter(s => s.title?.toLowerCase().includes(searchQuery.toLowerCase()) || s.messages.some(m => m.content.toLowerCase().includes(searchQuery.toLowerCase())))
    : sessions;

  if (isAuthLoading || !isAuthenticated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#070709] text-white">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-slate-400">
            {isAuthLoading ? 'Initializing Sovereign Security Context...' : 'Redirecting to Operator Login (/login)...'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen h-[100dvh] w-screen overflow-hidden bg-white text-slate-900 dark:bg-[#000000] dark:text-[#e3e3e3] font-sans antialiased selection:bg-blue-500/20 dark:selection:bg-[#4285f4]/30">
      {/* 1. Shared Modular Responsive Sidebar */}
      <AppSidebar
        onOpenSearchModal={() => setShowSearchModal(true)}
        activePage={activeView}
      />

      {/* 2. Main Window (Chat Window or In-Place Artifacts Vault) */}
      <main className="flex-1 flex flex-col h-full min-h-0 overflow-hidden relative bg-white dark:bg-black">
        {/* Dynamic Fluid Animated Aurora Glow (Gemini Atmosphere) */}
        <FluidAuroraGlow />

        {activeView === 'artifacts' ? (
          /* Dedicated In-Place Artifacts View */
          <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50 dark:bg-[#070709] relative z-10">
            {/* Top Bar Header */}
            <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-[#0c0c0e] border-b border-slate-200 dark:border-[#1f1f26] shrink-0">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setActiveView('chat')}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#181820] dark:hover:bg-[#22222c] text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-[#282834] transition-colors cursor-pointer"
                >
                  <ArrowLeft className="h-3.5 w-3.5 text-blue-600 dark:text-[#a8c7fa]" />
                  <span>Back to Chat</span>
                </button>

                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                    <FileText className="h-4 w-4 text-blue-600 dark:text-[#a8c7fa]" />
                  </div>
                  <div>
                    <h1 className="text-sm font-bold text-slate-900 dark:text-[#f1f3f4] flex items-center gap-2">
                      Artifacts & Sovereign Documents
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/30">
                        Air-Gapped Sovereign Storage
                      </span>
                    </h1>
                    <p className="text-[11px] text-slate-500 dark:text-[#8e918f]">
                      Automated Word (.docx), Excel (.xlsx), PowerPoint (.pptx), and Python (.py) deliverables
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    const target = selectedDeliverable || deliverables[0];
                    if (target) openCanvas(target);
                  }}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-[#0070f3] hover:bg-[#0060df] text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Open in Live Canvas</span>
                </button>
              </div>
            </header>

            {/* Workspace Body: Left Deliverables List + Right Detailed Document Inspector */}
            <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
              {/* Left Column: Search & Filterable Deliverables Grid */}
              <div className="w-full md:w-96 border-r border-slate-200 dark:border-[#1e1e24] bg-white dark:bg-[#09090c] flex flex-col shrink-0">
                {/* Search Input */}
                <div className="p-3 border-b border-slate-200 dark:border-[#18181e]">
                  <div className="relative">
                    <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400 dark:text-[#8e918f]" />
                    <input
                      type="text"
                      value={artifactSearchQuery}
                      onChange={(e) => setArtifactSearchQuery(e.target.value)}
                      placeholder="Search artifacts..."
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-[#121216] border border-slate-200 dark:border-[#22222a] text-slate-900 dark:text-[#e3e3e3] placeholder-slate-400 dark:placeholder-[#6e7175] focus:outline-none focus:border-blue-500 dark:focus:border-[#a8c7fa]"
                    />
                  </div>
                </div>

                {/* Category Filter Tabs */}
                <div className="flex items-center gap-1 p-2.5 border-b border-slate-200 dark:border-[#18181e] overflow-x-auto text-[11px]">
                  {(['ALL', 'docx', 'xlsx', 'pptx', 'py'] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setFilterType(t)}
                      className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                        filterType === t
                          ? 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-[#1e1f24] dark:text-[#a8c7fa] dark:border-[#3c4048]'
                          : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-[#8e918f] dark:hover:bg-[#141418] dark:hover:text-[#c4c7c5]'
                      }`}
                    >
                      {t.toUpperCase()}
                    </button>
                  ))}
                </div>

                {/* Deliverables List Area */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                  {deliverables
                    .filter((item) => {
                      const matchesType = filterType === 'ALL' || item.type === filterType;
                      const matchesSearch =
                        item.filename.toLowerCase().includes(artifactSearchQuery.toLowerCase()) ||
                        item.summary.toLowerCase().includes(artifactSearchQuery.toLowerCase()) ||
                        item.generating_model.toLowerCase().includes(artifactSearchQuery.toLowerCase());
                      return matchesType && matchesSearch;
                    })
                    .map((item) => {
                      const activeItem = selectedDeliverable || deliverables[0];
                      const isSelected = activeItem?.id === item.id;
                      return (
                        <button
                          key={item.id}
                          onClick={() => selectDeliverable(item.id)}
                          className={`w-full text-left p-3.5 rounded-2xl border transition-all flex items-start gap-3.5 cursor-pointer ${
                            isSelected
                              ? 'bg-blue-50/60 border-blue-500 shadow-md shadow-blue-500/10 dark:bg-[#15151c] dark:border-blue-500/50'
                              : 'bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300 dark:bg-[#0e0e12] dark:border-[#1c1c24] dark:hover:bg-[#131318]'
                          }`}
                        >
                          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#181820] shrink-0 mt-0.5">
                            {getFileIcon(item.type, 'h-5 w-5')}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-bold text-xs text-slate-900 dark:text-[#e3e3e3] truncate">
                              {item.filename}
                            </div>
                            <p className="text-[11px] text-slate-500 dark:text-[#8e918f] line-clamp-2 mt-0.5 leading-relaxed">
                              {item.summary}
                            </p>
                            <div className="flex items-center gap-2 text-[10px] text-slate-400 dark:text-[#6e7175] mt-2 font-mono">
                              <span className={`px-1.5 py-0.5 rounded font-sans uppercase font-bold ${getBadgeColor(item.type)}`}>
                                {item.type}
                              </span>
                              <span>{item.size_formatted}</span>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                </div>
              </div>

              {/* Right Column: Detailed Inspector & Actions */}
              {(() => {
                const activeItem = selectedDeliverable || deliverables[0];
                if (!activeItem) return null;
                return (
                  <div className="flex-1 bg-slate-50/50 dark:bg-[#0b0b0e] flex flex-col min-h-0 overflow-y-auto p-6 sm:p-8 space-y-6">
                    {/* Document Header & Main Action Bar */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-[#1e1e26]">
                      <div className="flex items-start gap-4">
                        <div className="p-4 rounded-2xl bg-white dark:bg-[#14141a] border border-slate-200 dark:border-[#262634] shrink-0 shadow-xs">
                          {getFileIcon(activeItem.type, 'h-8 w-8')}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h2 className="text-lg font-extrabold text-slate-900 dark:text-[#f1f3f4] break-all">
                              {activeItem.filename}
                            </h2>
                            <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-md border ${getBadgeColor(activeItem.type)}`}>
                              .{activeItem.type}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 dark:text-[#8e918f] mt-1">
                            Generated by <span className="text-blue-600 dark:text-[#a8c7fa] font-bold">{activeItem.generating_model}</span> &bull; {activeItem.size_formatted}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0">
                        <button
                          onClick={() => openCanvas(activeItem)}
                          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-[#0070f3] hover:bg-[#0060df] text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
                        >
                          <Sparkles className="h-4 w-4" />
                          <span>Open & Edit Live</span>
                        </button>

                        <button
                          onClick={() => downloadDeliverable(activeItem.id)}
                          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-100 dark:bg-[#1c1c24] dark:hover:bg-[#252530] border border-slate-200 dark:border-[#2e2e3e] text-slate-800 dark:text-[#e3e3e3] text-xs font-semibold transition-all cursor-pointer"
                        >
                          <Download className="h-4 w-4 text-blue-600 dark:text-[#a8c7fa]" />
                          <span>Download</span>
                        </button>
                      </div>
                    </div>

                    {/* Summary Description */}
                    <div className="p-5 rounded-2xl bg-[#111116] border border-[#20202a]">
                      <h3 className="text-xs font-semibold text-[#8e918f] uppercase tracking-wider mb-2">
                        Executive Document Summary
                      </h3>
                      <p className="text-xs sm:text-sm text-[#d0d3d6] leading-relaxed">
                        {activeItem.summary}
                      </p>
                    </div>

                    {/* Key Quantitative Metrics Grid */}
                    {activeItem.key_metrics && activeItem.key_metrics.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold text-[#8e918f] uppercase tracking-wider mb-3">
                          Key Performance Metrics & Parameters
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                          {activeItem.key_metrics.map((metric, idx) => (
                            <div
                              key={idx}
                              className="p-4 rounded-xl bg-[#111116] border border-[#20202a] flex flex-col justify-between"
                            >
                              <span className="text-[11px] text-[#8e918f] leading-tight mb-1">
                                {metric.label}
                              </span>
                              <span className="text-base sm:text-lg font-bold text-[#f1f3f4] font-mono">
                                {metric.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Regulatory SOP Citations */}
                    {activeItem.sop_citations && activeItem.sop_citations.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold text-[#8e918f] uppercase tracking-wider mb-3">
                          Referenced SOPs & Industry Standards
                        </h3>
                        <div className="space-y-2">
                          {activeItem.sop_citations.map((cite, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-xl bg-[#111116] border border-[#20202a] flex items-center justify-between text-xs text-[#c4c7c5]"
                            >
                              <div className="flex items-center space-x-2">
                                <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
                                <span>{cite}</span>
                              </div>
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                VERIFIED
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Air-Gapped Cryptographic Signature */}
                    <div className="p-4 rounded-2xl bg-[#0e0e12] border border-[#1e1e26] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2 text-[#8e918f]">
                          <ShieldCheck className="h-4 w-4 text-emerald-400" />
                          <span>SHA-256 Air-Gapped Signature</span>
                        </div>
                        <div className="font-mono text-[11px] text-[#a8c7fa] break-all">
                          {activeItem.sha256_hash}
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(activeItem.sha256_hash);
                          setCopiedHash(true);
                          setTimeout(() => setCopiedHash(false), 2000);
                        }}
                        className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-[#181820] hover:bg-[#22222c] border border-[#2a2a38] text-[#c4c7c5] hover:text-white shrink-0 self-start sm:self-auto transition-colors"
                      >
                        {copiedHash ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                        <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
                      </button>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        ) : (
          /* Conversational Chat View */
          <>
            {/* Mobile Top Navigation Header (Visible only on < md screens) */}
            <header className="md:hidden flex items-center justify-between px-3 py-2.5 bg-white/95 border-b border-slate-200 text-slate-900 dark:bg-[#080808]/95 dark:border-[#1a1a1a] dark:text-[#e3e3e3] backdrop-blur-xl z-30 shrink-0 shadow-xs">
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleSidebar}
                  aria-label="Open sidebar"
                  className="h-10 w-10 rounded-full hover:bg-slate-100 dark:hover:bg-[#1e1f20] active:bg-slate-200 dark:active:bg-[#282a2c] flex items-center justify-center text-slate-700 dark:text-[#c4c7c5] hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                    <line x1="4" x2="20" y1="12" y2="12" />
                    <line x1="4" x2="20" y1="6" y2="6" />
                    <line x1="4" x2="20" y1="18" y2="18" />
                  </svg>
                </button>
                <RevealBrand size="sm" />
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={cycleTheme}
                  aria-label="Toggle theme"
                  className="h-9 w-9 rounded-full hover:bg-slate-100 dark:hover:bg-[#1e1f20] active:bg-slate-200 text-slate-600 dark:text-[#c4c7c5] flex items-center justify-center transition-colors cursor-pointer"
                >
                  {theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-blue-600" />}
                </button>
                <button
                  onClick={async () => {
                    const newId = await createNewChat(user?.username || 'operator');
                    router.push(`/chat/${newId}`);
                  }}
                  aria-label="New chat"
                  className="h-9 w-9 rounded-full bg-blue-50 hover:bg-blue-100 active:scale-95 border border-blue-200 text-blue-700 dark:bg-[#1e1f20] dark:hover:bg-[#282a2c] dark:border-[#3c4043]/40 dark:text-[#a8c7fa] flex items-center justify-center transition-all shadow-xs cursor-pointer"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </header>

            {/* Conversational Scroll Area */}
            <div ref={scrollContainerRef} className={`flex-1 min-h-0 px-3 sm:px-6 pt-2 pb-2 flex flex-col z-10 ${hasMessages ? 'overflow-y-auto' : 'overflow-hidden'}`}>
              {hasMessages ? (
                <div className="max-w-3xl w-full mx-auto space-y-5 sm:space-y-6 py-3 sm:py-4">
                  {messages.map((msg, idx) => {
                    const isUser = msg.role === 'user';
                    const isLastUser = isUser && (idx === messages.length - 1 || idx === messages.length - 2);
                    const isThisMsgRegenerating = !isUser && isStreaming && msg.id === regeneratingMsgId;

                    return (
                      <motion.div
                        key={msg.id}
                        ref={isLastUser ? lastUserMsgRef : undefined}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.25, ease: [0.2, 0, 0, 1] }}
                        className={`w-full flex gap-2.5 sm:gap-4 ${
                          isUser ? 'justify-end' : 'justify-start'
                        }`}
                      >
                        {!isUser && (
                          <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-blue-50 border border-blue-200 dark:bg-[#1e1f20] dark:border-[#a8c7fa]/30 flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                            <RevealLogoIcon className="h-4 w-4 sm:h-4.5 sm:w-4.5" animated={isThisMsgRegenerating} />
                          </div>
                        )}

                        {isThisMsgRegenerating ? (
                          <div className="flex flex-col space-y-2 max-w-[88%] sm:max-w-3xl flex-1 min-w-0">
                            <PerplexityReasoningAccordion
                              steps={
                                activeTraceSteps.length > 0
                                  ? activeTraceSteps
                                  : [{ id: 'init-step', content: 'Reworking parameters & retrieving operational context...', type: 'thought', duration_ms: 20 }]
                              }
                              isStreaming={true}
                            />
                          </div>
                        ) : (
                          <div className={`flex flex-col space-y-1.5 max-w-[88%] sm:max-w-3xl ${
                            isUser ? 'items-end' : 'items-start flex-1 min-w-0'
                          }`}>
                            {/* Reasoning/Thinking Accordion */}
                            {!isUser && msg.trace_steps && msg.trace_steps.length > 0 && (
                              <PerplexityReasoningAccordion steps={msg.trace_steps} isStreaming={false} />
                            )}

                            {/* Message Body Bubble / Gemini Card Container */}
                            {isUser ? (
                              <div className="px-4 py-3 rounded-2xl sm:rounded-3xl bg-slate-100/90 text-slate-900 border border-slate-200/90 shadow-2xs dark:bg-[#1c1d22] dark:text-[#e5e7eb] dark:border-white/[0.08] text-[14.5px] sm:text-[15px] leading-relaxed whitespace-pre-wrap select-text break-words">
                                {msg.content}
                              </div>
                            ) : (
                              <div className="w-full rounded-2xl sm:rounded-3xl bg-white border border-slate-200/90 shadow-[0_2px_16px_rgba(0,0,0,0.03),0_8px_32px_rgba(0,0,0,0.03)] dark:bg-[#101116] dark:border-white/[0.08] dark:shadow-[0_4px_32px_rgba(0,0,0,0.6)] p-5 sm:p-6 transition-all relative overflow-hidden space-y-3">
                                {/* Ambient Top Glow Line */}
                                <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-transparent via-blue-500/40 to-transparent" />
                                
                                {/* Card Content with High-Grade Formatting */}
                                <MarkdownContent content={msg.content} />
                              </div>
                            )}

                            {/* Generated Deliverables Interactive Badges */}
                            {msg.deliverable_ids && msg.deliverable_ids.length > 0 && (
                              <div className="pt-2 flex flex-wrap gap-2 w-full">
                                {msg.deliverable_ids.map((deliv) => {
                                  const cleanId = deliv.replace(/^\/api\/files\/(download\/)?/, '').trim();
                                  const matchedDeliv = deliverables.find(
                                    (d) => d.id === cleanId || d.filename.toLowerCase() === cleanId.toLowerCase()
                                  );
                                  const displayName = matchedDeliv?.filename || (cleanId.includes('.') ? cleanId : `${cleanId}.docx`);
                                  const downloadUrl = `/api/files/${cleanId}`;

                                  return (
                                    <div
                                      key={deliv}
                                      className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-xs text-slate-900 font-medium transition-all group shadow-xs dark:bg-[#121215] dark:hover:bg-[#19191e] dark:border-[#2a2a32] dark:text-[#e3e3e3] w-full sm:w-auto"
                                    >
                                      <button
                                        onClick={() => openCanvas(matchedDeliv || deliv)}
                                        className="flex items-center space-x-2 text-left truncate flex-1 hover:text-blue-600 dark:hover:text-[#a8c7fa] transition-colors cursor-pointer"
                                        title="Open & Edit Live in Interactive Workspace"
                                      >
                                        <Sparkles className="h-4 w-4 text-blue-600 dark:text-[#a8c7fa] shrink-0" />
                                        <span className="truncate max-w-[200px] font-bold">{displayName}</span>
                                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-50 text-blue-700 border border-blue-200 dark:bg-[#1c2230] dark:text-[#a8c7fa] dark:border-[#2f3d5a]">
                                          Edit Live
                                        </span>
                                      </button>
                                      <a
                                        href={downloadUrl}
                                        download
                                        title={`Download ${displayName}`}
                                        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-[#282834] text-slate-400 dark:text-[#8e918f] hover:text-slate-800 dark:hover:text-[#e3e3e3] transition-colors ml-1"
                                      >
                                        <Download className="h-3.5 w-3.5" />
                                      </a>
                                    </div>
                                  );
                                })}
                              </div>
                            )}

                            {/* Action Bar (Copy & Metadata Action Bar) */}
                            {!isUser && msg.content && (
                              <div className="flex items-center w-full pt-1 text-slate-400 dark:text-[#8e918f]">
                                <div className="flex items-center space-x-1">
                                  <button
                                    onClick={() => handleCopy(msg.id, msg.content)}
                                    aria-label="Copy response"
                                    className="h-7 w-7 rounded-lg hover:bg-slate-100 dark:hover:bg-white/[0.06] active:bg-slate-200 dark:active:bg-white/[0.1] flex items-center justify-center text-slate-500 dark:text-[#9aa0a6] hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
                                    title="Copy response"
                                  >
                                    {copiedId === msg.id ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                                  </button>

                                  <button
                                    onClick={() => handleRegenerate(idx)}
                                    disabled={isStreaming}
                                    aria-label="Redo / Regenerate response"
                                    className="h-7 w-7 rounded-lg hover:bg-slate-100 dark:hover:bg-white/[0.06] active:bg-slate-200 dark:active:bg-white/[0.1] flex items-center justify-center text-slate-500 dark:text-[#9aa0a6] hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer disabled:opacity-40"
                                    title="Redo / Regenerate response"
                                  >
                                    <RotateCcw className="h-3.5 w-3.5" />
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {isUser && (
                          <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-slate-100 border border-slate-300 dark:bg-[#282a2c] dark:border-[#3c4043] flex items-center justify-center shrink-0 text-slate-700 dark:text-[#e3e3e3] shadow-xs mt-0.5">
                            <User className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                          </div>
                        )}
                      </motion.div>
                    );
                  })}

                  {/* Streaming Indicator & Real-Time Thoughts (For New Messages at Bottom) */}
                  {isStreaming && !regeneratingMsgId && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                      className="w-full flex gap-2.5 sm:gap-4 justify-start"
                    >
                      <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-blue-50 border border-blue-200 dark:bg-[#1e1f20] dark:border-[#a8c7fa]/30 flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                        <RevealLogoIcon className="h-4 w-4 sm:h-4.5 sm:w-4.5" animated={true} />
                      </div>

                      <div className="flex flex-col space-y-2 max-w-[88%] sm:max-w-3xl flex-1 min-w-0">
                        <PerplexityReasoningAccordion
                          steps={
                            activeTraceSteps.length > 0
                              ? activeTraceSteps
                              : [{ id: 'init-step', content: 'Analyzing parameters & retrieving operational context...', type: 'thought', duration_ms: 20 }]
                          }
                          isStreaming={true}
                        />
                      </div>
                    </motion.div>
                  )}

              <div ref={bottomRef} className="h-4" />
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center max-w-3xl mx-auto px-4 text-center space-y-3 sm:space-y-6 w-full my-auto">
              <div className="space-y-2.5 sm:space-y-4 flex flex-col items-center">
                {/* REVEAL 2.0 Radiant Logo Icon */}
                <RevealLogoIcon className="h-12 w-12 sm:h-20 sm:w-20 mb-0.5 sm:mb-1" animated={true} />

                {/* Multicolored Gradient Heading */}
                <h1 className="text-2xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-[#4285f4] dark:via-[#9b72cf] dark:to-[#d96570] bg-clip-text text-transparent">
                  Hello, Operations Engineer
                </h1>
                <p className="text-xs sm:text-lg font-medium text-slate-500 dark:text-[#8e918f] tracking-tight max-w-md">
                  REVEAL 2.0 Sovereign Intelligence Platform is ready to assist.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 3. Authentic Single-Line Gemini Pill Input Dock with Integrated Model Board */}
        <div className="max-w-4xl mx-auto w-full px-3 sm:px-4 pt-1 z-20 shrink-0 pb-36 sm:pb-5 relative">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
          />

          {/* Model Selection Board Popover Menu - Ultra-Compact, Mobile-Scrollable & Premium */}
          <AnimatePresence>
            {showModelBoard && (
              <>
                {/* Backdrop to dismiss Model Board on outside click */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowModelBoard(false)}
                />
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.96 }}
                  transition={{ duration: 0.18, ease: [0.2, 0, 0, 1] }}
                  className="absolute bottom-full left-0 right-0 mb-2 max-w-2xl mx-auto px-2 sm:px-3 py-2 bg-white/95 dark:bg-[#0c0c0e]/95 border border-slate-200 dark:border-[#1e1e22] rounded-[22px] shadow-2xl z-50 backdrop-blur-xl"
                >
                  {/* 7-Engine Role Grid — vertical on mobile, horizontal on desktop */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-1.5 px-1 py-0.5 max-h-[60vh] sm:max-h-none overflow-y-auto sm:overflow-x-auto sm:scrollbar-none">
                    {MODEL_ROLES.map((role) => {
                      const isSelected = activeModelRole === role.id;
                      return (
                        <button
                          key={role.id}
                          type="button"
                          onClick={() => {
                            setActiveModelRole(role.id as any);
                            setShowModelBoard(false);
                          }}
                          className={`group relative flex items-center space-x-3 sm:flex-col sm:items-center sm:space-x-0 py-2 px-3 sm:py-1.5 sm:px-2.5 rounded-xl transition-all duration-200 shrink-0 min-h-[44px] ${
                            isSelected
                              ? 'bg-blue-50 border border-blue-200 text-blue-700 shadow-xs dark:bg-white/[0.08] dark:border-white/15 dark:text-white cursor-pointer'
                              : 'hover:bg-slate-100 dark:hover:bg-white/[0.03] active:bg-slate-200 dark:active:bg-white/[0.06] border border-transparent opacity-80 hover:opacity-100 hover:scale-105 active:scale-95 cursor-pointer'
                          }`}
                        >
                          {/* Glowing 3D Logo */}
                          <div className="relative mb-0 sm:mb-1 transition-transform duration-200 group-hover:scale-110 filter drop-shadow">
                            <div className="scale-90 origin-center">
                              {role.icon}
                            </div>
                          </div>

                          {/* Role Title */}
                          <div className={`text-xs sm:text-[11px] tracking-tight whitespace-nowrap transition-colors ${
                            isSelected ? 'font-bold text-blue-700 dark:text-white' : 'font-medium text-slate-600 dark:text-[#8e918f] group-hover:text-slate-900 dark:group-hover:text-[#e3e3e3]'
                          }`}>
                            {role.label}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Authentic Gemini/Claude Stacked Pill Container */}
          <div 
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="relative flex flex-col bg-white border border-slate-300 focus-within:border-blue-500 shadow-lg dark:bg-[#0d0d0e] dark:border-[#222225] dark:focus-within:border-[#38383e] dark:shadow-[0_8px_32px_rgba(0,0,0,0.8)] rounded-[24px] sm:rounded-[28px] p-2.5 sm:p-3 transition-all duration-200 z-30"
          >
            {/* Pending Attachments Chip Preview Tray */}
            {pendingAttachments.length > 0 && (
              <div className="flex flex-wrap gap-2 px-2 pt-1 pb-2 border-b border-slate-100 dark:border-white/[0.06] mb-1.5">
                {pendingAttachments.map((att, idx) => (
                  <div
                    key={idx}
                    className="flex items-center space-x-2 pl-2.5 pr-1.5 py-1 rounded-xl bg-blue-50 border border-blue-200 dark:bg-blue-500/10 dark:border-blue-500/20 text-xs text-blue-900 dark:text-blue-300 shadow-2xs group"
                  >
                    <div className="h-4 w-4 rounded flex items-center justify-center shrink-0">
                      {att.type.startsWith('image/') ? (
                        <ImageIcon className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                      ) : (
                        <FileText className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                      )}
                    </div>
                    <span className="font-medium text-[11px] truncate max-w-[140px]" title={att.name}>
                      {att.name}
                    </span>
                    <span className="text-[10px] opacity-60 font-mono">
                      {(att.size / 1024).toFixed(0)}KB
                    </span>
                    <button
                      type="button"
                      onClick={() => setPendingAttachments(prev => prev.filter((_, i) => i !== idx))}
                      className="h-4 w-4 rounded-full hover:bg-blue-200/60 dark:hover:bg-white/10 flex items-center justify-center text-blue-700 dark:text-blue-300 transition-colors"
                      title="Remove attachment"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Top Tier: Growing Textarea Area */}
            <div className="relative w-full px-1 pt-0.5 pb-1 sm:pb-2 flex items-center">
              {/* Animated Voice Waves Visualizer when listening and input is empty */}
              {isListening && !currentInput.trim() && (
                <div className="absolute inset-y-0 left-2 flex items-center pointer-events-none space-x-1.5">
                  <div className="flex items-center space-x-1 h-5 px-0.5">
                    {[0.3, 0.8, 0.45, 1.0, 0.65, 0.25, 0.85, 0.5, 0.9, 0.35].map((delay, idx) => (
                      <motion.span
                        key={idx}
                        animate={{
                          scaleY: [0.2, 1.4, 0.35, 1.1, 0.2],
                          opacity: [0.5, 1, 0.6, 1, 0.5]
                        }}
                        transition={{
                          duration: 0.75 + (idx % 3) * 0.18,
                          repeat: Infinity,
                          ease: "easeInOut",
                          delay: delay * 0.25
                        }}
                        className="w-[3px] h-4 rounded-full bg-gradient-to-t from-blue-600 via-indigo-500 to-cyan-400 dark:from-blue-500 dark:via-indigo-400 dark:to-cyan-300 origin-center"
                      />
                    ))}
                  </div>
                </div>
              )}

              <textarea
                ref={textareaRef}
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onPaste={handlePaste}
                onFocus={() => {
                  setTimeout(() => {
                    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
                  }, 150);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                rows={1}
                placeholder={
                  isListening
                    ? ""
                    : pendingAttachments.length > 0
                    ? `Add instructions for ${pendingAttachments.length} attachment(s) or press Enter...`
                    : `Ask ${MODEL_ROLES.find(r => r.id === activeModelRole)?.label} or paste file / screenshot...`
                }
                className="w-full bg-transparent text-[15px] sm:text-[15px] text-slate-900 placeholder-slate-400 dark:text-[#e3e3e3] dark:placeholder-[#8e918f] outline-none font-sans resize-none leading-relaxed overflow-y-auto block min-h-[32px] max-h-[160px] sm:max-h-[200px]"
                style={{ height: '32px' }}
              />
            </div>

            {/* Bottom Tier: Fixed-Height Action & Tools Toolbar */}
            <div className="flex items-center justify-between pt-1 border-t border-transparent">
              {/* Left Toolbar Actions */}
              <div className="relative flex items-center">
                <button
                  type="button"
                  onClick={() => {
                    if (!showAttachMenu) {
                      setShowModelBoard(false);
                    }
                    setShowAttachMenu(!showAttachMenu);
                  }}
                  aria-label="Add files"
                  className={`h-10 w-10 sm:h-9 sm:w-9 rounded-full flex items-center justify-center transition-all duration-200 cursor-pointer ${
                    showAttachMenu
                      ? 'bg-slate-100 text-blue-600 dark:bg-[#1a1a1c] dark:text-[#a8c7fa] rotate-45'
                      : 'hover:bg-slate-100 active:bg-slate-200 text-slate-600 hover:text-slate-900 dark:hover:bg-[#1a1a1c] dark:active:bg-[#282a2c] dark:text-[#c4c7c5] dark:hover:text-white'
                  }`}
                >
                  <Plus className="h-[19px] w-[19px] sm:h-[18px] sm:w-[18px] stroke-[2.2] transition-transform duration-200" />
                </button>

                {/* Gemini Style Attachment Popover Menu */}
                <AnimatePresence>
                  {showAttachMenu && (
                    <>
                      {/* Backdrop to dismiss attach menu on outside click */}
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowAttachMenu(false)}
                      />
                      <motion.div
                        initial={{ opacity: 0, y: 8, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 8, scale: 0.95 }}
                        transition={{ duration: 0.18, ease: [0.2, 0, 0, 1] }}
                        className="absolute bottom-full left-0 mb-3 w-64 max-w-[calc(100vw-32px)] bg-white border border-slate-200 dark:bg-[#0d0d0e] dark:border-[#222225] rounded-2xl p-1.5 shadow-2xl z-50 backdrop-blur-xl"
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setShowAttachMenu(false);
                            fileInputRef.current?.click();
                          }}
                          className="w-full flex items-center space-x-3 px-3 py-3 rounded-xl hover:bg-slate-100 active:bg-slate-200 dark:hover:bg-[#1a1a1c] dark:active:bg-[#282a2c] text-xs text-slate-900 hover:text-blue-600 dark:text-[#e3e3e3] dark:hover:text-white transition-colors group text-left min-h-[44px] cursor-pointer"
                        >
                          <div className="h-7 w-7 rounded-lg bg-blue-50 dark:bg-[#080808] flex items-center justify-center text-blue-600 dark:text-[#a8c7fa] group-hover:scale-105 transition-transform border border-blue-200 dark:border-[#1a1a1c] shrink-0">
                            <FileText className="h-3.5 w-3.5" />
                          </div>
                          <div>
                            <div className="font-bold">Upload from device</div>
                            <div className="text-[10px] text-slate-500 dark:text-[#8e918f]">PDF, TXT, DOCX files</div>
                          </div>
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            setShowAttachMenu(false);
                            fileInputRef.current?.click();
                          }}
                          className="w-full flex items-center space-x-3 px-3 py-3 rounded-xl hover:bg-slate-100 active:bg-slate-200 dark:hover:bg-[#1a1a1c] dark:active:bg-[#282a2c] text-xs text-slate-900 hover:text-emerald-600 dark:text-[#e3e3e3] dark:hover:text-white transition-colors group text-left min-h-[44px] cursor-pointer"
                        >
                          <div className="h-7 w-7 rounded-lg bg-emerald-50 dark:bg-[#080808] flex items-center justify-center text-emerald-600 dark:text-emerald-400 group-hover:scale-105 transition-transform border border-emerald-200 dark:border-[#1a1a1c] shrink-0">
                            <Eye className="h-3.5 w-3.5" />
                          </div>
                          <div>
                            <div className="font-bold">P&ID / Schematics</div>
                            <div className="text-[10px] text-slate-500 dark:text-[#8e918f]">OCR & tag extraction</div>
                          </div>
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            setShowAttachMenu(false);
                            handleSend('Execute centrifugal pump hydraulic power verification in isolated Python sandbox.');
                          }}
                          className="w-full flex items-center space-x-3 px-3 py-3 rounded-xl hover:bg-slate-100 active:bg-slate-200 dark:hover:bg-[#1a1a1c] dark:active:bg-[#282a2c] text-xs text-slate-900 hover:text-amber-600 dark:text-[#e3e3e3] dark:hover:text-white transition-colors group text-left min-h-[44px] cursor-pointer"
                        >
                          <div className="h-7 w-7 rounded-lg bg-amber-50 dark:bg-[#080808] flex items-center justify-center text-amber-600 dark:text-amber-400 group-hover:scale-105 transition-transform border border-amber-200 dark:border-[#1a1a1c] shrink-0">
                            <Calculator className="h-3.5 w-3.5" />
                          </div>
                          <div>
                            <div className="font-bold">Engineering Sandbox</div>
                            <div className="text-[10px] text-slate-500 dark:text-[#8e918f]">Run Python calculations</div>
                          </div>
                        </button>
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>
              </div>

              {/* Right Toolbar Actions */}
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                {/* Model Role Badge Selector Pill */}
                <button
                  type="button"
                  onClick={() => {
                    if (!showModelBoard) {
                      setShowAttachMenu(false);
                    }
                    setShowModelBoard(!showModelBoard);
                  }}
                  className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-[#080808] dark:hover:bg-[#1a1a1c] dark:active:bg-[#282a2c] border border-slate-200 dark:border-[#222225] text-xs transition-all hover:scale-105 active:scale-95 shadow-xs min-h-[40px] sm:min-h-[36px] cursor-pointer"
                >
                  <div className="scale-75 origin-center">
                    {MODEL_ROLES.find(r => r.id === activeModelRole)?.icon || <MasterHubIcon className="h-4 w-4" />}
                  </div>
                  <span className="text-[11px] font-bold text-slate-800 dark:text-[#e3e3e3] capitalize hidden xs:inline">
                    {activeModelRole}
                  </span>
                  <ChevronDown className={`h-3 w-3 text-slate-500 dark:text-[#8e918f] transition-transform duration-200 ${showModelBoard ? 'rotate-180' : ''}`} />
                </button>

                {/* Speech Recognition Mic Button (No hover tooltip) */}
                <button
                  type="button"
                  onClick={toggleSpeechRecognition}
                  aria-label={isListening ? "Stop microphone" : "Use microphone"}
                  className={`h-10 w-10 sm:h-9 sm:w-9 rounded-full flex items-center justify-center transition-all duration-200 cursor-pointer ${
                    isListening
                      ? 'bg-rose-600 text-white animate-pulse shadow-md shadow-rose-600/40 ring-2 ring-rose-400'
                      : 'hover:bg-slate-100 dark:hover:bg-[#1a1a1c] active:bg-slate-200 dark:active:bg-[#282a2c] text-slate-600 hover:text-slate-900 dark:text-[#c4c7c5] dark:hover:text-white'
                  }`}
                >
                  {isListening ? (
                    <MicOff className="h-[19px] w-[19px] sm:h-[18px] sm:w-[18px] text-white" />
                  ) : (
                    <Mic className="h-[19px] w-[19px] sm:h-[18px] sm:w-[18px] text-slate-600 dark:text-[#c4c7c5]" />
                  )}
                </button>

                {/* Submit / Stop Button */}
                {isStreaming ? (
                  <button
                    onClick={handleStop}
                    className="h-10 sm:h-9 px-3.5 rounded-full bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 dark:bg-rose-500/20 dark:hover:bg-rose-500/30 dark:border-transparent dark:text-rose-300 text-xs font-bold flex items-center space-x-1.5 transition-all cursor-pointer"
                  >
                    <Square className="h-3.5 w-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleSend()}
                    disabled={!( (typeof currentInput === 'string' && currentInput.trim().length > 0) || pendingAttachments.length > 0 )}
                    aria-label="Send message"
                    className={`h-10 w-10 sm:h-9 sm:w-9 rounded-full flex items-center justify-center transition-all duration-200 shadow-sm cursor-pointer ${
                      (typeof currentInput === 'string' && currentInput.trim().length > 0) || pendingAttachments.length > 0
                        ? 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-white dark:text-black dark:hover:bg-[#f1f3f4]'
                        : 'bg-slate-100 text-slate-400 dark:bg-[#1e1f20] dark:text-[#717478]'
                    }`}
                  >
                    <ArrowUp className="h-[19px] w-[19px] sm:h-[18px] sm:w-[18px] stroke-[2.5]" />
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="text-center text-[9px] sm:text-[10px] text-slate-400 dark:text-[#8e918f] pt-1.5 sm:pt-2 font-sans px-2 leading-tight">
            REVEAL 2.0 Sovereign AI Platform operates 100% on-premise without external network egress. Verify critical engineering directives.
          </div>
        </div>
      </>
    )}

    {/* 4. Gemini / Claude-Style Interactive Document Canvas Side Panel */}
    <DocumentCanvasPanel />
  </main>

    {/* 3. Enterprise Artifacts & Deliverables Vault Modal Inspector */}
    <ArtifactsModal
      isOpen={showArtifactsModal}
      onClose={() => setShowArtifactsModal(false)}
    />

    {/* 4. Global Search Chats Command Palette Modal */}
    <SearchChatsModal
      isOpen={showSearchModal}
      onClose={() => setShowSearchModal(false)}
    />
  </div>
  );
}

