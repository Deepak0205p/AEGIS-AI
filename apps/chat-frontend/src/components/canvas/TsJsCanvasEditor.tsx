'use client';

import React, { useState } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Play,
  Copy,
  Check,
  Code2,
  Terminal,
  ZoomIn,
  ZoomOut,
  Download,
  Sparkles,
  CheckCircle2,
  FileCode2
} from 'lucide-react';
import { runCode, formatRunReport, CodeRunResult } from '@/lib/codeRunner';

interface TsJsCanvasEditorProps {
  deliverable: DeliverableItem;
}

export function TsJsCanvasEditor({ deliverable }: TsJsCanvasEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [outputConsole, setOutputConsole] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<CodeRunResult | null>(null);
  const [fontSize, setFontSize] = useState(13);

  const defaultTsCode =
    editedContent[deliverable.id]?.code ||
    `/**
 * MRPL Real-Time Yield & Margin Calculation Engine
 * Filename: ${deliverable.filename}
 * Runtime: Node.js permission sandbox (type stripping)
 */

interface CrudeAssay {
  crudeGrade: string;
  apiGravity: number;
  sulfurPct: number;
  brentDifferentialUsd: number;
}

interface YieldResult {
  crudeGrade: string;
  grossRefiningMarginUsd: number;
  desulfurizationLoadKgPerTon: number;
  recommendedBlendSharePct: number;
  verdict: 'OPTIMAL' | 'SUB_OPTIMAL';
}

export function computeRefineryGrossMargin(assay: CrudeAssay): YieldResult {
  const baseMarginUsd = 12.45;
  const gravityBonus = (assay.apiGravity - 30.0) * 0.18;
  const sulfurPenalty = assay.sulfurPct * 0.85;
  
  const grm = baseMarginUsd + assay.brentDifferentialUsd + gravityBonus - sulfurPenalty;
  
  return {
    crudeGrade: assay.crudeGrade,
    grossRefiningMarginUsd: Number(grm.toFixed(2)),
    desulfurizationLoadKgPerTon: Number((assay.sulfurPct * 10.2).toFixed(1)),
    recommendedBlendSharePct: grm > 12.0 ? 74 : 26,
    verdict: grm > 12.0 ? 'OPTIMAL' : 'SUB_OPTIMAL'
  };
}

// Sandbox execution test
const highSulfurCrude: CrudeAssay = {
  crudeGrade: 'Arab Heavy / Maya Blend',
  apiGravity: 28.4,
  sulfurPct: 1.85,
  brentDifferentialUsd: 2.40
};

const evaluation = computeRefineryGrossMargin(highSulfurCrude);
console.log("=== MRPL YIELD ASSAY EVALUATION ===");
console.log(JSON.stringify(evaluation, null, 2));
`;

  const [tsCode, setTsCode] = useState(defaultTsCode);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setTsCode(val);
    updateEditedContent(deliverable.id, { code: val });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(tsCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunJs = async () => {
    setIsRunning(true);
    setOutputConsole('Submitting the source to the sovereign Node.js runner...');

    const language = deliverable.filename.toLowerCase().endsWith('.js') ? 'javascript' : 'typescript';
    const result = await runCode(language, tsCode, { filename: deliverable.filename });

    setLastRun(result);
    setOutputConsole(formatRunReport(result));
    setIsRunning(false);
  };

  const handleDownload = () => {
    const blob = new Blob([tsCode], { type: 'text/typescript;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = deliverable.filename.endsWith('.ts') ? deliverable.filename : `${deliverable.filename}.ts`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const lines = tsCode.split('\n');

  return (
    <div className="flex flex-col h-full bg-[#ffffff] text-[#0f172a] select-none font-sans">
      {/* 1. TS/JS Ribbon Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-[#f8fafc] border-b border-[#e2e8f0] text-xs shrink-0 shadow-sm">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-[#eff6ff] border border-[#bfdbfe] text-[#2563eb] font-semibold">
            <FileCode2 className="h-3.5 w-3.5" />
            <span className="font-mono text-xs">{deliverable.filename}</span>
          </div>
          <span className="text-[11px] text-[#64748b] font-medium hidden sm:inline" title={lastRun?.engine || 'No run yet'}>
            {lastRun ? lastRun.engine : 'Node.js permission sandbox'}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Zoom / Font Size */}
          <div className="flex items-center space-x-1 pr-2 border-r border-[#cbd5e1]">
            <button
              onClick={() => setFontSize((s) => Math.max(10, s - 1))}
              className="p-1 rounded hover:bg-[#e2e8f0] text-[#64748b]"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[11px] font-mono text-[#0f172a] font-semibold">{fontSize}px</span>
            <button
              onClick={() => setFontSize((s) => Math.min(22, s + 1))}
              className="p-1 rounded hover:bg-[#e2e8f0] text-[#64748b]"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-[#ffffff] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#334155] font-medium"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg bg-[#ffffff] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#334155]"
            title="Download .ts file"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          {/* Run TS/JS Button */}
          <button
            onClick={handleRunJs}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-3.5 py-1 rounded-lg bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-semibold shadow-sm transition-all hover:scale-[1.02]"
          >
            <Play className={`h-3 w-3 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Running...' : 'Run in Sandbox'}</span>
          </button>
        </div>
      </div>

      {/* 2. Code Area */}
      <div className="flex-1 flex overflow-hidden bg-[#ffffff]">
        <div
          style={{ fontSize: `${fontSize}px` }}
          className="w-12 bg-[#f8fafc] text-[#94a3b8] border-r border-[#e2e8f0] text-right pr-2 py-4 select-none font-mono leading-relaxed shrink-0"
        >
          {lines.map((_: string, i: number) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        <textarea
          value={tsCode}
          onChange={handleCodeChange}
          spellCheck={false}
          style={{ fontSize: `${fontSize}px` }}
          className="flex-1 h-full bg-[#ffffff] text-[#0f172a] focus:outline-none resize-none font-mono p-4 leading-relaxed overflow-auto selection:bg-[#bfdbfe]"
        />
      </div>

      {/* 3. Output Terminal Deck */}
      {outputConsole && (
        <div className="h-48 bg-[#f8fafc] border-t border-[#cbd5e1] flex flex-col shrink-0">
          <div className="flex items-center justify-between px-4 py-2 bg-[#f1f5f9] border-b border-[#e2e8f0] text-xs text-[#64748b]">
            <div className="flex items-center space-x-1.5 text-[#2563eb] font-bold">
              <Terminal className="h-3.5 w-3.5" />
              <span>SANDBOX OUTPUT (REAL EXECUTION)</span>
            </div>
            <button onClick={() => setOutputConsole(null)} className="text-[#64748b] hover:text-[#0f172a] text-xs">
              ✕ Close
            </button>
          </div>
          <pre
            className={`flex-1 p-3 text-xs font-mono whitespace-pre-wrap overflow-auto bg-[#ffffff] ${
              lastRun?.status === 'SUCCESS'
                ? 'text-[#1e293b]'
                : lastRun?.status === 'UNSUPPORTED'
                  ? 'text-amber-700'
                  : lastRun
                    ? 'text-rose-700'
                    : 'text-[#1e293b]'
            }`}
          >
            {outputConsole}
          </pre>
        </div>
      )}

      {/* 4. Footer */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#f8fafc] border-t border-[#e2e8f0] text-[11px] text-[#64748b] font-mono shrink-0">
        <div>
          Lines: <strong className="text-[#0f172a]">{lines.length}</strong> &bull; Chars: <strong className="text-[#0f172a]">{tsCode.length}</strong>
        </div>
        <span className="text-[#2563eb] font-sans font-semibold">TypeScript & JavaScript Studio</span>
      </div>
    </div>
  );
}
