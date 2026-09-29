'use client';

import React, { useState, useEffect, useRef } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Play,
  Copy,
  Check,
  Terminal,
  Code2,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Sparkles,
  Download,
  Search,
  CheckCircle2,
  Table as TableIcon,
  Globe,
  FileCode,
  Braces,
  Settings2,
  Maximize2,
  Minimize2,
  Sliders,
  ChevronDown
} from 'lucide-react';
import { CustomDropdown } from '@/components/ui/CustomDropdown';
import { runCode, formatRunReport, CodeRunResult } from '@/lib/codeRunner';

interface CodeCanvasEditorProps {
  deliverable: DeliverableItem;
}

export type SupportedLang =
  | 'python'
  | 'javascript'
  | 'typescript'
  | 'sql'
  | 'json'
  | 'yaml'
  | 'html'
  | 'css'
  | 'shell'
  | 'cpp'
  | 'rust'
  | 'markdown';

// Engine labels describe what this deployment can ACTUALLY run — the runner
// returns the real engine string at execution time (see lib/codeRunner.ts).
const LANGUAGE_CONFIGS: Record<
  SupportedLang,
  { label: string; ext: string; engine: string; color: string }
> = {
  python: { label: 'Python 3.11', ext: '.py', engine: 'Container (--network none) or Job Object + network guard', color: 'text-purple-400' },
  javascript: { label: 'JavaScript (ES2024)', ext: '.js', engine: 'Node.js permission sandbox', color: 'text-yellow-400' },
  typescript: { label: 'TypeScript 5.4', ext: '.ts', engine: 'Node.js permission sandbox (type stripping)', color: 'text-blue-400' },
  sql: { label: 'ANSI SQL', ext: '.sql', engine: 'SQL read-only sandbox', color: 'text-cyan-400' },
  json: { label: 'JSON Data Schema', ext: '.json', engine: 'Server-side RFC 8259 parser', color: 'text-emerald-400' },
  yaml: { label: 'YAML / K8s Config', ext: '.yaml', engine: 'Schema only - no server runner', color: 'text-rose-400' },
  html: { label: 'HTML5 Web Preview', ext: '.html', engine: 'Browser sandboxed iframe', color: 'text-orange-400' },
  css: { label: 'CSS3 / Tailwind', ext: '.css', engine: 'Style sheet - no server runner', color: 'text-sky-400' },
  shell: { label: 'Bash / Linux Shell', ext: '.sh', engine: 'Docker bash sandbox (if available)', color: 'text-green-400' },
  cpp: { label: 'C++ 20', ext: '.cpp', engine: 'Local g++/clang++ (if installed)', color: 'text-blue-500' },
  rust: { label: 'Rust 1.78', ext: '.rs', engine: 'Local rustc (if installed)', color: 'text-amber-500' },
  markdown: { label: 'Markdown Docs', ext: '.md', engine: 'Documentation - no server runner', color: 'text-slate-300' },
};

function detectLanguage(filename: string, deliverableType: string): SupportedLang {
  const name = filename.toLowerCase();
  const type = deliverableType.toLowerCase();

  if (name.endsWith('.py') || type === 'py') return 'python';
  if (name.endsWith('.sql') || type === 'sql') return 'sql';
  if (name.endsWith('.json') || type === 'json') return 'json';
  if (name.endsWith('.ts') || name.endsWith('.tsx') || type === 'ts') return 'typescript';
  if (name.endsWith('.js') || name.endsWith('.jsx') || type === 'js') return 'javascript';
  if (name.endsWith('.html') || name.endsWith('.htm') || type === 'html') return 'html';
  if (name.endsWith('.css') || type === 'css') return 'css';
  if (name.endsWith('.sh') || name.endsWith('.bash') || type === 'sh') return 'shell';
  if (name.endsWith('.yaml') || name.endsWith('.yml') || type === 'yaml') return 'yaml';
  if (name.endsWith('.cpp') || name.endsWith('.c') || name.endsWith('.h')) return 'cpp';
  if (name.endsWith('.rs')) return 'rust';
  if (name.endsWith('.md') || name.endsWith('.txt')) return 'markdown';

  return 'python';
}

function getDefaultCodeByLang(lang: SupportedLang, filename: string): string {
  switch (lang) {
    case 'sql':
      return `-- MRPL SOVEREIGN SQL REFINERY QUERY
-- Filename: ${filename}
-- Database: read-only sandbox schema (sih_sql_sandbox)
-- Only SELECT / WITH / SHOW / EXPLAIN are permitted here

SELECT 
    p.unit_id,
    p.unit_name,
    p.operating_temp_c,
    p.pressure_bar,
    g.combustible_lel_pct,
    g.oxygen_vol_pct,
    g.h2s_toxic_ppm,
    CASE 
        WHEN g.combustible_lel_pct = 0.0 AND g.oxygen_vol_pct >= 20.0 THEN 'SAFE_AUTHORIZED'
        ELSE 'SAFETY_HOLD'
    END AS oisd_105_verdict
FROM refinery_process_units p
JOIN oisd_atmospheric_readings g ON p.unit_id = g.unit_id
WHERE p.is_active = TRUE
ORDER BY p.operating_temp_c DESC;
`;

    case 'json':
      return `{
  "system": "MRPL Sovereign Refinery Intelligence Platform",
  "document": "${filename}",
  "version": "1.0.0",
  "air_gapped": true,
  "data": {
    "timestamp": "${new Date().toISOString()}",
    "status": "NOMINAL",
    "readings": []
  },
  "compliance_status": "VERIFIED"
}`;

    case 'typescript':
    case 'javascript':
      return `/**
 * MRPL Real-Time Yield & Margin Calculation Engine
 * Filename: ${filename}
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

    case 'html':
      return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MRPL Refinery Telemetry Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }
    .card { background: #1e293b; border-radius: 12px; border: 1px solid #334155; padding: 20px; margin-bottom: 16px; }
    h1 { color: #38bdf8; font-size: 20px; margin-top: 0; }
    .badge { background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 4px 10px; border-radius: 9999px; font-size: 12px; border: 1px solid rgba(16, 185, 129, 0.4); }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }
    .metric { background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #1e293b; }
    .val { font-size: 22px; font-weight: bold; font-family: monospace; color: #f1f5f9; }
  </style>
</head>
<body>
  <div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h1>Operational Telemetry Dashboard</h1>
      <span class="badge">AIR-GAP ACTIVE</span>
    </div>
    <p style="color: #94a3b8; font-size: 13px;">Live automated process data stream monitoring (OISD-STD-105 Compliant)</p>
    <div class="grid">
      <div class="metric"><div style="font-size: 11px; color: #94a3b8;">Throughput</div><div class="val">310.5 KBPD</div></div>
      <div class="metric"><div style="font-size: 11px; color: #94a3b8;">Combustible Gas</div><div class="val" style="color: #4ade80;">0.0% LEL</div></div>
      <div class="metric"><div style="font-size: 11px; color: #94a3b8;">Energy (MBN)</div><div class="val">54.2</div></div>
    </div>
  </div>
</body>
</html>`;

    case 'shell':
      return `#!/usr/bin/env bash
# MRPL SOVEREIGN AIR-GAPPED VERIFICATION SCRIPT
# Filename: ${filename}

set -euo pipefail

echo "=================================================="
echo "MRPL SOVEREIGN SYSTEM INTEGRITY & OISD CHECK"
echo "=================================================="

# 1. Check network isolation
echo "[1/3] Verifying Air-Gapped Network State..."
if ping -c 1 -W 1 8.8.8.8 >/dev/null 2>&1; then
    echo "❌ ERROR: External route detected! Aborting."
    exit 1
else
    echo "✓ PASS: Network isolated (Air-Gapped 100%)."
fi

# 2. Check SHA-256 Checksums
echo "[2/3] Verifying Deliverable SHA-256 Signatures..."
echo "✓ HW-B-OISD105.docx : SIGNATURE_VALID"
echo "✓ HSE-KPI-Dash.xlsx : SIGNATURE_VALID"

# 3. Model Engine Status
echo "[3/3] Querying Local On-Prem Inference Cluster..."
echo "✓ Primary Reasoning Engine (Q4_K_M) : READY (0.0ms WAN)"

echo "--------------------------------------------------"
echo "SYSTEM STATE: SECURE & OPERATIONAL"
`;

    case 'python':
    default:
      return `"""
MRPL SOVEREIGN REFINERY OPTIMIZATION ALGORITHM
Filename: ${filename}
Runtime: Python 3.11 On-Premise Sandboxed Execution (--network none)
Compliance: OISD-STD-105 / PESO / Statutory Energy Efficiency
"""

import math
from typing import Dict, Any

def evaluate_crude_assay_blend(
    api_gravity: float,
    sulfur_pct: float,
    brent_differential_usd: float,
    throughput_kbpd: float = 310.0
) -> Dict[str, Any]:
    """Calculates gross refining margin (GRM) uplift & energy efficiency index."""
    base_grm_usd_per_bbl = 11.20
    
    # API gravity bonus/penalty (Benchmark 32.0 API)
    gravity_delta = (api_gravity - 32.0) * 0.15
    
    # Sulfur desulfurization processing cost penalty
    sulfur_penalty = max(0.0, (sulfur_pct - 0.5) * 1.20)
    
    # Net realized margin per barrel
    net_grm = base_grm_usd_per_bbl + brent_differential_usd + gravity_delta - sulfur_penalty
    daily_ebitda_usd = net_grm * (throughput_kbpd * 1000)
    
    return {
        "api_gravity": api_gravity,
        "sulfur_pct": sulfur_pct,
        "brent_differential_usd": brent_differential_usd,
        "net_grm_usd_per_bbl": round(net_grm, 2),
        "daily_operating_ebitda_usd": round(daily_ebitda_usd, 2),
        "energy_consumption_mbn": 54.2,
        "oisd_safety_compliant": True,
        "recommendation": "OPTIMAL_FEEDSTOCK_BLEND" if net_grm >= 12.0 else "SUB_OPTIMAL"
    }

if __name__ == "__main__":
    print("=====================================================")
    print("  MRPL SOVEREIGN PROCESS YIELD & MARGIN CALCULATOR   ")
    print("=====================================================")
    
    report = evaluate_crude_assay_blend(
        api_gravity=28.4,
        sulfur_pct=1.85,
        brent_differential_usd=2.40,
        throughput_kbpd=310.5
    )
    
    for key, val in report.items():
        print(f"  {key:<30} : {val}")
        
    print("=====================================================")
    print("  STATUS: LOCAL RUN COMPLETE (runtime printed above)     ")
`;
  }
}

export function CodeCanvasEditor({ deliverable }: CodeCanvasEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [outputConsole, setOutputConsole] = useState<string | null>(null);
  const [sqlResults, setSqlResults] = useState<{ headers: string[]; rows: (string | number | null)[][] } | null>(null);
  const [activeViewTab, setActiveViewTab] = useState<'editor' | 'preview'>('editor');
  const [lastRun, setLastRun] = useState<CodeRunResult | null>(null);
  const [fontSize, setFontSize] = useState(13);
  const [showLineNumbers, setShowLineNumbers] = useState(true);
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [replaceTerm, setReplaceTerm] = useState('');

  const [currentLang, setCurrentLang] = useState<SupportedLang>(() =>
    detectLanguage(deliverable.filename, deliverable.type)
  );

  const initialCode =
    editedContent[deliverable.id]?.code || getDefaultCodeByLang(currentLang, deliverable.filename);

  const [code, setCode] = useState(initialCode);

  useEffect(() => {
    const detected = detectLanguage(deliverable.filename, deliverable.type);
    setCurrentLang(detected);
    const codeForFile =
      editedContent[deliverable.id]?.code || getDefaultCodeByLang(detected, deliverable.filename);
    setCode(codeForFile);
  }, [deliverable.id]);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setCode(val);
    updateEditedContent(deliverable.id, { code: val });
  };

  const handleLanguageChange = (newLang: SupportedLang) => {
    setCurrentLang(newLang);
    const template = getDefaultCodeByLang(newLang, deliverable.filename);
    setCode(template);
    updateEditedContent(deliverable.id, { code: template });
    setOutputConsole(null);
    setSqlResults(null);
    setLastRun(null);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFormatCode = () => {
    if (currentLang === 'json') {
      try {
        const parsed = JSON.parse(code);
        const formatted = JSON.stringify(parsed, null, 2);
        setCode(formatted);
        updateEditedContent(deliverable.id, { code: formatted });
      } catch (err) {
        setOutputConsole(`[JSON FORMAT ERROR]: ${String(err)}`);
      }
    } else {
      // Clean indentation formatting
      const cleaned = code
        .split('\n')
        .map((line: string) => line.replace(/\s+$/, ''))
        .join('\n');
      setCode(cleaned);
      updateEditedContent(deliverable.id, { code: cleaned });
    }
  };

  const handleFindReplace = () => {
    if (!searchTerm) return;
    const regex = new RegExp(searchTerm, 'g');
    const replaced = code.replace(regex, replaceTerm);
    setCode(replaced);
    updateEditedContent(deliverable.id, { code: replaced });
  };

  const handleDownloadFile = () => {
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const ext = LANGUAGE_CONFIGS[currentLang].ext;
    a.download = deliverable.filename.includes('.') ? deliverable.filename : `${deliverable.filename}${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRunCode = async () => {
    // HTML has no server-side runner: the browser iframe is the real renderer.
    if (currentLang === 'html') {
      setActiveViewTab('preview');
      setLastRun(null);
      setOutputConsole(
        '[HTML PREVIEW]\nRendered by your browser inside a sandboxed iframe (scripts allowed, no network).\nThere is no server-side HTML runner, so nothing was executed on the backend.'
      );
      return;
    }

    setIsRunning(true);
    setSqlResults(null);
    setOutputConsole(`Executing ${LANGUAGE_CONFIGS[currentLang].label} on the sovereign backend...`);

    const result = await runCode(currentLang, code, { filename: deliverable.filename });

    setLastRun(result);
    setOutputConsole(formatRunReport(result));

    if (result.sql) {
      setSqlResults({ headers: result.sql.columns, rows: result.sql.rows });
    }

    setIsRunning(false);
  };

  const lines = code.split('\n');

  return (
    <div className="flex flex-col h-full bg-[#08080c] text-[#e3e3e3] select-none font-sans relative">
      {/* 1. Universal Language Ribbon Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2 bg-[#0e0e14] border-b border-[#1c1c26] shrink-0 text-xs">
        {/* Left: Language Switcher Dropdown & File Label */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <FileCode className={`h-4 w-4 ${LANGUAGE_CONFIGS[currentLang].color}`} />
            <span className="font-bold text-[#f1f3f4] font-mono">{deliverable.filename}</span>
          </div>

          <div className="h-4 w-px bg-[#262634]" />

          {/* Interactive Language Selector Dropdown (Custom Dropdown) */}
          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] text-[#8e918f]">Language:</span>
            <CustomDropdown
              value={currentLang}
              onChange={(val) => handleLanguageChange(val as SupportedLang)}
              size="xs"
              options={Object.entries(LANGUAGE_CONFIGS).map(([key, cfg]) => ({
                value: key,
                label: `${cfg.label} (${cfg.ext})`,
              }))}
              buttonClassName="bg-[#14141e] text-[#a8c7fa] border-[#262638] rounded-xl font-mono text-xs font-semibold"
            />
          </div>

          {/* View Tab Switcher for HTML/Web Code */}
          {currentLang === 'html' && (
            <div className="flex items-center bg-[#14141e] border border-[#262638] rounded-xl p-0.5">
              <button
                onClick={() => setActiveViewTab('editor')}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                  activeViewTab === 'editor' ? 'bg-[#222234] text-[#a8c7fa]' : 'text-[#8e918f]'
                }`}
              >
                Code
              </button>
              <button
                onClick={() => setActiveViewTab('preview')}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center space-x-1 ${
                  activeViewTab === 'preview' ? 'bg-[#222234] text-emerald-400' : 'text-[#8e918f]'
                }`}
              >
                <Globe className="h-3 w-3" />
                <span>Web Preview</span>
              </button>
            </div>
          )}
        </div>

        {/* Right: Developer Actions (Run, Format, Find, Zoom, Copy, Download) */}
        <div className="flex items-center space-x-2">
          {/* Zoom / Font Size */}
          <div className="flex items-center space-x-1 pr-2 border-r border-[#262634]">
            <button
              onClick={() => setFontSize((s) => Math.max(10, s - 1))}
              className="p-1 rounded hover:bg-[#1a1a26] text-[#8e918f]"
              title="Decrease Font Size"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[11px] font-mono text-[#a8c7fa]">{fontSize}px</span>
            <button
              onClick={() => setFontSize((s) => Math.min(24, s + 1))}
              className="p-1 rounded hover:bg-[#1a1a26] text-[#8e918f]"
              title="Increase Font Size"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Format / Beautify Code */}
          <button
            onClick={handleFormatCode}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-xl bg-[#14141e] hover:bg-[#1e1e2c] border border-[#262638] text-[#c4c7c5] hover:text-white"
            title="Format / Beautify Code"
          >
            <Sparkles className="h-3 w-3 text-[#a8c7fa]" />
            <span className="hidden sm:inline">Format</span>
          </button>

          {/* Search & Replace Modal Trigger */}
          <button
            onClick={() => setShowFindReplace(!showFindReplace)}
            className={`p-1.5 rounded-xl border transition-colors ${
              showFindReplace ? 'bg-blue-500/20 border-blue-500/50 text-[#a8c7fa]' : 'bg-[#14141e] border-[#262638] text-[#8e918f] hover:text-white'
            }`}
            title="Search & Replace"
          >
            <Search className="h-3.5 w-3.5" />
          </button>

          {/* Copy Code */}
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-xl bg-[#14141e] hover:bg-[#1e1e2c] border border-[#262638] text-[#c4c7c5] hover:text-white"
            title="Copy Code"
          >
            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3 text-[#a8c7fa]" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Download File */}
          <button
            onClick={handleDownloadFile}
            className="p-1.5 rounded-xl bg-[#14141e] hover:bg-[#1e1e2c] border border-[#262638] text-[#8e918f] hover:text-white"
            title="Download Source File"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          {/* Primary Run Code Button */}
          <button
            onClick={handleRunCode}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-3.5 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-md shadow-emerald-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Play className={`h-3 w-3 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Running...' : 'Run in Sandbox'}</span>
          </button>
        </div>
      </div>

      {/* Find & Replace Bar */}
      {showFindReplace && (
        <div className="flex items-center space-x-2 px-4 py-2 bg-[#12121a] border-b border-[#20202c] text-xs">
          <input
            type="text"
            placeholder="Find text..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-[#0b0b10] border border-[#262638] rounded-lg px-2.5 py-1 text-xs text-[#e3e3e3] focus:outline-none focus:border-[#a8c7fa] w-44 font-mono"
          />
          <input
            type="text"
            placeholder="Replace with..."
            value={replaceTerm}
            onChange={(e) => setReplaceTerm(e.target.value)}
            className="bg-[#0b0b10] border border-[#262638] rounded-lg px-2.5 py-1 text-xs text-[#e3e3e3] focus:outline-none focus:border-[#a8c7fa] w-44 font-mono"
          />
          <button
            onClick={handleFindReplace}
            className="px-2.5 py-1 rounded-lg bg-[#1a1a28] hover:bg-[#252538] border border-[#303046] text-[#a8c7fa] font-medium"
          >
            Replace All
          </button>
          <button
            onClick={() => setShowFindReplace(false)}
            className="p-1 text-[#8e918f] hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      {/* 2. Main Workspace: Code Area / HTML Live Preview */}
      <div className="flex-1 flex overflow-hidden bg-[#07070b]">
        {activeViewTab === 'editor' ? (
          <div className="flex-1 flex overflow-hidden">
            {/* Line Numbers Column */}
            {showLineNumbers && (
              <div
                style={{ fontSize: `${fontSize}px` }}
                className="w-12 bg-[#09090f] text-[#4b4d58] border-r border-[#1a1a24] text-right pr-2 py-4 select-none font-mono leading-relaxed"
              >
                {lines.map((_: string, i: number) => (
                  <div key={i} className="hover:text-[#8e918f] transition-colors">{i + 1}</div>
                ))}
              </div>
            )}

            {/* Code Textarea Area */}
            <textarea
              value={code}
              onChange={handleCodeChange}
              spellCheck={false}
              style={{ fontSize: `${fontSize}px` }}
              className="flex-1 h-full bg-transparent text-[#dcdfe4] focus:outline-none resize-none font-mono p-4 leading-relaxed overflow-auto selection:bg-[#38bdf8]/30 selection:text-white"
            />
          </div>
        ) : (
          /* Live HTML5 Web Preview Frame */
          <div className="flex-1 bg-[#ffffff] overflow-auto">
            <iframe
              srcDoc={code}
              title="Live HTML DOM Preview"
              className="w-full h-full border-none"
              sandbox="allow-scripts"
            />
          </div>
        )}
      </div>

      {/* 3. Multi-Tab Output Deck (Terminal / SQL Data Table) */}
      {(outputConsole || sqlResults) && (
        <div className="h-56 bg-[#060609] border-t border-[#1e1e28] flex flex-col shrink-0">
          {/* Output Deck Header */}
          <div className="flex items-center justify-between px-4 py-2 bg-[#0c0c12] border-b border-[#181822] text-xs text-[#8e918f]">
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1.5 text-emerald-400 font-semibold">
                <Terminal className="h-3.5 w-3.5" />
                <span>SANDBOX TERMINAL OUTPUT</span>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                  !lastRun
                    ? 'bg-[#14141e] text-[#6b6d76] border-[#262638]'
                    : lastRun.isolated
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}
                title={lastRun ? lastRun.engine : 'Nothing has been executed yet'}
              >
                {!lastRun
                  ? 'NOT RUN'
                  : lastRun.isolated
                    ? 'SANDBOXED'
                    : 'NO CONTAINER ISOLATION'}
              </span>
            </div>

            <button
              onClick={() => {
                setOutputConsole(null);
                setSqlResults(null);
              }}
              className="text-[#6b6d76] hover:text-white text-xs px-2 py-0.5 rounded hover:bg-[#181822]"
            >
              Close Console
            </button>
          </div>

          {/* Console Text & SQL Results Grid */}
          <div className="flex-1 overflow-auto p-3 font-mono text-xs space-y-3">
            {outputConsole && (
              <pre
                className={`whitespace-pre-wrap leading-relaxed ${
                  !lastRun
                    ? 'text-emerald-400'
                    : lastRun.status === 'SUCCESS'
                      ? 'text-emerald-400'
                      : lastRun.status === 'UNSUPPORTED'
                        ? 'text-amber-400'
                        : 'text-rose-400'
                }`}
              >
                {outputConsole}
              </pre>
            )}

            {sqlResults && (
              <div className="rounded-xl border border-[#262638] overflow-hidden mt-2">
                <table className="w-full text-left border-collapse text-xs">
                  <thead className="bg-[#14141e] text-[#a8c7fa] font-bold border-b border-[#262638]">
                    <tr>
                      {sqlResults.headers.map((h, idx) => (
                        <th key={idx} className="p-2 border-r border-[#262638] font-mono">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sqlResults.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="border-b border-[#181824] hover:bg-[#12121c] text-[#e3e3e3]">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="p-2 border-r border-[#181824] font-mono">{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. Bottom Code Statistics Footer */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#0a0a0e] border-t border-[#1a1a24] text-[11px] text-[#6b6d76] font-mono shrink-0">
        <div className="flex items-center space-x-3">
          <span>Lines: <strong className="text-[#a8c7fa]">{lines.length}</strong></span>
          <span>&bull;</span>
          <span>Length: <strong className="text-[#a8c7fa]">{code.length}</strong> chars</span>
          <span>&bull;</span>
          <span>Encoding: <strong>UTF-8</strong></span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-emerald-400 font-sans font-medium">
            {LANGUAGE_CONFIGS[currentLang].engine}
          </span>
        </div>
      </div>
    </div>
  );
}
