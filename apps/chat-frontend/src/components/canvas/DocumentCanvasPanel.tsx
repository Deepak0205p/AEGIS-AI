'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCanvasStore } from '@/store/useCanvasStore';
import { useDeliverableStore } from '@/store/useDeliverableStore';
import dynamic from 'next/dynamic';

const UniverSheetEditor = dynamic(
  () => import('./UniverSheetEditor').then((mod) => mod.UniverSheetEditor),
  { ssr: false }
);
const UniverDocEditor = dynamic(
  () => import('./UniverDocEditor').then((mod) => mod.UniverDocEditor),
  { ssr: false }
);
const UniverSlideEditor = dynamic(
  () => import('./UniverSlideEditor').then((mod) => mod.UniverSlideEditor),
  { ssr: false }
);
const PythonCanvasEditor = dynamic(
  () => import('./PythonCanvasEditor').then((mod) => mod.PythonCanvasEditor),
  { ssr: false }
);
const SqlCanvasEditor = dynamic(
  () => import('./SqlCanvasEditor').then((mod) => mod.SqlCanvasEditor),
  { ssr: false }
);
const WebCanvasEditor = dynamic(
  () => import('./WebCanvasEditor').then((mod) => mod.WebCanvasEditor),
  { ssr: false }
);
const JsonYamlCanvasEditor = dynamic(
  () => import('./JsonYamlCanvasEditor').then((mod) => mod.JsonYamlCanvasEditor),
  { ssr: false }
);
const TsJsCanvasEditor = dynamic(
  () => import('./TsJsCanvasEditor').then((mod) => mod.TsJsCanvasEditor),
  { ssr: false }
);
const ShellSystemsCanvasEditor = dynamic(
  () => import('./ShellSystemsCanvasEditor').then((mod) => mod.ShellSystemsCanvasEditor),
  { ssr: false }
);

import {
  X,
  Maximize2,
  Minimize2,
  Download,
  Save,
  FileText,
  FileSpreadsheet,
  Presentation,
  Code,
  Database,
  Globe,
  Braces,
  Terminal,
  FileCode2,
  Edit2,
  Check as CheckIcon,
  X as CancelIcon,
  ShieldCheck
} from 'lucide-react';
import { useVerificationStore } from '@/store/useVerificationStore';

export function DocumentCanvasPanel() {
  const {
    isOpen,
    isExpanded,
    activeDeliverable,
    closeCanvas,
    toggleExpand,
    saveChanges,
    hasUnsavedChanges,
    isSaving,
    renameActiveDeliverable,
  } = useCanvasStore();

  const { downloadDeliverable } = useDeliverableStore();
  const [isEditingTitle, setIsEditingTitle] = React.useState(false);
  const [editTitleValue, setEditTitleValue] = React.useState('');

  React.useEffect(() => {
    if (activeDeliverable?.filename) {
      setEditTitleValue(activeDeliverable.filename);
      setIsEditingTitle(false);
    }
  }, [activeDeliverable?.filename]);

  const handleCommitRename = async () => {
    if (editTitleValue.trim() && editTitleValue.trim() !== activeDeliverable?.filename) {
      await renameActiveDeliverable(editTitleValue.trim());
    }
    setIsEditingTitle(false);
  };

  if (!isOpen || !activeDeliverable) return null;

  const filename = activeDeliverable.filename.toLowerCase();
  const deliverableType = (activeDeliverable.type || '').toLowerCase();

  // 1. Automatic Extension & Language Category Resolver
  const getExtension = () => {
    const dotIdx = filename.lastIndexOf('.');
    if (dotIdx !== -1) {
      const extracted = filename.slice(dotIdx).toLowerCase();
      if (['.docx', '.doc', '.xlsx', '.xls', '.csv', '.pptx', '.ppt', '.py', '.ipynb', '.sql', '.html', '.htm', '.svg', '.xml', '.css', '.json', '.yaml', '.yml', '.env', '.toml', '.ts', '.tsx', '.js', '.jsx', '.sh', '.bash'].includes(extracted)) {
        return extracted;
      }
    }
    if (['docx', 'doc', 'xlsx', 'xls', 'csv', 'pptx', 'ppt', 'py', 'ipynb', 'sql', 'html', 'json', 'ts', 'js', 'sh'].includes(deliverableType)) {
      return `.${deliverableType}`;
    }
    return '.docx';
  };

  const ext = getExtension();

  // 2. Icon Resolver based on extension
  const renderFileIcon = () => {
    if (['.xlsx', '.xls', '.csv'].includes(ext) || deliverableType === 'xlsx') {
      return <FileSpreadsheet className="h-5 w-5 text-emerald-600" />;
    }
    if (['.pptx', '.ppt'].includes(ext) || deliverableType === 'pptx') {
      return <Presentation className="h-5 w-5 text-orange-600" />;
    }
    if (['.docx', '.doc'].includes(ext) || deliverableType === 'docx' || deliverableType === '') {
      return <FileText className="h-5 w-5 text-blue-600" />;
    }
    if (['.py', '.ipynb'].includes(ext) || deliverableType === 'py') {
      return <span className="text-base">🐍</span>;
    }
    if (['.sql'].includes(ext)) {
      return <Database className="h-5 w-5 text-blue-600" />;
    }
    if (['.html', '.htm', '.svg', '.xml', '.css'].includes(ext)) {
      return <Globe className="h-5 w-5 text-orange-500" />;
    }
    if (['.json', '.yaml', '.yml', '.env', '.toml'].includes(ext)) {
      return <Braces className="h-5 w-5 text-emerald-600" />;
    }
    if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
      return <FileCode2 className="h-5 w-5 text-blue-500" />;
    }
    return <FileText className="h-5 w-5 text-blue-600" />;
  };

  // 3. Dedicated Language Viewer Component Resolver
  const renderEditorComponent = () => {
    // Spreadsheets
    if (['.xlsx', '.xls', '.csv'].includes(ext) || deliverableType === 'xlsx') {
      return <UniverSheetEditor deliverable={activeDeliverable} />;
    }
    // Presentations
    if (['.pptx', '.ppt'].includes(ext) || deliverableType === 'pptx') {
      return <UniverSlideEditor deliverable={activeDeliverable} />;
    }
    // Python Logic & Data Scripts
    if (['.py', '.ipynb'].includes(ext) || deliverableType === 'py') {
      return <PythonCanvasEditor deliverable={activeDeliverable} />;
    }
    // SQL Queries & Database Views
    if (['.sql'].includes(ext)) {
      return <SqlCanvasEditor deliverable={activeDeliverable} />;
    }
    // Web HTML / CSS / SVG Markup
    if (['.html', '.htm', '.svg', '.xml', '.css'].includes(ext)) {
      return <WebCanvasEditor deliverable={activeDeliverable} />;
    }
    // JSON / YAML Data Schemas
    if (['.json', '.yaml', '.yml', '.env', '.toml'].includes(ext)) {
      return <JsonYamlCanvasEditor deliverable={activeDeliverable} />;
    }
    // TypeScript & JavaScript
    if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
      return <TsJsCanvasEditor deliverable={activeDeliverable} />;
    }
    // Shell Script specifically
    if (['.sh', '.bash', '.zsh'].includes(ext) || deliverableType === 'sh') {
      return <ShellSystemsCanvasEditor deliverable={activeDeliverable} />;
    }
    // Default: Word Documents (.docx, .doc, templates, general reports)
    return <UniverDocEditor deliverable={activeDeliverable} />;
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 28, stiffness: 240 }}
        className={`fixed md:relative inset-0 md:inset-auto bg-[#ffffff] border-l border-[#cbd5e1] dark:border-white/10 flex flex-col shadow-2xl transition-all duration-300 z-50 md:z-20 h-full overflow-hidden flex-1 ${
          isExpanded
            ? 'w-full fixed inset-0 md:absolute z-50 border-l-0'
            : 'w-full md:flex-1'
        }`}
      >
        {/* 1. Canvas Top Header (Clean Light Theme & Mobile Optimized) */}
        <div className="flex items-center justify-between px-2.5 sm:px-4 py-2 sm:py-3 bg-[#ffffff] border-b border-[#e2e8f0] shrink-0 shadow-sm gap-2">
          {/* Left: Document Info, Type Badge & Live Auto-Save Status */}
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
            <div className="p-1.5 sm:p-2 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] shrink-0">
              {renderFileIcon()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                {isEditingTitle ? (
                  <div className="flex items-center gap-1 min-w-0">
                    <input
                      type="text"
                      value={editTitleValue}
                      onChange={(e) => setEditTitleValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleCommitRename();
                        if (e.key === 'Escape') setIsEditingTitle(false);
                      }}
                      autoFocus
                      className="px-2 py-0.5 text-xs font-bold text-[#0f172a] bg-white border-2 border-blue-500 rounded-lg outline-none shadow-xs w-48 sm:w-64"
                    />
                    <button
                      onClick={handleCommitRename}
                      className="p-1 rounded-md bg-blue-50 hover:bg-blue-100 text-blue-600 cursor-pointer"
                      title="Confirm Rename"
                    >
                      <CheckIcon className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setIsEditingTitle(false)}
                      className="p-1 rounded-md hover:bg-slate-100 text-slate-400 cursor-pointer"
                      title="Cancel"
                    >
                      <CancelIcon className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 min-w-0 group/title">
                    <h2
                      onClick={() => setIsEditingTitle(true)}
                      className="text-xs sm:text-sm font-bold text-[#0f172a] truncate max-w-[120px] xs:max-w-[180px] sm:max-w-none cursor-pointer hover:text-blue-600 transition-colors"
                      title="Click to rename document"
                    >
                      {activeDeliverable.filename}
                    </h2>
                    <button
                      onClick={() => setIsEditingTitle(true)}
                      className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50/80 transition-all cursor-pointer"
                      title="Rename Document"
                    >
                      <Edit2 className="h-3 w-3" />
                    </button>
                  </div>
                )}
                <span className="px-1.5 py-0.5 rounded text-[9px] sm:text-[10px] font-bold uppercase tracking-wider bg-[#f1f5f9] border border-[#cbd5e1] text-[#334155] shrink-0">
                  {ext.replace('.', '') || activeDeliverable.type}
                </span>

                {/* Live Auto-Save Indicator in Title Bar */}
                {isSaving ? (
                  <span className="hidden sm:flex items-center space-x-1 px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 shrink-0">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse" />
                    <span>Saving...</span>
                  </span>
                ) : hasUnsavedChanges ? (
                  <span className="hidden sm:flex items-center space-x-1 px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 shrink-0">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                    <span>Editing</span>
                  </span>
                ) : (
                  <span className="hidden sm:flex items-center space-x-1 px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                    <span>Saved</span>
                  </span>
                )}
              </div>
              <p className="text-[10px] sm:text-[11px] text-[#64748b] truncate hidden sm:block">
                {activeDeliverable.source_scenario} &bull; {activeDeliverable.generating_model}
              </p>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center space-x-1 sm:space-x-2 shrink-0">
            {/* Quick Human Verification Advance Trigger */}
            <button
              onClick={async () => {
                await saveChanges(activeDeliverable.id);
                useCanvasStore.getState().closeCanvas();
                useVerificationStore.getState().openVerificationModal({
                  file_id: activeDeliverable.id,
                  chat_id: activeDeliverable.source_scenario || 'current',
                  filename: activeDeliverable.filename,
                  file_type: activeDeliverable.type,
                  verification_status: activeDeliverable.verification_status || 'PENDING_STAGE_1',
                  created_at: activeDeliverable.generated_timestamp || '',
                  download_url: `/api/files/${activeDeliverable.id}`
                });
              }}
              className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-50 hover:bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:hover:bg-blue-500/20 dark:text-[#a8c7fa] border border-blue-200 dark:border-blue-500/30 transition-all cursor-pointer shadow-xs"
              title="Save changes and open 2-step verification review"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-blue-600 dark:text-[#a8c7fa]" />
              <span className="hidden sm:inline">Verification Review</span>
            </button>

            <button
              onClick={() => saveChanges(activeDeliverable.id)}
              disabled={isSaving}
              className="flex items-center space-x-1 sm:space-x-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 transition-colors shadow-sm cursor-pointer"
            >
              <Save className="h-3.5 w-3.5" />
              <span className="hidden xs:inline">{isSaving ? 'Saving...' : 'Save'}</span>
            </button>

            <button
              onClick={() => downloadDeliverable(activeDeliverable.id)}
              className="p-1.5 sm:px-3 sm:py-1.5 rounded-lg text-xs font-medium bg-[#f8fafc] hover:bg-[#f1f5f9] text-[#1e293b] border border-[#cbd5e1] transition-colors cursor-pointer flex items-center space-x-1"
              title="Download Original Deliverable"
            >
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Download</span>
            </button>

            <button
              onClick={toggleExpand}
              className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#64748b] hover:text-[#0f172a] transition-colors hidden md:block cursor-pointer"
              title={isExpanded ? 'Split Screen' : 'Expand Fullscreen'}
            >
              {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>

            <button
              onClick={closeCanvas}
              className="p-1.5 rounded-lg hover:bg-rose-50 text-[#64748b] hover:text-rose-600 transition-colors cursor-pointer"
              title="Close Canvas"
            >
              <X className="h-4 w-4 sm:h-4.5 sm:w-4.5" />
            </button>
          </div>
        </div>

        {/* 2. Direct Dedicated Language Viewer Component */}
        <div className="flex-1 overflow-hidden relative bg-[#ffffff]">
          {renderEditorComponent()}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
