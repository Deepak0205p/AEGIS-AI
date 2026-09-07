'use client';

import React, { useState, useEffect } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Plus,
  Trash2,
  Download,
  RotateCcw,
  RotateCw,
  Bold,
  Italic,
  Underline,
  Strikethrough,
  AlignLeft,
  AlignCenter,
  AlignRight,
  DollarSign,
  Percent,
  FileSpreadsheet,
  Sigma,
  Eraser,
  ZoomIn,
  ZoomOut,
  FolderPlus,
  ArrowUpDown,
  Table,
  Check,
  Printer,
  ChevronDown
} from 'lucide-react';
import { CustomDropdown } from '@/components/ui/CustomDropdown';
import { motion, AnimatePresence } from 'framer-motion';

interface UniverSheetEditorProps {
  deliverable: DeliverableItem;
}

export interface CellStyle {
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  strikethrough?: boolean;
  color?: string;
  bgColor?: string;
  align?: 'left' | 'center' | 'right';
  fontSize?: number;
  fontFamily?: string;
  format?: 'general' | 'currency' | 'percent' | 'number';
}

export interface SheetCell {
  value: string;
  formula?: string;
  style?: CellStyle;
  isHeader?: boolean;
}

export interface SheetTab {
  id: string;
  name: string;
  rows: SheetCell[][];
  colWidths?: number[];
}

const CELL_BG_PALETTE = [
  { label: 'White', value: '#ffffff' },
  { label: 'Soft Green', value: '#f0fdf4' },
  { label: 'Ice Blue', value: '#f0f9ff' },
  { label: 'Amber Light', value: '#fffbeb' },
  { label: 'Slate Gray', value: '#f1f5f9' },
  { label: 'Rose Light', value: '#fff1f2' }
];

export function UniverSheetEditor({ deliverable }: UniverSheetEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [activeRibbonTab, setActiveRibbonTab] = useState<'home' | 'insert' | 'formulas' | 'data' | 'view'>('home');
  const [activeSheetIndex, setActiveSheetIndex] = useState(0);
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number }>({ row: 1, col: 1 });
  const [formulaInput, setFormulaInput] = useState('');
  const [zoomLevel, setZoomLevel] = useState(100);
  const [showGridlines, setShowGridlines] = useState(true);
  const [showFormulaBar, setShowFormulaBar] = useState(true);
  const [selectedFont, setSelectedFont] = useState('Inter');
  const [selectedFontSize, setSelectedFontSize] = useState(12);
  const [copied, setCopied] = useState(false);

  // Pre-configured refinery spreadsheet templates based on deliverable ID/filename
  const getInitialSheets = (): SheetTab[] => {
    if (editedContent[deliverable.id]?.sheets) {
      return editedContent[deliverable.id].sheets;
    }

    if (deliverable.filename.toLowerCase().includes('kpi') || deliverable.filename.toLowerCase().includes('hse')) {
      return [
        {
          id: 'sheet-1',
          name: 'Safety KPIs FY26',
          rows: [
            [
              { value: 'Metric Parameter', isHeader: true, style: { bold: true, align: 'left', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Q1 Actual', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Q2 Actual', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Q3 Forecast', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Q4 Target', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'YTD Total / Avg', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'OISD Status', isHeader: true, style: { bold: true, align: 'center', bgColor: '#f1f5f9', color: '#0f172a' } },
            ],
            [
              { value: 'Safe Man-Hours (M)', style: { align: 'left' } },
              { value: '1.20', style: { align: 'right', format: 'number' } },
              { value: '1.18', style: { align: 'right', format: 'number' } },
              { value: '1.22', style: { align: 'right', format: 'number' } },
              { value: '1.22', style: { align: 'right', format: 'number' } },
              { value: '4.82', formula: '=SUM(B2:E2)', style: { align: 'right', bold: true, color: '#15803d' } },
              { value: 'COMPLIANT', style: { align: 'center', bold: true, color: '#15803d' } },
            ],
            [
              { value: 'Lost Time Injury Frequency (LTIFR)', style: { align: 'left' } },
              { value: '0.00', style: { align: 'right', format: 'number' } },
              { value: '0.00', style: { align: 'right', format: 'number' } },
              { value: '0.00', style: { align: 'right', format: 'number' } },
              { value: '0.00', style: { align: 'right', format: 'number' } },
              { value: '0.00', formula: '=AVERAGE(B3:E3)', style: { align: 'right', bold: true, color: '#15803d' } },
              { value: 'ZERO HARM', style: { align: 'center', bold: true, color: '#15803d' } },
            ],
            [
              { value: 'Total Recordable Incidents (TRIR)', style: { align: 'left' } },
              { value: '0.05', style: { align: 'right', format: 'number' } },
              { value: '0.04', style: { align: 'right', format: 'number' } },
              { value: '0.02', style: { align: 'right', format: 'number' } },
              { value: '0.00', style: { align: 'right', format: 'number' } },
              { value: '0.03', formula: '=AVERAGE(B4:E4)', style: { align: 'right' } },
              { value: 'PASS (≤0.10)', style: { align: 'center', color: '#15803d', bold: true } },
            ],
            [
              { value: 'Near-Miss Reports Logged', style: { align: 'left' } },
              { value: '42', style: { align: 'right', format: 'number' } },
              { value: '56', style: { align: 'right', format: 'number' } },
              { value: '61', style: { align: 'right', format: 'number' } },
              { value: '50', style: { align: 'right', format: 'number' } },
              { value: '209', formula: '=SUM(B5:E5)', style: { align: 'right', color: '#2563eb', bold: true } },
              { value: 'PROACTIVE', style: { align: 'center', color: '#2563eb' } },
            ],
            [
              { value: 'Contractor Safety Audits', style: { align: 'left' } },
              { value: '18', style: { align: 'right', format: 'number' } },
              { value: '20', style: { align: 'right', format: 'number' } },
              { value: '22', style: { align: 'right', format: 'number' } },
              { value: '24', style: { align: 'right', format: 'number' } },
              { value: '84', formula: '=SUM(B6:E6)', style: { align: 'right' } },
              { value: 'VERIFIED', style: { align: 'center', color: '#15803d' } },
            ],
          ],
        },
        {
          id: 'sheet-2',
          name: 'Unit Breakdown',
          rows: [
            [
              { value: 'Zone / Unit', isHeader: true, style: { bold: true, align: 'left', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Near-Miss', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'First Aid', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Property Loss (₹)', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
              { value: 'Risk Rating', isHeader: true, style: { bold: true, align: 'center', bgColor: '#f1f5f9', color: '#0f172a' } },
            ],
            [
              { value: 'Unit-001 / Sample Processing', style: { align: 'left' } },
              { value: '14', style: { align: 'right' } },
              { value: '1', style: { align: 'right' } },
              { value: '0', style: { align: 'right' } },
              { value: 'LOW', style: { align: 'center', color: '#15803d' } },
            ],
            [
              { value: 'FCCU Reactor & Regenerator', style: { align: 'left' } },
              { value: '19', style: { align: 'right' } },
              { value: '0', style: { align: 'right' } },
              { value: '0', style: { align: 'right' } },
              { value: 'LOW', style: { align: 'center', color: '#15803d' } },
            ],
            [
              { value: 'DHDS / Diesel Hydrotreater', style: { align: 'left' } },
              { value: '11', style: { align: 'right' } },
              { value: '0', style: { align: 'right' } },
              { value: '0', style: { align: 'right' } },
              { value: 'LOW', style: { align: 'center', color: '#15803d' } },
            ],
          ],
        },
      ];
    }

    return [
      {
        id: 'sheet-1',
        name: 'Assay Mass Balance',
        rows: [
          [
            { value: 'Equipment / Stream', isHeader: true, style: { bold: true, align: 'left', bgColor: '#f1f5f9', color: '#0f172a' } },
            { value: 'Operating Temp (°C)', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
            { value: 'Pressure (kg/cm²g)', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
            { value: 'Flow Rate (m³/hr)', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
            { value: 'Efficiency (%)', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
            { value: 'Status', isHeader: true, style: { bold: true, align: 'center', bgColor: '#f1f5f9', color: '#0f172a' } },
          ],
          [
            { value: 'No data available', style: { align: 'left' } },
            { value: '-', style: { align: 'right' } },
            { value: '-', style: { align: 'right' } },
            { value: '-', style: { align: 'right' } },
            { value: '-', style: { align: 'right' } },
            { value: 'N/A', style: { align: 'center', bold: true } },
          ],
        ],
      },
    ];
  };

  const [sheets, setSheets] = useState<SheetTab[]>(getInitialSheets);
  const [isLoadingContent, setIsLoadingContent] = useState(false);

  useEffect(() => {
    // 1. Initial local state setup
    const initial = getInitialSheets();
    setSheets(initial);

    // 2. Automatically fetch genuine parsed .xlsx data from live backend
    const fetchLiveContent = async () => {
      const cleanId = deliverable.id.replace(/^\/api\/files\/(download\/)?/, '').trim();
      if (!cleanId) return;

      const host = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
      try {
        setIsLoadingContent(true);
        const res = await fetch(`http://${host}:8000/api/files/${cleanId}/content`);
        if (res.ok) {
          const data = await res.json();
          if (data.sheets && Array.isArray(data.sheets) && data.sheets.length > 0) {
            setSheets(data.sheets);
            updateEditedContent(deliverable.id, { sheets: data.sheets });
          }
        }
      } catch (err) {
        console.warn('[UniverSheetEditor] Fallback to cached sheet view:', err);
      } finally {
        setIsLoadingContent(false);
      }
    };

    fetchLiveContent();
  }, [deliverable.id]);

  const currentSheet = sheets[activeSheetIndex] || sheets[0];

  const handleCellClick = (row: number, col: number) => {
    setSelectedCell({ row, col });
    const cell = currentSheet.rows[row]?.[col];
    setFormulaInput(cell?.formula || cell?.value || '');
  };

  const handleCellValueChange = (row: number, col: number, newValue: string) => {
    const newSheets = [...sheets];
    const newRows = [...newSheets[activeSheetIndex].rows];
    const targetCell = { ...newRows[row][col] };

    if (newValue.startsWith('=')) {
      targetCell.formula = newValue;
      targetCell.value = 'CALC';
    } else {
      targetCell.value = newValue;
      targetCell.formula = undefined;
    }

    newRows[row][col] = targetCell;
    newSheets[activeSheetIndex].rows = newRows;
    setSheets(newSheets);
    updateEditedContent(deliverable.id, { sheets: newSheets });
  };

  const handleApplyStyle = (stylePatch: Partial<CellStyle>) => {
    const { row, col } = selectedCell;
    const newSheets = [...sheets];
    const newRows = [...newSheets[activeSheetIndex].rows];
    const targetCell = { ...newRows[row][col] };
    targetCell.style = { ...targetCell.style, ...stylePatch };
    newRows[row][col] = targetCell;
    newSheets[activeSheetIndex].rows = newRows;
    setSheets(newSheets);
    updateEditedContent(deliverable.id, { sheets: newSheets });
  };

  const handleAddSheet = () => {
    const newSheet: SheetTab = {
      id: `sheet-${Date.now()}`,
      name: `Sheet ${sheets.length + 1}`,
      rows: [
        [
          { value: 'Parameter', isHeader: true, style: { bold: true, align: 'left', bgColor: '#f1f5f9', color: '#0f172a' } },
          { value: 'Value', isHeader: true, style: { bold: true, align: 'right', bgColor: '#f1f5f9', color: '#0f172a' } },
          { value: 'Status', isHeader: true, style: { bold: true, align: 'center', bgColor: '#f1f5f9', color: '#0f172a' } },
        ],
        [
          { value: 'Item 1', style: { align: 'left' } },
          { value: '100.0', style: { align: 'right' } },
          { value: 'PASS', style: { align: 'center', color: '#15803d', bold: true } },
        ],
      ],
    };
    const newSheets = [...sheets, newSheet];
    setSheets(newSheets);
    setActiveSheetIndex(newSheets.length - 1);
    updateEditedContent(deliverable.id, { sheets: newSheets });
  };

  const handleAddRow = () => {
    const newSheets = [...sheets];
    const colCount = newSheets[activeSheetIndex].rows[0]?.length || 5;
    const blankRow: SheetCell[] = Array.from({ length: colCount }).map(() => ({
      value: '',
      style: { align: 'left' },
    }));
    newSheets[activeSheetIndex].rows.push(blankRow);
    setSheets(newSheets);
    updateEditedContent(deliverable.id, { sheets: newSheets });
  };

  const exportCSV = () => {
    const csvContent = currentSheet.rows
      .map((r) => r.map((c) => `"${c.value.replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${deliverable.filename.replace(/\.[^/.]+$/, '')}_${currentSheet.name}.csv`);
    link.click();
  };

  // Calculate live statistics for numerical values in sheet
  const calculateStats = () => {
    let sum = 0;
    let count = 0;
    currentSheet.rows.slice(1).forEach((row) => {
      row.forEach((c) => {
        const num = parseFloat(c.value);
        if (!isNaN(num)) {
          sum += num;
          count++;
        }
      });
    });
    return {
      sum: sum.toFixed(2),
      avg: count > 0 ? (sum / count).toFixed(2) : '0.00',
      count,
    };
  };

  const stats = calculateStats();

  return (
    <div className="flex flex-col h-full bg-[#f8fafc] text-[#1e293b] select-none font-sans relative overflow-hidden">
      {/* 1. TOP STUDIO RIBBON HEADER (Mobile Scrollable) */}
      <div className="flex items-center justify-between px-2 sm:px-4 pt-2 pb-1 bg-white border-b border-[#e2e8f0] text-xs shrink-0 shadow-xs gap-2 overflow-x-auto scrollbar-none">
        {/* Left: Tab Switcher */}
        <div className="flex items-center space-x-1 p-0.5 sm:p-1 bg-[#f1f5f9] rounded-xl border border-[#e2e8f0] shrink-0">
          {(['home', 'insert', 'formulas', 'data', 'view'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveRibbonTab(tab)}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg font-semibold text-xs transition-all capitalize whitespace-nowrap ${
                activeRibbonTab === tab
                  ? 'bg-white text-[#15803d] shadow-sm font-bold'
                  : 'text-[#64748b] hover:text-[#0f172a] hover:bg-white/50'
              }`}
            >
              {tab === 'data' ? 'Data & Sort' : tab}
            </button>
          ))}
        </div>

        {/* Right Header Actions */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={exportCSV}
            className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3.5 py-1.5 rounded-xl bg-[#15803d] hover:bg-[#166534] text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer shrink-0"
            title="Download CSV / Excel"
          >
            <Download className="h-3.5 w-3.5" />
            <span className="hidden xs:inline">Export CSV</span>
          </button>
        </div>
      </div>

      {/* 2. RIBBON ACTION TOOLBAR */}
      <div className="flex items-center gap-2 px-2 sm:px-4 py-2 bg-white border-b border-[#e2e8f0] text-xs shadow-xs relative z-20 shrink-0 overflow-x-auto scrollbar-none flex-nowrap">
        {activeRibbonTab === 'home' && (
          <>
            {/* Font Family & Size (Custom Dropdowns) */}
            <div className="flex items-center space-x-1.5 pr-2.5 border-r border-[#e2e8f0]">
              <CustomDropdown
                value={selectedFont}
                onChange={(val) => {
                  setSelectedFont(val);
                  handleApplyStyle({ fontFamily: val });
                }}
                size="xs"
                options={[
                  { value: 'Inter', label: 'Inter' },
                  { value: 'Arial', label: 'Arial' },
                  { value: 'Georgia', label: 'Georgia' },
                  { value: 'JetBrains Mono', label: 'JetBrains Mono' },
                ]}
                buttonClassName="bg-[#f8fafc] text-[#0f172a] border-[#cbd5e1] rounded-lg font-semibold"
              />

              <CustomDropdown
                value={selectedFontSize}
                onChange={(val) => {
                  setSelectedFontSize(Number(val));
                  handleApplyStyle({ fontSize: Number(val) });
                }}
                size="xs"
                options={[
                  { value: 10, label: '10pt' },
                  { value: 11, label: '11pt' },
                  { value: 12, label: '12pt' },
                  { value: 14, label: '14pt' },
                  { value: 16, label: '16pt' },
                ]}
                buttonClassName="bg-[#f8fafc] text-[#0f172a] border-[#cbd5e1] rounded-lg font-semibold w-16"
              />
            </div>

            {/* Typography Styles */}
            <div className="flex items-center space-x-0.5 pr-2.5 border-r border-[#e2e8f0]">
              <button
                onClick={() => handleApplyStyle({ bold: !currentSheet.rows[selectedCell.row]?.[selectedCell.col]?.style?.bold })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
                title="Bold (Ctrl+B)"
              >
                <Bold className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleApplyStyle({ italic: !currentSheet.rows[selectedCell.row]?.[selectedCell.col]?.style?.italic })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
                title="Italic (Ctrl+I)"
              >
                <Italic className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleApplyStyle({ underline: !currentSheet.rows[selectedCell.row]?.[selectedCell.col]?.style?.underline })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
                title="Underline (Ctrl+U)"
              >
                <Underline className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Cell Background Color Picker */}
            <div className="flex items-center space-x-1.5 pr-2.5 border-r border-[#e2e8f0]">
              <span className="text-[#64748b] font-bold text-[10px] uppercase">Fill:</span>
              <div className="flex items-center space-x-1">
                {CELL_BG_PALETTE.map((c) => (
                  <button
                    key={c.value}
                    onClick={() => handleApplyStyle({ bgColor: c.value })}
                    style={{ backgroundColor: c.value }}
                    className="h-5 w-5 rounded-md border border-[#cbd5e1] hover:scale-110 transition-transform shadow-2xs cursor-pointer"
                    title={c.label}
                  />
                ))}
              </div>
            </div>

            {/* Alignments */}
            <div className="flex items-center space-x-0.5 pr-2.5 border-r border-[#e2e8f0]">
              <button
                onClick={() => handleApplyStyle({ align: 'left' })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]"
                title="Align Left"
              >
                <AlignLeft className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleApplyStyle({ align: 'center' })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]"
                title="Align Center"
              >
                <AlignCenter className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleApplyStyle({ align: 'right' })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]"
                title="Align Right"
              >
                <AlignRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Number Formats */}
            <div className="flex items-center space-x-1 pr-2.5 border-r border-[#e2e8f0]">
              <button
                onClick={() => handleApplyStyle({ format: 'currency' })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#15803d] font-bold text-xs"
                title="Currency Format"
              >
                $
              </button>
              <button
                onClick={() => handleApplyStyle({ format: 'percent' })}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-blue-700 font-bold text-xs"
                title="Percentage Format"
              >
                %
              </button>
            </div>

            {/* Clear Formatting */}
            <button
              onClick={() => handleApplyStyle({ bold: false, italic: false, underline: false, bgColor: '#ffffff', color: '#0f172a' })}
              className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#64748b] hover:text-[#0f172a]"
              title="Clear Cell Formatting"
            >
              <Eraser className="h-3.5 w-3.5" />
            </button>
          </>
        )}

        {activeRibbonTab === 'insert' && (
          <div className="flex items-center space-x-2.5">
            <button
              onClick={handleAddSheet}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <FolderPlus className="h-3.5 w-3.5 text-emerald-600" />
              <span>New Worksheet</span>
            </button>
            <button
              onClick={handleAddRow}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Plus className="h-3.5 w-3.5 text-emerald-600" />
              <span>Insert Blank Row</span>
            </button>
          </div>
        )}

        {activeRibbonTab === 'formulas' && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleCellValueChange(selectedCell.row, selectedCell.col, '=SUM(B2:E2)')}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-emerald-700 font-mono font-bold text-xs"
            >
              <Sigma className="h-3.5 w-3.5" />
              <span>=SUM(...)</span>
            </button>
            <button
              onClick={() => handleCellValueChange(selectedCell.row, selectedCell.col, '=AVERAGE(B2:E2)')}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-blue-700 font-mono font-bold text-xs"
            >
              <span>=AVERAGE(...)</span>
            </button>
            <button
              onClick={() => handleCellValueChange(selectedCell.row, selectedCell.col, '=MAX(B2:E2)')}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-mono font-bold text-xs"
            >
              <span>=MAX(...)</span>
            </button>
            <button
              onClick={() => handleCellValueChange(selectedCell.row, selectedCell.col, '=MIN(B2:E2)')}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-mono font-bold text-xs"
            >
              <span>=MIN(...)</span>
            </button>
          </div>
        )}

        {activeRibbonTab === 'data' && (
          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => {
                const newSheets = [...sheets];
                const rows = [...newSheets[activeSheetIndex].rows];
                const header = rows[0];
                const dataRows = rows.slice(1);
                dataRows.sort((a, b) => (a[selectedCell.col]?.value || '').localeCompare(b[selectedCell.col]?.value || ''));
                newSheets[activeSheetIndex].rows = [header, ...dataRows];
                setSheets(newSheets);
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold"
            >
              <ArrowUpDown className="h-3.5 w-3.5 text-blue-600" />
              <span>Sort Column (A → Z)</span>
            </button>
          </div>
        )}

        {activeRibbonTab === 'view' && (
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-1.5 text-xs text-[#475569] font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={showGridlines}
                onChange={(e) => setShowGridlines(e.target.checked)}
                className="rounded border-[#cbd5e1] text-emerald-600 focus:ring-emerald-500"
              />
              <span>Gridlines</span>
            </label>
            <label className="flex items-center space-x-1.5 text-xs text-[#475569] font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={showFormulaBar}
                onChange={(e) => setShowFormulaBar(e.target.checked)}
                className="rounded border-[#cbd5e1] text-emerald-600 focus:ring-emerald-500"
              />
              <span>Formula Bar</span>
            </label>
            <div className="flex items-center space-x-1.5 bg-[#f8fafc] border border-[#cbd5e1] rounded-lg px-2.5 py-1">
              <button onClick={() => setZoomLevel((z) => Math.max(50, z - 15))} className="p-1 hover:bg-[#e2e8f0] rounded text-[#475569]">
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span className="text-[11px] font-mono text-[#0f172a] font-bold">{zoomLevel}%</span>
              <button onClick={() => setZoomLevel((z) => Math.min(200, z + 15))} className="p-1 hover:bg-[#e2e8f0] rounded text-[#475569]">
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setZoomLevel(100)}
                className="text-[10px] font-semibold text-[#64748b] hover:text-[#0f172a] px-1.5 py-0.5 rounded"
              >
                Reset
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 3. FORMULA BAR */}
      {showFormulaBar && (
        <div className="flex items-center space-x-2 px-2.5 sm:px-4 py-1.5 sm:py-2 bg-white border-b border-[#e2e8f0] shadow-2xs">
          <div className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-[#f1f5f9] border border-[#cbd5e1] text-[11px] font-mono text-[#0f172a] font-bold min-w-[48px] justify-center shadow-xs shrink-0">
            {String.fromCharCode(65 + selectedCell.col)}
            {selectedCell.row + 1}
          </div>
          <div className="text-[13px] font-mono font-black text-emerald-700 select-none shrink-0">fx</div>
          <input
            type="text"
            value={formulaInput}
            onChange={(e) => {
              setFormulaInput(e.target.value);
              handleCellValueChange(selectedCell.row, selectedCell.col, e.target.value);
            }}
            placeholder="Type cell value or formula (=SUM(B2:E2)...)"
            className="flex-1 bg-[#f8fafc] text-[#0f172a] text-xs font-mono px-2.5 sm:px-3 py-1.5 rounded-lg border border-[#cbd5e1] focus:border-emerald-600 focus:bg-white focus:outline-none placeholder-[#94a3b8] transition-colors min-w-0"
          />
        </div>
      )}

      {/* 4. SPREADSHEET GRID */}
      <div
        className="flex-1 overflow-auto bg-white"
        style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top left' }}
      >
        <table className={`w-full border-collapse font-sans text-xs ${showGridlines ? '' : 'border-transparent'}`}>
          <thead>
            <tr className="bg-[#f8fafc] border-b border-[#cbd5e1] sticky top-0 z-10 select-none">
              <th className="w-10 sm:w-12 px-2 py-2 text-center text-[10px] font-mono font-bold text-[#64748b] border-r border-[#cbd5e1] bg-[#f1f5f9]">
                #
              </th>
              {currentSheet.rows[0]?.map((_, colIdx) => (
                <th
                  key={colIdx}
                  className="px-2.5 sm:px-3.5 py-2 text-center font-mono text-[11px] font-bold text-[#475569] border-r border-[#cbd5e1] min-w-[95px] sm:min-w-[130px]"
                >
                  {String.fromCharCode(65 + colIdx)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentSheet.rows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={`border-b border-[#e2e8f0] hover:bg-slate-50/80 transition-colors ${
                  rowIdx === 0 ? 'bg-[#f8fafc] font-bold text-[#0f172a]' : ''
                }`}
              >
                {/* Row Header Number */}
                <td className="px-2 sm:px-2.5 py-2 text-center text-[10px] font-mono font-bold text-[#64748b] bg-[#f1f5f9] border-r border-[#cbd5e1] select-none">
                  {rowIdx + 1}
                </td>

                {/* Grid Cells */}
                {row.map((cell, colIdx) => {
                  const isSelected = selectedCell.row === rowIdx && selectedCell.col === colIdx;
                  return (
                    <td
                      key={colIdx}
                      onClick={() => handleCellClick(rowIdx, colIdx)}
                      style={{
                        backgroundColor: cell.style?.bgColor || (rowIdx === 0 ? '#f8fafc' : '#ffffff'),
                        color: cell.style?.color || '#0f172a',
                        fontWeight: cell.style?.bold ? 'bold' : 'normal',
                        fontStyle: cell.style?.italic ? 'italic' : 'normal',
                        textDecoration: cell.style?.underline ? 'underline' : 'none',
                        textAlign: cell.style?.align || (colIdx === 0 ? 'left' : 'right'),
                      }}
                      className={`px-2.5 sm:px-3 py-1.5 border-r border-[#e2e8f0] transition-all relative ${
                        isSelected
                          ? 'ring-2 ring-[#15803d] bg-emerald-50/40 z-10'
                          : ''
                      }`}
                    >
                      <input
                        type="text"
                        value={cell.value}
                        onChange={(e) => handleCellValueChange(rowIdx, colIdx, e.target.value)}
                        className="w-full bg-transparent border-none outline-none text-xs font-medium cursor-pointer focus:cursor-text"
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 5. BOTTOM WORKSHEETS TAB BAR & STATUS FOOTER */}
      <div className="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-2.5 bg-[#f1f5f9] border-t border-[#cbd5e1] text-xs shrink-0 shadow-xs overflow-x-auto scrollbar-none gap-3">
        {/* Left: Sheet Tabs */}
        <div className="flex items-center space-x-1.5 shrink-0">
          {sheets.map((sheet, idx) => (
            <button
              key={sheet.id}
              onClick={() => {
                setActiveSheetIndex(idx);
                setSelectedCell({ row: 1, col: 1 });
              }}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl font-bold text-xs transition-all cursor-pointer whitespace-nowrap ${
                activeSheetIndex === idx
                  ? 'bg-white text-[#15803d] border border-[#cbd5e1] shadow-xs ring-1 ring-emerald-500/20'
                  : 'text-[#64748b] hover:text-[#0f172a] hover:bg-white/60'
              }`}
            >
              <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
              <span>{sheet.name}</span>
            </button>
          ))}
          <button
            onClick={handleAddSheet}
            className="p-1.5 rounded-xl hover:bg-white text-emerald-700 border border-transparent hover:border-[#cbd5e1] transition-all cursor-pointer shrink-0"
            title="Add New Worksheet"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        {/* Right: Live Cell Statistics */}
        <div className="flex items-center space-x-2 sm:space-x-3 text-[11px] text-[#64748b] font-mono shrink-0">
          <span>SUM: <strong className="text-[#15803d]">{stats.sum}</strong></span>
          <span>&bull;</span>
          <span>AVG: <strong className="text-blue-700">{stats.avg}</strong></span>
          <span className="hidden sm:inline">&bull;</span>
          <span className="hidden sm:inline">COUNT: <strong className="text-[#0f172a]">{stats.count}</strong></span>
          <span>&bull;</span>
          <span className="text-[#15803d] font-sans font-bold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[#15803d] animate-pulse" />
            Excel Studio
          </span>
        </div>
      </div>
    </div>
  );
}
