'use client';

import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, Sparkles, CheckCircle2, Clock, BrainCircuit, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TraceStep {
  id?: string;
  type?: string;
  content: string;
  duration_ms?: number;
}

interface Props {
  steps: TraceStep[];
  isStreaming?: boolean;
}

export function PerplexityReasoningAccordion({ steps, isStreaming = false }: Props) {
  const [isOpen, setIsOpen] = useState(isStreaming);

  // Filter out raw token fragments or join coherent thoughts
  const { combinedText, parsedSteps, secondsElapsed } = useMemo(() => {
    if (!steps || steps.length === 0) {
      return { combinedText: '', parsedSteps: [], secondsElapsed: 0 };
    }

    // Combine raw token chunks into unified narrative text
    const fullText = steps
      .map((s) => s.content)
      .join('')
      .replace(/<think>|<\/think>/gi, '')
      .trim();

    // Parse into distinct reasoning paragraphs / steps
    const paragraphs = fullText
      .split(/\n\s*\n+/)
      .map((p) => p.trim())
      .filter((p) => p.length > 0);

    // If text didn't have double newlines, split by sentences or keep full blocks
    const formattedSteps: string[] = [];
    if (paragraphs.length > 0) {
      paragraphs.forEach((p) => {
        // Clean markdown headers or bullet noise if any
        const cleaned = p.replace(/^[\*\-\#\d\.\s]+/, '').trim();
        if (cleaned.length > 0) {
          formattedSteps.push(p);
        }
      });
    }

    const totalMs = steps.reduce((acc, curr) => acc + (curr.duration_ms || 0), 0);
    const secs = totalMs > 0 ? Math.round(totalMs / 100) / 10 : Math.max(1, Math.round(steps.length * 0.08 * 10) / 10);

    return {
      combinedText: fullText,
      parsedSteps: formattedSteps.length > 0 ? formattedSteps : [fullText],
      secondsElapsed: secs,
    };
  }, [steps]);

  if (!steps || steps.length === 0 || !combinedText) return null;

  return (
    <div className="w-full mb-3 rounded-2xl border border-slate-200/80 bg-slate-50/70 dark:border-white/[0.08] dark:bg-[#12141c]/80 backdrop-blur-sm overflow-hidden text-xs transition-all shadow-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-slate-100/70 dark:hover:bg-white/[0.03] transition-colors cursor-pointer"
      >
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="h-5 w-5 rounded-full bg-blue-500/10 dark:bg-blue-400/15 flex items-center justify-center shrink-0 border border-blue-500/20">
            {isStreaming ? (
              <Activity className="h-3 w-3 text-blue-600 dark:text-blue-400 animate-pulse" />
            ) : (
              <BrainCircuit className="h-3 w-3 text-blue-600 dark:text-blue-400" />
            )}
          </div>
          <div className="flex items-center space-x-2 truncate">
            <span className="font-semibold text-slate-800 dark:text-slate-200 tracking-tight">
              {isStreaming ? 'Thinking Process' : `Thought for ${secondsElapsed}s`}
            </span>
            {isStreaming && (
              <span className="flex items-center space-x-1 text-[11px] text-blue-600 dark:text-blue-400 font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-600 dark:bg-blue-400 animate-ping" />
                <span className="truncate">Analyzing query & synthesizing operational reasoning...</span>
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-1.5 shrink-0 text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
          <span className="text-[11px] font-medium">{isOpen ? 'Hide' : 'View steps'}</span>
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22, ease: 'easeInOut' }}
            className="px-4 pb-3.5 pt-2 border-t border-slate-200/60 dark:border-white/[0.06] space-y-2.5 bg-white/40 dark:bg-black/20"
          >
            {parsedSteps.map((paragraph, idx) => {
              const isLast = idx === parsedSteps.length - 1;
              return (
                <div key={idx} className="flex items-start space-x-2.5 text-slate-600 dark:text-slate-300 text-[12px] leading-relaxed">
                  <div className="mt-1 shrink-0">
                    {isStreaming && isLast ? (
                      <div className="h-2.5 w-2.5 rounded-full bg-blue-500 animate-ping" />
                    ) : (
                      <div className="h-1.5 w-1.5 rounded-full bg-slate-400 dark:bg-slate-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0 font-normal select-text">
                    <p className={`whitespace-pre-wrap ${isStreaming && isLast ? 'text-slate-800 dark:text-slate-200 font-medium' : 'text-slate-600 dark:text-slate-400'}`}>
                      {paragraph}
                    </p>
                  </div>
                </div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

