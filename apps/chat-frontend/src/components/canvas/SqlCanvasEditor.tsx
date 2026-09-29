'use client';

import React, { useEffect, useState } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Play,
  Copy,
  Check,
  Database,
  Table as TableIcon,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Download,
  Terminal,
  FileSpreadsheet,
  CheckCircle2,
  Filter,
  X,
  Server
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { runCode } from '@/lib/codeRunner';
import { apiFetch } from '@/lib/apiFetch';
import { getApiBase } from '@/lib/apiBase';

interface SqlCanvasEditorProps {
  deliverable: DeliverableItem;
}

export function SqlCanvasEditor({ deliverable }: SqlCanvasEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [fontSize, setFontSize] = useState(13);
  const [activeTab, setActiveTab] = useState<'results' | 'messages'>('results');
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [runStatus, setRunStatus] = useState<'SUCCESS' | 'ERROR' | 'UNSUPPORTED' | null>(null);
  const [runMessage, setRunMessage] = useState<string | null>(null);
  const [runEngine, setRunEngine] = useState<string | null>(null);
  // The active database engine, read from the backend. Never hard-coded: the
  // deployment targets PostgreSQL by default and MySQL only as a fallback, so a
  // fixed "XAMPP MySQL" label would misreport the engine actually in use.
  const [dbEngine, setDbEngine] = useState<string>('Database');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch(`${getApiBase()}/api/sandbox/status`);
        if (!res.ok) return;
        const data = await res.json();
        const label = data?.database?.label;
        if (!cancelled && label) setDbEngine(label);
      } catch {
        // Leave the default; the editor still works.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const defaultQuery =
    editedContent[deliverable.id]?.code ||
    `-- ==========================================================
-- MRPL SOVEREIGN REFINERY TELEMETRY & COMPLIANCE QUERY
-- Database: read-only sandbox schema (sih_sql_sandbox) on the configured engine
-- Only SELECT / WITH / SHOW / EXPLAIN are permitted here
-- Query: ${deliverable.filename}
-- ==========================================================

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

  const [query, setQuery] = useState(defaultQuery);

  // No fabricated rows: results only ever come from a real sandbox execution.
  const [results, setResults] = useState<{
    headers: string[];
    rows: (string | number | null)[][];
  }>({
    headers: [],
    rows: [],
  });

  const handleQueryChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setQuery(val);
    updateEditedContent(deliverable.id, { code: val });
  };

  const handleRunQuery = async () => {
    setIsRunning(true);
    setActiveTab('results');
    setRunMessage(null);

    const result = await runCode('sql', query, { filename: deliverable.filename });

    setRunStatus(result.status);
    setRunEngine(result.engine);
    setExecutionTime(Number(result.duration_ms || 0));

    if (result.sql) {
      setResults({ headers: result.sql.columns, rows: result.sql.rows });
      setRunMessage(
        `${result.sql.row_count} row(s) returned from sandbox schema \`${result.sql.sandbox_schema}\`` +
          `${result.sql.truncated ? ' (capped at 500 rows)' : ''}.`
      );
    } else {
      setResults({ headers: [], rows: [] });
      setRunMessage(result.message || result.stderr);
    }

    setIsRunning(false);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([query], { type: 'text/sql;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = deliverable.filename.endsWith('.sql') ? deliverable.filename : `${deliverable.filename}.sql`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const lines = query.split('\n');

  return (
    <div className="flex flex-col h-full bg-[#0f172a] text-[#f8fafc] select-none font-sans relative overflow-hidden">
      {/* 1. TOP STATUS & ACTION BAR (Mobile Optimized) */}
      <div className="flex items-center justify-between px-2.5 sm:px-4 py-2 sm:py-2.5 bg-[#0b1120] border-b border-slate-800 text-xs shrink-0 gap-2 overflow-x-auto scrollbar-none">
        {/* Left: DB Engine Status */}
        <div className="flex items-center space-x-2 shrink-0">
          <div className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1 rounded-xl bg-cyan-950/40 border border-cyan-800/40 text-cyan-400 font-mono text-[10px] sm:text-xs">
            <Server className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
            <span className="hidden sm:inline">{dbEngine} &bull; Read-Only Sandbox</span>
            <span className="sm:hidden">{dbEngine} sandbox</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0">
          {/* Zoom / Font Size */}
          <div className="hidden sm:flex items-center space-x-1 pr-2.5 border-r border-slate-700">
            <button
              onClick={() => setFontSize((s) => Math.max(10, s - 1))}
              className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white"
              title="Decrease Font Size"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[11px] font-mono text-slate-200 font-bold">{fontSize}px</span>
            <button
              onClick={() => setFontSize((s) => Math.min(22, s + 1))}
              className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white"
              title="Increase Font Size"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 sm:px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold transition-colors cursor-pointer"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
            <span className="hidden xs:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors cursor-pointer"
            title="Download .sql script"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          {/* Run SQL Query */}
          <button
            onClick={handleRunQuery}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-3 sm:px-4 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-md shadow-cyan-900/30 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer disabled:opacity-50 shrink-0"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Executing...' : 'Run SQL'}</span>
          </button>
        </div>
      </div>

      {/* 2. SQL QUERY EDITOR AREA */}
      <div className="flex-1 flex overflow-hidden bg-[#0b1120]">
        <div
          style={{ fontSize: `${fontSize}px` }}
          className="w-12 bg-[#0b1120] text-slate-600 border-r border-slate-800 text-right pr-3 py-4 select-none font-mono leading-relaxed"
        >
          {lines.map((_: string, i: number) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        <textarea
          value={query}
          onChange={handleQueryChange}
          spellCheck={false}
          style={{ fontSize: `${fontSize}px` }}
          className="flex-1 h-full bg-[#0b1120] text-cyan-200 focus:outline-none resize-none font-mono p-4 leading-relaxed overflow-auto selection:bg-cyan-900/60"
        />
      </div>

      {/* 3. SQL RESULTS GRID PANEL */}
      <div className="h-56 bg-[#0f172a] border-t border-slate-700/80 flex flex-col shrink-0">
        <div className="flex items-center justify-between px-4 py-2 bg-[#1e293b] border-b border-slate-700 text-xs text-slate-400">
          <div className="flex items-center space-x-3">
            <span className="font-bold text-cyan-400 flex items-center gap-1.5">
              <TableIcon className="h-3.5 w-3.5" />
              <span>Query Results ({results.rows.length} rows)</span>
            </span>
            {executionTime && (
              <span className="text-[11px] text-slate-400 font-mono">
                &bull; Executed in <strong className="text-emerald-400">{executionTime}ms</strong>
              </span>
            )}
          </div>

          <span
            className={`font-bold text-[11px] border px-2.5 py-0.5 rounded-full ${
              runStatus === 'SUCCESS'
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80'
                : runStatus === 'UNSUPPORTED'
                  ? 'bg-amber-950/60 text-amber-400 border-amber-800/80'
                  : runStatus === 'ERROR'
                    ? 'bg-rose-950/60 text-rose-400 border-rose-800/80'
                    : 'bg-slate-800/60 text-slate-400 border-slate-700'
            }`}
            title={runEngine || 'No query executed yet'}
          >
            {runStatus === 'SUCCESS'
              ? '✓ Executed (read-only)'
              : runStatus === 'UNSUPPORTED'
                ? '⚠ Not executed'
                : runStatus === 'ERROR'
                  ? '✗ Query failed'
                  : '— Not run yet'}
          </span>
        </div>

        {/* Run Result Message (real engine output) */}
        {runMessage && (
          <div
            className={`px-4 py-1.5 text-[11px] font-mono border-b ${
              runStatus === 'SUCCESS'
                ? 'bg-emerald-950/30 text-emerald-300 border-emerald-900/60'
                : runStatus === 'UNSUPPORTED'
                  ? 'bg-amber-950/30 text-amber-300 border-amber-900/60'
                  : 'bg-rose-950/30 text-rose-300 border-rose-900/60'
            }`}
            title={runMessage}
          >
            {runMessage}
          </div>
        )}

        {/* Results Data Table */}
        <div className="flex-1 overflow-auto bg-[#090d16]">
          <table className="w-full text-xs font-mono text-left border-collapse">
            <thead className="bg-[#1e293b] text-slate-300 border-b border-slate-700 sticky top-0">
              <tr>
                {results.headers.map((h, idx) => (
                  <th key={idx} className="p-2.5 border-r border-slate-700/60 font-bold text-[11px]">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.rows.length === 0 ? (
                <tr>
                  <td colSpan={Math.max(results.headers.length, 1)} className="p-6 text-center text-slate-500">
                    {runStatus === null
                      ? 'No query executed yet - press "Run SQL" to execute against the read-only sandbox.'
                      : runStatus === 'SUCCESS'
                        ? 'Query executed successfully and returned 0 rows.'
                        : 'No result set - see the run status above.'}
                  </td>
                </tr>
              ) : (
                results.rows.map((row, rIdx) => (
                  <tr key={rIdx} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="p-2.5 border-r border-slate-800/60 text-slate-300">
                        {cell === 'SAFE_AUTHORIZED' ? (
                          <span className="text-emerald-400 font-bold">SAFE_AUTHORIZED</span>
                        ) : (
                          cell
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. STATISTICS FOOTER */}
      <div className="flex items-center justify-between px-5 py-2 bg-[#1e293b] border-t border-slate-700/80 text-[11px] text-slate-400 font-mono shrink-0">
        <div className="flex items-center space-x-3">
          <span>Lines: <strong className="text-white">{lines.length}</strong></span>
          <span>&bull;</span>
          <span>Database: <strong className="text-cyan-400">{dbEngine} sandbox</strong></span>
          <span>&bull;</span>
          <span>
            Status:{' '}
            <strong
              className={
                runStatus === 'SUCCESS'
                  ? 'text-emerald-400'
                  : runStatus === 'UNSUPPORTED'
                    ? 'text-amber-400'
                    : runStatus === 'ERROR'
                      ? 'text-rose-400'
                      : 'text-slate-300'
              }
            >
              {runStatus === 'SUCCESS'
                ? 'Query executed'
                : runStatus === 'UNSUPPORTED'
                  ? 'Not executed'
                  : runStatus === 'ERROR'
                    ? 'Failed'
                    : 'Idle'}
            </strong>
          </span>
        </div>
        <span className="text-cyan-400 font-sans font-bold flex items-center gap-1.5" title={runEngine || undefined}>
          <span
            className={`h-2 w-2 rounded-full ${
              runStatus === 'SUCCESS' ? 'bg-emerald-400' : runStatus ? 'bg-amber-400' : 'bg-slate-500'
            }`}
          />
          SQL Telemetry Studio
        </span>
      </div>
    </div>
  );
}
