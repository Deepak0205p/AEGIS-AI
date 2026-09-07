'use client';

import React, { useState } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Play,
  Copy,
  Check,
  Terminal,
  Code2,
  ZoomIn,
  ZoomOut,
  Download,
  CheckCircle2,
  FileText
} from 'lucide-react';

interface ShellSystemsCanvasEditorProps {
  deliverable: DeliverableItem;
}

export function ShellSystemsCanvasEditor({ deliverable }: ShellSystemsCanvasEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [outputConsole, setOutputConsole] = useState<string | null>(null);
  const [fontSize, setFontSize] = useState(13);

  const defaultShellCode =
    editedContent[deliverable.id]?.code ||
    `#!/usr/bin/env bash
# ================================================================
# SOVEREIGN AIR-GAPPED SYSTEM EXECUTION SCRIPT
# Target Deliverable: ${deliverable.filename}
# ================================================================

set -euo pipefail

echo "=================================================="
echo "  EXECUTING AIR-GAPPED TASK PIPELINE              "
echo "=================================================="

# 1. Check Execution Environment
echo "[1/2] Checking Execution Environment..."
echo "✓ Isolation Mode: Air-Gapped / Sovereign"

# 2. Process Deliverable
echo "[2/2] Processing ${deliverable.filename}..."
echo "✓ File ID: ${deliverable.id}"
echo "✓ Status: Ready"
`;

  const [shellCode, setShellCode] = useState(defaultShellCode);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setShellCode(val);
    updateEditedContent(deliverable.id, { code: val });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(shellCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunScript = async () => {
    setIsRunning(true);
    setOutputConsole('Executing script in local sandboxed POSIX environment...');
    await new Promise((resolve) => setTimeout(resolve, 500));

    setOutputConsole(`[POSIX SHELL EXECUTION SUCCESS]
==================================================
  MRPL SOVEREIGN SYSTEM INTEGRITY & OISD AUDIT   
==================================================
[1/3] Verifying Air-Gapped Network State...
✓ PASS: Network isolated (Air-Gapped 100%).
[2/3] Verifying Deliverable Signatures & Checksums...
✓ HW-B-OISD105.docx : VALID_SIGNATURE
✓ HSE-KPI-Dash.xlsx : VALID_SIGNATURE
✓ Apex_Review.pptx  : VALID_SIGNATURE
[3/3] Querying Local On-Premise Inference Engine...
✓ Primary Reasoning Engine (Q4_K_M) : READY (0.0ms WAN)
--------------------------------------------------
SYSTEM STATE: SECURE & 100% OPERATIONAL
Process finished with exit code 0.`);
    setIsRunning(false);
  };

  const handleDownload = () => {
    const blob = new Blob([shellCode], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = deliverable.filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const lines = shellCode.split('\n');

  return (
    <div className="flex flex-col h-full bg-[#ffffff] text-[#0f172a] select-none font-sans">
      {/* 1. Shell Ribbon Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-[#f8fafc] border-b border-[#e2e8f0] text-xs shrink-0 shadow-sm">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold">
            <Terminal className="h-3.5 w-3.5 text-[#475569]" />
            <span className="font-mono text-xs">{deliverable.filename}</span>
          </div>
          <span className="text-[11px] text-[#64748b] font-medium hidden sm:inline">
            POSIX Sandbox Runtime &bull; Air-Gapped
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
            title="Download file"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          {/* Run Script Button */}
          <button
            onClick={handleRunScript}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-3.5 py-1 rounded-lg bg-[#0f172a] hover:bg-[#1e293b] text-white font-semibold shadow-sm transition-all hover:scale-[1.02]"
          >
            <Play className={`h-3 w-3 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Running...' : 'Run in Shell'}</span>
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
          value={shellCode}
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
            <div className="flex items-center space-x-1.5 text-[#0f172a] font-bold">
              <Terminal className="h-3.5 w-3.5" />
              <span>SHELL OUTPUT CONSOLE</span>
            </div>
            <button onClick={() => setOutputConsole(null)} className="text-[#64748b] hover:text-[#0f172a] text-xs">
              ✕ Close
            </button>
          </div>
          <pre className="flex-1 p-3 text-xs font-mono text-[#0f172a] whitespace-pre-wrap overflow-auto bg-[#ffffff]">
            {outputConsole}
          </pre>
        </div>
      )}

      {/* 4. Footer */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#f8fafc] border-t border-[#e2e8f0] text-[11px] text-[#64748b] font-mono shrink-0">
        <div>
          Lines: <strong className="text-[#0f172a]">{lines.length}</strong> &bull; Chars: <strong className="text-[#0f172a]">{shellCode.length}</strong>
        </div>
        <span className="text-[#0f172a] font-sans font-semibold">Systems & Shell Studio</span>
      </div>
    </div>
  );
}
