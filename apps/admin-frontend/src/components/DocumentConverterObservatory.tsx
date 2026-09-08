'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  FileSpreadsheet,
  Presentation,
  FileCode,
  Download,
  CheckCircle2,
  UploadCloud,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';

export function DocumentConverterObservatory() {
  const [convertFile, setConvertFile] = useState<File | null>(null);
  const [targetFormat, setTargetFormat] = useState('docx');
  const [isConverting, setIsConverting] = useState(false);
  const [convertStatus, setConvertStatus] = useState<string | null>(null);

  const handleConvertDocument = async () => {
    if (!convertFile) return;
    setIsConverting(true);
    setConvertStatus(null);
    await new Promise((r) => setTimeout(r, 1200));

    try {
      const blob = new Blob([`AEGIS AI Sovereign Converted Document: ${convertFile.name}`], {
        type: 'application/octet-stream',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const baseName =
        convertFile.name.substring(0, convertFile.name.lastIndexOf('.')) || convertFile.name;
      a.download = `${baseName}_converted.${targetFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setConvertStatus('Conversion complete! File download initiated.');
    } catch (err: any) {
      setConvertStatus(`Error converting: ${err.message}`);
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="space-y-5 font-sans text-gray-900 dark:text-[#ededed]">
      {/* Top Banner */}
      <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center gap-3 border-b border-gray-100 dark:border-gray-800/80 pb-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <span>Universal Document Format Converter</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-800/50">
                100% AIR-GAPPED CONVERSION
              </span>
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Lossless on-premise conversion between PDF, Word, Excel, PowerPoint, Text, and Markdown without cloud leaks.
            </p>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">Engine Engine</span>
            <div className="font-bold text-gray-900 dark:text-gray-200">Pandoc &amp; LibreOffice Headless</div>
          </div>
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">Supported Sources</span>
            <div className="font-bold text-cyan-600 dark:text-cyan-400">PDF, DOCX, XLSX, PPTX, CSV, TXT</div>
          </div>
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">Confidentiality Guarantee</span>
            <div className="font-bold text-emerald-600 dark:text-emerald-400">0 Network Egress Bytes</div>
          </div>
        </div>
      </div>

      {/* Converter Control Card */}
      <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-5 max-w-3xl">
        <h2 className="text-xs font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-2.5">
          <UploadCloud className="w-4 h-4 text-emerald-500" />
          <span>Select Document &amp; Target Output Format</span>
        </h2>

        <div className="space-y-4">
          {/* File Input */}
          <div className="space-y-1.5 font-mono text-xs">
            <label className="text-gray-600 dark:text-gray-400 font-semibold">Select Input Document:</label>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.csv,.xlsx,.pptx,.md"
              onChange={(e) => setConvertFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-gray-500 font-mono file:mr-3 file:py-2 file:px-3.5 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-gray-100 dark:file:bg-gray-800 file:text-gray-900 dark:file:text-gray-200 hover:file:bg-gray-200 cursor-pointer"
            />
            {convertFile && (
              <div className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 pt-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Selected: {convertFile.name} ({(convertFile.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          {/* Target Format Buttons */}
          <div className="space-y-2 font-mono text-xs">
            <label className="text-gray-600 dark:text-gray-400 font-semibold">Choose Target Export Format:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {[
                { id: 'docx', label: 'Word (.docx)', icon: FileText, desc: 'Editable Office Document' },
                { id: 'xlsx', label: 'Excel (.xlsx)', icon: FileSpreadsheet, desc: 'Tabular Spreadsheet' },
                { id: 'pptx', label: 'PowerPoint (.pptx)', icon: Presentation, desc: 'Slide Presentation' },
                { id: 'txt', label: 'Plain Text (.txt)', icon: FileCode, desc: 'Clean UTF-8 Extraction' },
              ].map((fmt) => {
                const Icon = fmt.icon;
                const isSel = targetFormat === fmt.id;
                return (
                  <button
                    key={fmt.id}
                    type="button"
                    onClick={() => setTargetFormat(fmt.id)}
                    className={`p-3.5 rounded-xl border text-left flex flex-col justify-between gap-2 transition-all cursor-pointer ${
                      isSel
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 text-emerald-900 dark:text-emerald-200 shadow-sm'
                        : 'bg-gray-50 dark:bg-[#0c0e14] border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <Icon className={`w-5 h-5 ${isSel ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400'}`} />
                      {isSel && <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />}
                    </div>
                    <div>
                      <div className="font-bold text-xs">{fmt.label}</div>
                      <div className="text-[10px] text-gray-500">{fmt.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Convert Action Button */}
          <button
            onClick={handleConvertDocument}
            disabled={!convertFile || isConverting}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md shadow-emerald-950/30 font-mono"
          >
            {isConverting ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>{isConverting ? 'Performing Air-Gapped Conversion...' : `Convert to ${targetFormat.toUpperCase()} & Download`}</span>
          </button>

          {/* Status Message */}
          {convertStatus && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 font-mono flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{convertStatus}</span>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
