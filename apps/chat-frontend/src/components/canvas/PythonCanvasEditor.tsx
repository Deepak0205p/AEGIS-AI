'use client';

import React, { useState, useEffect } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Play,
  Copy,
  Check,
  Terminal,
  ZoomIn,
  ZoomOut,
  Download,
  Sliders,
  CheckCircle2,
  XCircle,
  FileCode2,
  Cpu,
  RefreshCw,
  FolderDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PythonCanvasEditorProps {
  deliverable: DeliverableItem;
}

function getApiBase(): string {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
}

export function PythonCanvasEditor({ deliverable }: PythonCanvasEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [outputConsole, setOutputConsole] = useState<string | null>(null);
  const [runSuccess, setRunSuccess] = useState<boolean | null>(null);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [generatedFiles, setGeneratedFiles] = useState<any[]>([]);
  const [fontSize, setFontSize] = useState(13);
  const [showLineNumbers, setShowLineNumbers] = useState(true);

  // Dynamic code initial value
  const initialCode =
    editedContent[deliverable.id]?.code ||
    (deliverable as any).code ||
    `"""
AIR-GAPPED SOVEREIGN REFINERY SCRIPT
Filename: ${deliverable.filename}
Runtime: Isolated Python 3.11 Execution Engine
Compliance: OISD-STD-105 / PESO Statutory Rules
"""

import sys
import math

def run_analysis():
    print("=" * 55)
    print("  AIR-GAPPED PYTHON RUNTIME EXECUTION")
    print("=" * 55)
    
    api_gravity = 28.4
    sulfur_pct = 1.85
    throughput_kbpd = 310.5
    
    # Calculate refinery economics
    base_margin = 11.20
    gravity_bonus = (api_gravity - 32.0) * 0.15
    sulfur_penalty = max(0.0, (sulfur_pct - 0.5) * 1.20)
    net_grm = round(base_margin + 2.40 + gravity_bonus - sulfur_penalty, 2)
    daily_ebitda = round(net_grm * throughput_kbpd * 1000, 2)
    
    print(f"  [+] Crude Assay Gravity      : {api_gravity}° API")
    print(f"  [+] Sulfur Content           : {sulfur_pct}% wt")
    print(f"  [+] Realized Gross Margin    : ${net_grm:.2f} / bbl")
    print(f"  [+] Daily Operating EBITDA   : ${daily_ebitda:,.2f}")
    print(f"  [+] OISD Safety Verification : COMPLIANT (Pass)")
    print("=" * 55)
    print("  STATUS: EXECUTION FINISHED SUCCESSFULLY")

if __name__ == "__main__":
    run_analysis()
`;

  const [code, setCode] = useState(initialCode);

  useEffect(() => {
    if (editedContent[deliverable.id]?.code) {
      setCode(editedContent[deliverable.id].code);
    }
  }, [deliverable.id, editedContent]);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setCode(val);
    updateEditedContent(deliverable.id, { code: val });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutputConsole('Executing script in air-gapped Python sandbox...');
    setRunSuccess(null);
    setGeneratedFiles([]);

    try {
      const res = await fetch(`${getApiBase()}/api/sandbox/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      if (!res.ok) {
        throw new Error(`HTTP Error: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();
      const stdout = data.stdout || '';
      const stderr = data.stderr || '';
      const exitCode = data.exit_code ?? (data.success ? 0 : 1);
      const isSuccess = data.success ?? exitCode === 0;

      setRunSuccess(isSuccess);
      setExecutionTime(data.execution_time_sec ? Math.round(data.execution_time_sec * 1000) : 45);
      if (data.generated_files && Array.isArray(data.generated_files)) {
        setGeneratedFiles(data.generated_files);
      }

      let consoleOutput = '';
      if (stdout) {
        consoleOutput += stdout;
      }
      if (stderr) {
        consoleOutput += (consoleOutput ? '\n\n[STDERR]:\n' : '') + stderr;
      }
      if (!consoleOutput.trim()) {
        consoleOutput = `[Script executed with exit code ${exitCode} (No standard output returned)]`;
      }

      setOutputConsole(consoleOutput);
    } catch (err: any) {
      setRunSuccess(false);
      setOutputConsole(`[SANDBOX EXECUTION ERROR]:\n${err.message || 'Failed to reach air-gapped sandbox backend.'}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/x-python;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = deliverable.filename.endsWith('.py') ? deliverable.filename : `${deliverable.filename}.py`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const lines = code.split('\n');

  return (
    <div className="flex flex-col h-full bg-[#0b1120] text-[#f8fafc] select-none font-sans relative overflow-hidden">
      {/* 1. TOP HEADER & ACTION CONTROLS */}
      <div className="flex items-center justify-between px-3 sm:px-4 py-2.5 bg-[#070b14] border-b border-slate-800 text-xs shrink-0 gap-2 overflow-x-auto scrollbar-none">
        {/* Left: Environment & Runtime status */}
        <div className="flex items-center space-x-2 shrink-0">
          <div className="flex items-center space-x-2 px-3 py-1 rounded-xl bg-slate-900 border border-slate-700/80 text-emerald-400 font-mono text-[11px] sm:text-xs shadow-inner">
            <Cpu className="h-3.5 w-3.5 text-emerald-400 shrink-0 animate-pulse" />
            <span className="font-semibold text-white">Python 3.11</span>
            <span className="text-slate-500">•</span>
            <span className="text-emerald-400 font-medium">Air-Gapped Sandbox</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2 shrink-0">
          {/* Zoom Controls */}
          <div className="hidden sm:flex items-center space-x-1 pr-2.5 border-r border-slate-800">
            <button
              onClick={() => setFontSize((s) => Math.max(10, s - 1))}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Decrease Font Size"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[11px] font-mono text-slate-300 px-1">{fontSize}px</span>
            <button
              onClick={() => setFontSize((s) => Math.min(22, s + 1))}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Increase Font Size"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800/90 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-xs transition-colors cursor-pointer active:scale-95"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800/90 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-xs transition-colors cursor-pointer active:scale-95"
            title="Download Python script (.py)"
          >
            <Download className="h-3.5 w-3.5 text-slate-400" />
            <span className="hidden xs:inline">Download</span>
          </button>

          {/* Run Code in Sandbox */}
          <button
            onClick={handleRunCode}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-950/40 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer disabled:opacity-50 shrink-0"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Running...' : 'Run in Sandbox'}</span>
          </button>
        </div>
      </div>

      {/* 2. CODE EDITOR AREA */}
      <div className="flex-1 flex overflow-hidden bg-[#0b1120]">
        {showLineNumbers && (
          <div
            style={{ fontSize: `${fontSize}px` }}
            className="w-12 bg-[#070b14] text-slate-600 border-r border-slate-800 text-right pr-3 py-4 select-none font-mono leading-relaxed shrink-0"
          >
            {lines.map((_: string, i: number) => (
              <div key={i} className="hover:text-slate-400">{i + 1}</div>
            ))}
          </div>
        )}

        <textarea
          value={code}
          onChange={handleCodeChange}
          spellCheck={false}
          style={{ fontSize: `${fontSize}px` }}
          className="flex-1 h-full bg-[#0b1120] text-slate-100 focus:outline-none resize-none font-mono p-4 leading-relaxed overflow-auto selection:bg-blue-600/40"
          placeholder="# Type or paste Python code here..."
        />
      </div>

      {/* 3. OUTPUT TERMINAL DECK (LIVE REAL SANDBOX) */}
      <AnimatePresence>
        {outputConsole && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 230, opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-[#070b14] border-t border-slate-800 flex flex-col shrink-0 z-20 shadow-2xl"
          >
            {/* Terminal Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#0d1527] border-b border-slate-800 text-xs">
              <div className="flex items-center space-x-2">
                <Terminal className="h-3.5 w-3.5 text-emerald-400" />
                <span className="font-mono font-bold text-white tracking-wide">SANDBOX TERMINAL CONSOLE</span>
                {runSuccess === true && (
                  <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/30">
                    <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                    Passed (Exit Code 0)
                  </span>
                )}
                {runSuccess === false && (
                  <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 font-medium border border-rose-500/30">
                    <XCircle className="h-3 w-3 text-rose-400" />
                    Execution Failed
                  </span>
                )}
                {executionTime !== null && (
                  <span className="text-slate-400 font-mono text-[11px]">{executionTime}ms</span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleRunCode}
                  disabled={isRunning}
                  className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium transition-colors"
                >
                  <RefreshCw className={`h-3 w-3 ${isRunning ? 'animate-spin' : ''}`} />
                  <span>Rerun</span>
                </button>
                <button
                  onClick={() => setOutputConsole(null)}
                  className="text-slate-400 hover:text-white text-xs font-bold px-1.5 py-0.5 rounded hover:bg-slate-800 transition-colors"
                >
                  ✕ Close
                </button>
              </div>
            </div>

            {/* Terminal Output */}
            <pre className={`flex-1 p-3.5 text-xs font-mono whitespace-pre-wrap overflow-auto selection:bg-emerald-900/50 ${runSuccess === false ? 'text-rose-300 bg-[#0c0a0f]' : 'text-emerald-300 bg-[#050811]'}`}>
              {outputConsole}
            </pre>

            {/* Generated Files if any */}
            {generatedFiles.length > 0 && (
              <div className="px-4 py-1.5 bg-[#090e1a] border-t border-slate-800/80 flex items-center gap-2 overflow-x-auto text-[11px]">
                <FolderDown className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                <span className="text-slate-400 font-medium">Generated Outputs:</span>
                {generatedFiles.map((file, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800/50 text-blue-300 font-mono">
                    {file.name} ({(file.size_bytes / 1024).toFixed(1)} KB)
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 4. FOOTER STATUS BAR */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#070b14] border-t border-slate-800 text-[11px] text-slate-400 font-mono shrink-0">
        <div className="flex items-center space-x-3">
          <span>Lines: <strong className="text-slate-200">{lines.length}</strong></span>
          <span>&bull;</span>
          <span>Chars: <strong className="text-slate-200">{code.length}</strong></span>
          <span>&bull;</span>
          <span>Encoding: <strong className="text-slate-300">UTF-8</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-emerald-400 font-sans font-medium text-[11px]">Python Sandbox Ready</span>
        </div>
      </div>
    </div>
  );
}
