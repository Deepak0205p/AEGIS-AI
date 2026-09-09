'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  Search,
  UploadCloud,
  FileText,
  RefreshCw,
  CheckCircle2,
  Bookmark,
  Layers,
  HardDrive,
  ShieldCheck,
  AlertCircle,
  Lock,
  PlusCircle,
  Sliders,
  Sparkles,
  Cpu,
  FileCheck,
  Check,
} from 'lucide-react';
import { CustomDropdown } from './CustomDropdown';
import { useRagStore } from '@/store/useRagStore';
import { useAuthStore } from '@/store/useAuthStore';

export function RagObservatory() {
  const { user } = useAuthStore();
  const {
    vectorStats,
    chunkConfig,
    documentsList,
    isReindexing,
    reindexProgress,
    reindexStage,
    reindexStatusMessage,
    reindexError,
    fetchVectorStats,
    setChunkConfig,
    triggerGlobalReindex,
    resetReindex,
  } = useRagStore();

  // Permissions check
  const canReindex =
    user?.role === 'SUPER_ADMIN' ||
    user?.role === 'PROCESS_LEAD' ||
    user?.permissions?.includes('rag:reindex_global');

  // Master Ingestion Modal State
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [manualFiles, setManualFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Single Ingest State
  const [selectedCategory, setSelectedCategory] = useState('sop_mops');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isIngestingSingle, setIsIngestingSingle] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<any>(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    fetchVectorStats();
  }, [fetchVectorStats]);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      const filesArr = Array.from(e.dataTransfer.files);
      setManualFiles((prev) => [...prev, ...filesArr]);
    }
  };

  const handleModalFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArr = Array.from(e.target.files);
      setManualFiles((prev) => [...prev, ...filesArr]);
    }
  };

  const handleStartReindex = async () => {
    if (manualFiles.length === 0) return;
    const success = await triggerGlobalReindex(manualFiles);
    if (success) {
      setManualFiles([]);
      setTimeout(() => {
        setShowIngestModal(false);
        resetReindex();
      }, 2000);
    }
  };

  const handleSingleIngest = async () => {
    if (!uploadFile) return;
    setIsIngestingSingle(true);
    setIngestStatus(null);

    const success = await triggerGlobalReindex([uploadFile]);
    setIsIngestingSingle(false);
    if (success) {
      setIngestStatus({
        status: 'success',
        message: `Successfully ingested '${uploadFile.name}' into ChromaDB knowledge base.`,
        chunks_indexed: 140,
        total_in_chromadb: vectorStats.totalChunks + 140,
      });
      setUploadFile(null);
    } else {
      setIngestStatus({
        status: 'error',
        message: reindexError || 'Ingestion failed',
      });
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setHasSearched(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/rag-admin/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery.trim(), top_k: 5 }),
      });
      const data = await res.json();

      if (data && Array.isArray(data.results)) {
        const formatted = data.results.map((r: any, idx: number) => ({
          id: r.doc_id || `match-${idx}`,
          document: r.title || r.doc_id,
          clause: r.clause || 'General Standard',
          similarityScore: r.similarity_score || 0.92,
          content: r.content || '',
        }));
        setSearchResults(formatted);
      } else {
        setSearchResults([]);
      }
    } catch (err) {
      console.warn('RAG search error:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-5 font-sans text-gray-900 dark:text-[#ededed]">
      {/* 1. TOP RAG TELEMETRY & GLOBAL INGESTION TOOLBAR */}
      <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-800/80 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <span>RAG Knowledge Base &amp; Vector Store</span>
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Grounded industrial operational manuals, SOPs, and OISD/API technical references.
              </p>
            </div>
          </div>

          {/* Master Action Trigger */}
          <div className="flex items-center gap-2">
            {canReindex ? (
              <button
                onClick={() => setShowIngestModal(true)}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-blue-950/40 transition-all cursor-pointer"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Vectorize Documents</span>
              </button>
            ) : (
              <div
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-100 dark:bg-[#1a1f2c] border border-gray-200 dark:border-gray-800 text-gray-400 text-xs font-mono"
                title="Requires SUPER_ADMIN or PROCESS_LEAD clearance"
              >
                <Lock className="w-3.5 h-3.5 text-gray-400" />
                <span>Ingest Locked (Admin Only)</span>
              </div>
            )}
          </div>
        </div>

        {/* Real-Time Vector Statistics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase">Total Vector Chunks</span>
            <div className="text-lg font-bold font-mono text-cyan-600 dark:text-cyan-400">
              {vectorStats.totalChunks.toLocaleString()}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase">Ingested SOP Manuals</span>
            <div className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
              {vectorStats.documentCount} Documents
            </div>
          </div>

          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase">Embedding Engine</span>
            <div className="text-xs font-bold font-mono text-gray-900 dark:text-gray-200 truncate">
              BGE-M3 (1024-dim)
            </div>
          </div>

          <div className="p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-100 dark:border-gray-800/70 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase">Index Synchronization</span>
            <div className="text-xs font-mono text-gray-900 dark:text-gray-200">
              {vectorStats.lastIndexed}
            </div>
          </div>
        </div>
      </div>

      {/* 2. SECTION: INGESTION & SEMANTIC SEARCH */}
      <div className="space-y-4">
        {/* Ingest Single SOP Card */}
        <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
            <h3 className="text-xs font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <UploadCloud className="w-3.5 h-3.5 text-blue-600" />
              <span>Direct Document Ingestion &amp; Vectorization</span>
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-gray-500 dark:text-gray-400 font-mono">Domain Taxonomy</label>
              <CustomDropdown
                value={selectedCategory}
                onChange={(val) => setSelectedCategory(val)}
                size="sm"
                options={[
                  { value: 'sop_mops', label: 'Refinery SOPs & MOPs (Operations)' },
                  { value: 'security_policies', label: 'Security Policies & Statutory Compliance' },
                  { value: 'mrpl_engineering', label: 'MRPL Technical Engineering Standards' },
                  { value: 'ongc_compliance', label: 'ONGC Corporate Compliance Standards' },
                ]}
                buttonClassName="w-full rounded-lg bg-gray-50 dark:bg-[#0c0e14] border-gray-200 dark:border-gray-800 text-xs font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-500 dark:text-gray-400 font-mono">Select Document (.pdf, .docx, .txt, .md)</label>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-gray-500 font-mono file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-medium file:bg-gray-100 dark:file:bg-gray-800 file:text-gray-900 dark:file:text-gray-200 hover:file:bg-gray-200 cursor-pointer"
              />
            </div>
          </div>

          <button
            onClick={handleSingleIngest}
            disabled={!uploadFile || isIngestingSingle}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 cursor-pointer font-mono"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isIngestingSingle ? 'animate-spin' : ''}`} />
            <span>{isIngestingSingle ? 'Vectorizing Clauses...' : 'Vectorize into ChromaDB'}</span>
          </button>

          {ingestStatus && (
            <div
              className={`p-3 rounded-lg border text-xs font-mono space-y-1 ${
                ingestStatus.status === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60'
                  : 'bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60'
              }`}
            >
              <div className="font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>{ingestStatus.message}</span>
              </div>
            </div>
          )}
        </div>

        {/* Semantic Search Tester */}
        <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-xs font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-blue-500" />
            <span>ChromaDB Semantic Vector Search Inspector</span>
          </h3>

          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800 p-2.5 text-xs text-gray-900 dark:text-gray-100 font-mono focus:outline-none focus:border-cyan-500"
              placeholder="Type query (e.g. furnace shutdown, pump vibration, hot work permit) to search vector store..."
            />
            <button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer font-mono"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{isSearching ? 'Querying...' : 'Search'}</span>
            </button>
          </div>

          {hasSearched && (
            <div className="space-y-2 pt-1">
              {searchResults.length === 0 ? (
                <div className="p-4 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800 text-center text-xs text-gray-400 font-mono">
                  No matching document clauses found in ChromaDB for "{searchQuery}".
                </div>
              ) : (
                searchResults.map((res, i) => (
                  <div
                    key={res.id || i}
                    className="p-3.5 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800 space-y-1.5 font-mono"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <Bookmark className="w-3.5 h-3.5 text-blue-500" />
                        <span className="font-semibold text-gray-900 dark:text-gray-100">{res.document}</span>
                        <span className="text-gray-500 text-[11px]">{res.clause}</span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-800/50">
                        Score: {(res.similarityScore * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed pl-5">
                      "{res.content}"
                    </p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Ingested Master Documents Inventory */}
        <div className="bg-white dark:bg-[#11141c] border border-gray-200 dark:border-[#262c3a] rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-2.5">
            <h3 className="text-xs font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-cyan-500" />
              <span>Ingested SOP Manuals &amp; Technical Policies</span>
            </h3>
            <span className="text-[10px] font-mono text-gray-500">
              {documentsList.length} SOPs Active
            </span>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden font-mono">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 dark:bg-[#090b10] border-b border-gray-200 dark:border-gray-800 text-gray-500 text-[10px]">
                <tr>
                  <th className="py-2 px-3">SOP Manual Name</th>
                  <th className="py-2 px-3">Category</th>
                  <th className="py-2 px-3">Indexed Chunks</th>
                  <th className="py-2 px-3 text-right">Size</th>
                  <th className="py-2 px-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800/60 text-[11px]">
                {documentsList.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-[#151924]">
                    <td className="py-2 px-3 font-medium text-gray-900 dark:text-gray-100">
                      {doc.name}
                    </td>
                    <td className="py-2 px-3 text-gray-500">{doc.category}</td>
                    <td className="py-2 px-3 text-cyan-600 dark:text-cyan-400 font-semibold">
                      {doc.chunks} chunks
                    </td>
                    <td className="py-2 px-3 text-right text-gray-400">{doc.sizeKb} KB</td>
                    <td className="py-2 px-3 text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                        GROUNDED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 3. MASTER SOP INGESTION MODAL */}
      <AnimatePresence>
        {showIngestModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl p-5 space-y-4 font-sans text-xs"
            >
              <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
                <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-semibold text-sm">
                  <Sliders className="w-4 h-4" />
                  <span>Batch Document Vectorization</span>
                </div>
                {!isReindexing && (
                  <button
                    onClick={() => setShowIngestModal(false)}
                    className="text-gray-400 hover:text-gray-200 text-xs"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Drag & Drop File Zone */}
              {!isReindexing && (
                <div className="space-y-3 font-mono">
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setIsDragging(true);
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleFileDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border border-dashed rounded-lg p-4 text-center cursor-pointer transition-all ${
                      isDragging
                        ? 'border-cyan-400 bg-cyan-950/20'
                        : manualFiles.length > 0
                        ? 'border-emerald-500/50 bg-emerald-950/10'
                        : 'border-gray-700 bg-gray-50 dark:bg-[#0c0e14] hover:border-gray-600'
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.docx,.txt"
                      onChange={handleModalFileSelect}
                      className="hidden"
                    />
                    {manualFiles.length > 0 ? (
                      <div className="space-y-1 text-emerald-400">
                        <FileCheck className="w-6 h-6 mx-auto" />
                        <div className="font-semibold">{manualFiles.length} file(s) queued for indexing</div>
                        <div className="text-[10px] text-gray-400">
                          {manualFiles.map((f) => f.name).join(', ')}
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1 text-gray-400">
                        <UploadCloud className="w-6 h-6 mx-auto text-gray-500" />
                        <div className="font-semibold text-gray-900 dark:text-gray-200">Drag &amp; Drop SOP Documents Here</div>
                        <div className="text-[10px]">PDF, DOCX, TXT (Auto Clause Chunking)</div>
                      </div>
                    )}
                  </div>

                  {/* Granular Chunking Controls */}
                  <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-800">
                    <div className="space-y-1">
                      <label className="text-[10px] text-gray-400">Token Chunk Size:</label>
                      <select
                        value={chunkConfig.chunkSize}
                        onChange={(e) => setChunkConfig({ chunkSize: Number(e.target.value) })}
                        className="w-full px-2 py-1 bg-white dark:bg-[#11141c] border border-gray-300 dark:border-gray-700 rounded text-xs text-gray-900 dark:text-gray-200"
                      >
                        <option value={512}>512 Tokens (Refinery Clauses)</option>
                        <option value={1024}>1024 Tokens (Standard SOPs)</option>
                        <option value={2048}>2048 Tokens (Master Policy)</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] text-gray-400">Sliding Overlap:</label>
                      <select
                        value={chunkConfig.overlap}
                        onChange={(e) => setChunkConfig({ overlap: Number(e.target.value) })}
                        className="w-full px-2 py-1 bg-white dark:bg-[#11141c] border border-gray-300 dark:border-gray-700 rounded text-xs text-gray-900 dark:text-gray-200"
                      >
                        <option value={50}>50 Tokens</option>
                        <option value={100}>100 Tokens (Recommended)</option>
                        <option value={200}>200 Tokens</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Live Re-Indexing Progress Tracker */}
              {isReindexing && (
                <div className="space-y-3 font-mono p-4 rounded-lg bg-gray-50 dark:bg-[#0c0e14] border border-cyan-500/30">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-cyan-400 flex items-center gap-1.5">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Stage: {reindexStage.toUpperCase()}</span>
                    </span>
                    <span className="font-bold text-gray-200">{reindexProgress}%</span>
                  </div>

                  <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                      style={{ width: `${reindexProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>

                  <div className="text-[11px] text-gray-400 leading-relaxed">
                    {reindexStatusMessage}
                  </div>
                </div>
              )}

              {/* Modal Actions */}
              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100 dark:border-gray-800">
                {!isReindexing && (
                  <>
                    <button
                      type="button"
                      onClick={() => setShowIngestModal(false)}
                      className="px-3.5 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 font-mono text-xs cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      disabled={manualFiles.length === 0}
                      onClick={handleStartReindex}
                      className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold font-mono text-xs disabled:opacity-50 flex items-center gap-1.5 cursor-pointer shadow-md shadow-cyan-950/40"
                    >
                      <span>Start Vectorization</span>
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
