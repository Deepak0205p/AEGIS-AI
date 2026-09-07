'use client';

import React, { useState, useEffect, useRef } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Bold,
  Italic,
  Underline,
  Strikethrough,
  List,
  ListOrdered,
  Quote,
  Code,
  ShieldCheck,
  Download,
  Copy,
  Check,
  Printer,
  Sparkles,
  FileText,
  AlertCircle,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Subscript,
  Superscript,
  Highlighter,
  Eraser,
  Table,
  Minus,
  CheckSquare,
  Search,
  ZoomIn,
  ZoomOut,
  Calendar,
  Layers,
  FileCheck2,
  Type,
  ChevronDown,
  Palette,
  Undo,
  Redo,
  Clock,
  Sliders,
  CheckCircle2,
  FileEdit,
  Maximize2,
  Heading1,
  Heading2,
  Heading3
} from 'lucide-react';
import { CustomDropdown } from '@/components/ui/CustomDropdown';
import { motion, AnimatePresence } from 'framer-motion';

interface UniverDocEditorProps {
  deliverable: DeliverableItem;
}

const FONT_COLORS = [
  { label: 'Obsidian Dark', value: '#0f172a' },
  { label: 'Navy Blue', value: '#1e3a8a' },
  { label: 'Royal Blue', value: '#2563eb' },
  { label: 'Teal Cyan', value: '#0d9488' },
  { label: 'Emerald Green', value: '#16a34a' },
  { label: 'Amber Flame', value: '#ea580c' },
  { label: 'Crimson Red', value: '#dc2626' },
  { label: 'Purple Apex', value: '#7c3aed' },
  { label: 'Slate Gray', value: '#64748b' }
];

const HIGHLIGHT_COLORS = [
  { label: 'Soft Amber', value: '#fef08a' },
  { label: 'Sky Cyan', value: '#a5f3fc' },
  { label: 'Mint Green', value: '#bbf7d0' },
  { label: 'Lavender Pink', value: '#fbcfe8' },
  { label: 'Peach Orange', value: '#fed7aa' },
  { label: 'No Color', value: 'transparent' }
];

const PAGE_BG_PRESETS = [
  { label: 'Pure White', value: '#ffffff' },
  { label: 'Soft Ivory', value: '#fdfbf7' },
  { label: 'Subtle Slate', value: '#f8fafc' },
  { label: 'Clean Mint', value: '#f0fdf4' }
];

export function UniverDocEditor({ deliverable }: UniverDocEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const editorRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState<'home' | 'insert' | 'layout' | 'review' | 'view'>('home');
  const [copied, setCopied] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [selectedFont, setSelectedFont] = useState('Inter');
  const [selectedFontSize, setSelectedFontSize] = useState('3');
  const [showColorDropdown, setShowColorDropdown] = useState(false);
  const [showHighlightDropdown, setShowHighlightDropdown] = useState(false);
  const [selectedTextColor, setSelectedTextColor] = useState('#0f172a');
  const [selectedHighlightColor, setSelectedHighlightColor] = useState('#fef08a');
  const [pageBgColor, setPageBgColor] = useState('#ffffff');
  const [showRuler, setShowRuler] = useState(true);

  // Pre-configured refinery SOP document templates based on filename/ID
  const getInitialDocHtml = (): string => {
    if (editedContent[deliverable.id]?.html) {
      return editedContent[deliverable.id].html;
    }

    if (deliverable.filename.toLowerCase().includes('oisd') || deliverable.filename.toLowerCase().includes('hw-b')) {
      return `
        <h1 style="color: #1e40af; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">MRPL HOT WORK & NAKED FLAME PERMIT (FORM B)</h1>
        <p style="color: #64748b; font-size: 13px; margin-top: 6px;"><strong>Permit Serial No:</strong> MRPL/HSE/2026/HW-8902 &nbsp;|&nbsp; <strong>Date:</strong> 27-AUG-2026 &nbsp;|&nbsp; <strong>Valid Up To:</strong> 18:00 HRS IST</p>
        <p style="color: #64748b; font-size: 13px; margin-top: 2px;"><strong>Work Location / Plant Unit:</strong> Distillation Column Top Platform (Elev. +38.5m)</p>
        
        <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">1. Scope & Description of Work</h2>
        <p style="color: #1e293b; line-height: 1.7; font-size: 14px;">Replacement and plasma bevel cutting of 8-inch high-pressure crude transfer line spool (P-104A discharge). Welding and grinding work requires continuous firewatch and spark containment enclosure.</p>

        <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">2. Mandatory Pre-Entry Atmospheric 4-Gas Test Matrix</h2>
        <table style="width: 100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 18px; border: 1px solid #cbd5e1; font-size: 13px; border-radius: 8px; overflow: hidden;">
          <thead>
            <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
              <th style="padding: 10px 12px; text-align: left; border: 1px solid #cbd5e1; color: #0f172a; font-weight: 700;">Gas Parameter</th>
              <th style="padding: 10px 12px; text-align: right; border: 1px solid #cbd5e1; color: #0f172a; font-weight: 700;">Permissible Limit</th>
              <th style="padding: 10px 12px; text-align: right; border: 1px solid #cbd5e1; color: #0f172a; font-weight: 700;">Measured Value</th>
              <th style="padding: 10px 12px; text-align: center; border: 1px solid #cbd5e1; color: #0f172a; font-weight: 700;">Verdict</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border: 1px solid #e2e8f0; background-color: #ffffff;">
              <td style="padding: 9px 12px; border: 1px solid #e2e8f0; color: #334155; font-weight: 500;">Combustible Hydrocarbons (%LEL)</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #334155;">0.0% LEL</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">0.0%</td>
              <td style="padding: 9px 12px; text-align: center; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">PASS</td>
            </tr>
            <tr style="border: 1px solid #e2e8f0; background-color: #f8fafc;">
              <td style="padding: 9px 12px; border: 1px solid #e2e8f0; color: #334155; font-weight: 500;">Oxygen Concentration (O₂)</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #334155;">19.5% - 21.0%</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">20.8%</td>
              <td style="padding: 9px 12px; text-align: center; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">SAFE</td>
            </tr>
            <tr style="border: 1px solid #e2e8f0; background-color: #ffffff;">
              <td style="padding: 9px 12px; border: 1px solid #e2e8f0; color: #334155; font-weight: 500;">Hydrogen Sulfide (H₂S)</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #334155;">&lt; 10.0 ppm</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">0.0 ppm</td>
              <td style="padding: 9px 12px; text-align: center; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">PASS</td>
            </tr>
            <tr style="border: 1px solid #e2e8f0; background-color: #f8fafc;">
              <td style="padding: 9px 12px; border: 1px solid #e2e8f0; color: #334155; font-weight: 500;">Carbon Monoxide (CO)</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #334155;">&lt; 25.0 ppm</td>
              <td style="padding: 9px 12px; text-align: right; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">2.1 ppm</td>
              <td style="padding: 9px 12px; text-align: center; border: 1px solid #e2e8f0; color: #15803d; font-weight: 700;">PASS</td>
            </tr>
          </tbody>
        </table>

        <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">3. Safety Precautions & Checkpoints (OISD-STD-105)</h2>
        <ul style="color: #1e293b; line-height: 1.8; font-size: 14px;">
          <li>Equipment isolated from live hydrocarbon header by slip blinds / spectacles (Blind Tag #BL-4402).</li>
          <li>Surrounding sewer manholes, catch basins, and open drains covered with fire-resistant tarpaulins within 15m radius.</li>
          <li>Pressurized water hose and dual 10kg DCP extinguishers stationed at work deck.</li>
          <li>Continuous personal multi-gas detector deployed with audio-visual alarm preset.</li>
        </ul>

        <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">4. Statutory Authorizations & Signatures</h2>
        <p style="color: #334155; line-height: 1.7; font-size: 13.5px;"><strong>Permit Issuer (Operations Shift In-Charge):</strong> Er. R. Nair (Emp ID: 4109) &nbsp;&bull;&nbsp; <em>Signed digitally at 07:45 HRS</em></p>
        <p style="color: #334155; line-height: 1.7; font-size: 13.5px;"><strong>Permit Receiver (Maintenance Lead):</strong> Er. K. Verma (Emp ID: 5218) &nbsp;&bull;&nbsp; <em>Signed digitally at 07:50 HRS</em></p>
        <p style="color: #334155; line-height: 1.7; font-size: 13.5px;"><strong>HSE & Fire Safety Inspector:</strong> S. Patil (Emp ID: 1042) &nbsp;&bull;&nbsp; <em>Certified & Approved</em></p>
      `;
    }

    const fLower = deliverable.filename.toLowerCase();
    const titleClean = deliverable.filename.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ').toUpperCase();

    if (fLower.includes('insurance') || fLower.includes('machinery') || fLower.includes('letter')) {
      return `
        <div style="font-family: Calibri, 'Segoe UI', Arial, sans-serif; color: #0f172a; line-height: 1.6;">
          <div style="text-align: right; color: #64748b; font-size: 13px; margin-bottom: 20px;">
            <p><strong>Ref:</strong> MRPL/ENG-INS/2026/089</p>
            <p><strong>Date:</strong> ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
          </div>

          <div style="margin-bottom: 24px; font-size: 14px; line-height: 1.5;">
            <p><strong>To,</strong></p>
            <p>The Senior Divisional Manager / Underwriting Head</p>
            <p>Industrial & Engineering Risk Underwriting Division</p>
            <p>National Insurance Company Ltd. / United India Insurance</p>
          </div>

          <h2 style="color: #1e40af; border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; font-size: 16px; font-weight: 800; text-transform: uppercase;">
            Subject: Formal Application for Machinery Breakdown & Comprehensive Plant Asset Coverage
          </h2>

          <p style="margin-top: 16px; font-size: 14px;">Dear Sir/Madam,</p>
          <p style="font-size: 14px; margin-top: 8px;">
            We hereby submit our formal request for the endorsement and renewal of Machinery Breakdown (MBD) and Comprehensive Industrial Risk Insurance for our high-criticality refinery machinery and rotary equipment.
          </p>

          <h3 style="color: #0369a1; margin-top: 20px; font-size: 14px; font-weight: 700;">1. Equipment Inventory & Valuation Details</h3>
          <table style="width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 16px; border: 1px solid #cbd5e1; font-size: 13px;">
            <thead>
              <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                <th style="padding: 8px 10px; text-align: left; border: 1px solid #cbd5e1;">Tag / Asset ID</th>
                <th style="padding: 8px 10px; text-align: left; border: 1px solid #cbd5e1;">Description</th>
                <th style="padding: 8px 10px; text-align: center; border: 1px solid #cbd5e1;">Operating Rating</th>
                <th style="padding: 8px 10px; text-align: right; border: 1px solid #cbd5e1;">Declared Sum Insured</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; font-weight: 600;">P-104A/B</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0;">Crude Distillation Multi-Stage Feed Pump</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; text-align: center;">450 kW / 2950 RPM</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; text-align: right;">₹ 4,85,00,000</td>
              </tr>
              <tr style="background-color: #f8fafc;">
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; font-weight: 600;">C-201</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0;">Centrifugal Cracked Gas Compressor</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; text-align: center;">18.5 Bar / 1.2 MW</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; text-align: right;">₹ 18,20,00,000</td>
              </tr>
              <tr>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; font-weight: 600;">F-101</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0;">Crude Vacuum Charge Furnace</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; text-align: center;">42 GCal/hr Heavy Duty</td>
                <td style="padding: 8px 10px; border: 1px solid #e2e8f0; text-align: right;">₹ 32,50,00,000</td>
              </tr>
            </tbody>
          </table>

          <h3 style="color: #0369a1; margin-top: 18px; font-size: 14px; font-weight: 700;">2. Risk Mitigation & Statutory Compliance</h3>
          <p style="font-size: 13.5px; line-height: 1.6;">
            All designated assets are operated under strict compliance with OISD-STD-105, API 610/617, and certified ISO 55001 Asset Integrity Management Systems. Predictive vibration diagnostics, thermography surveys, and lube oil analysis are logged bi-weekly.
          </p>

          <h3 style="color: #0369a1; margin-top: 18px; font-size: 14px; font-weight: 700;">3. Action Requested</h3>
          <p style="font-size: 13.5px; line-height: 1.6;">
            Kindly arrange the technical pre-risk inspection by your certified surveyor and issue the formal premium quote along with the policy endorsement draft at your earliest convenience.
          </p>

          <div style="margin-top: 32px; font-size: 13.5px;">
            <p>Yours faithfully,</p>
            <p style="margin-top: 24px; font-weight: bold; color: #1e3a8a;">Authorised Signatory / Chief General Manager (Engineering & Finance)</p>
            <p style="color: #64748b;">Mangalore Refinery and Petrochemicals Limited (MRPL)</p>
          </div>
        </div>
      `;
    }

    return `
      <h1 style="color: #1e40af; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">${titleClean}</h1>
      <p style="color: #64748b; font-size: 13px; margin-top: 6px;"><strong>Classification:</strong> Confidential Refinery Standard Operating Procedure &bull; <strong>Status:</strong> AUTHORIZED</p>
      <p style="color: #1e293b; line-height: 1.7; margin-top: 12px; font-size: 14px;"><strong>Summary:</strong> ${deliverable.summary || 'Technical engineering deliverable and operational benchmark document.'}</p>
      
      <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">1. Operational Overview & Objectives</h2>
      <p style="color: #1e293b; line-height: 1.7; font-size: 14px;">This technical document formalizes all statutory norms, process parameters, safety guardrails, and quality specifications mandated by OISD, PESO, and internal MRPL technical benchmarks.</p>

      <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">2. Key Compliance & Performance Criteria</h2>
      <ul style="color: #1e293b; line-height: 1.8; font-size: 14px;">
        ${(deliverable.key_metrics || []).map(m => `<li><strong>${m.label}:</strong> ${m.value}</li>`).join('')}
      </ul>

      <h2 style="color: #0369a1; margin-top: 24px; font-size: 16px; font-weight: 700;">3. Referenced SOPs and Regulatory Standards</h2>
      <ul style="color: #1e293b; line-height: 1.8; font-size: 14px;">
        ${(deliverable.sop_citations || ['MRPL Plant Operating Guide', 'OISD-STD-105']).map(c => `<li>${c}</li>`).join('')}
      </ul>
    `;
  };

  const [docHtml, setDocHtml] = useState(getInitialDocHtml);

  useEffect(() => {
    const initial = getInitialDocHtml();
    setDocHtml(initial);
    if (editorRef.current) {
      editorRef.current.innerHTML = initial;
      updateStats(editorRef.current.innerText || '');
    }
  }, [deliverable.id]);

  const updateStats = (text: string) => {
    const words = text.trim().split(/\s+/).filter(Boolean);
    setWordCount(words.length);
    setCharCount(text.length);
  };

  const handleInput = () => {
    if (editorRef.current) {
      const html = editorRef.current.innerHTML;
      setDocHtml(html);
      updateStats(editorRef.current.innerText || '');
      updateEditedContent(deliverable.id, { html });
    }
  };

  const exec = (command: string, value: string = '') => {
    document.execCommand(command, false, value);
    if (editorRef.current) {
      editorRef.current.focus();
      handleInput();
    }
  };

  const applyFontColor = (colorHex: string) => {
    setSelectedTextColor(colorHex);
    exec('foreColor', colorHex);
    setShowColorDropdown(false);
  };

  const applyHighlightColor = (colorHex: string) => {
    setSelectedHighlightColor(colorHex);
    exec('hiliteColor', colorHex);
    setShowHighlightDropdown(false);
  };

  const insertCustomHtml = (htmlString: string) => {
    exec('insertHTML', htmlString);
  };

  return (
    <div className="flex flex-col h-full bg-[#f8fafc] text-[#1e293b] select-none font-sans relative overflow-hidden">
      {/* 1. TOP STUDIO RIBBON HEADER (Mobile Scrollable) */}
      <div className="flex items-center justify-between px-2 sm:px-4 pt-2 pb-1 bg-white border-b border-[#e2e8f0] text-xs shrink-0 shadow-xs gap-2 overflow-x-auto scrollbar-none">
        {/* Left: Tab Switcher Bar */}
        <div className="flex items-center space-x-1 p-0.5 sm:p-1 bg-[#f1f5f9] rounded-xl border border-[#e2e8f0] shrink-0">
          {(['home', 'insert', 'layout', 'review', 'view'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg font-semibold text-xs transition-all capitalize whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-white text-[#2563eb] shadow-sm font-bold'
                  : 'text-[#64748b] hover:text-[#0f172a] hover:bg-white/50'
              }`}
            >
              {tab === 'review' ? 'Review & Safety' : tab}
            </button>
          ))}
        </div>

        {/* Right Header Actions: Quick Copy & Print */}
        <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0">
          <button
            onClick={() => {
              if (editorRef.current) {
                navigator.clipboard.writeText(editorRef.current.innerText || '');
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }
            }}
            className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-[#f8fafc] hover:bg-[#f1f5f9] text-[#0f172a] border border-[#cbd5e1] font-semibold text-xs transition-all cursor-pointer"
            title="Copy Text to Clipboard"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5 text-[#475569]" />}
            <span className="hidden xs:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={() => window.print()}
            className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3.5 py-1.5 rounded-xl bg-[#2563eb] hover:bg-[#1d4ed8] text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer shrink-0"
            title="Print or Export as PDF"
          >
            <Printer className="h-3.5 w-3.5" />
            <span className="hidden xs:inline">Print / PDF</span>
          </button>
        </div>
      </div>

      {/* 2. RIBBON ACTION TOOLBAR */}
      <div className="flex items-center gap-2 px-2 sm:px-4 py-2 bg-white border-b border-[#e2e8f0] text-xs shadow-xs relative z-20 shrink-0 overflow-x-auto scrollbar-none flex-nowrap">
        {activeTab === 'home' && (
          <>
            {/* Undo / Redo */}
            <div className="flex items-center space-x-1 pr-2.5 border-r border-[#e2e8f0]">
              <button
                onClick={() => exec('undo')}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#475569] hover:text-[#0f172a] transition-colors"
                title="Undo (Ctrl+Z)"
              >
                <Undo className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => exec('redo')}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#475569] hover:text-[#0f172a] transition-colors"
                title="Redo (Ctrl+Y)"
              >
                <Redo className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Font Family & Size Selectors (Custom Dropdowns) */}
            <div className="flex items-center space-x-1.5 pr-2.5 border-r border-[#e2e8f0]">
              <CustomDropdown
                value={selectedFont}
                onChange={(val) => {
                  setSelectedFont(val);
                  exec('fontName', val);
                }}
                size="xs"
                options={[
                  { value: 'Inter', label: 'Inter (Clean UI)' },
                  { value: 'Arial', label: 'Arial Standard' },
                  { value: 'Georgia', label: 'Georgia Serif' },
                  { value: 'Times New Roman', label: 'Times New Roman' },
                  { value: 'Courier New', label: 'Courier Mono' },
                ]}
                buttonClassName="bg-[#f8fafc] text-[#0f172a] border-[#cbd5e1] rounded-lg font-semibold"
              />

              <CustomDropdown
                value={selectedFontSize}
                onChange={(val) => {
                  setSelectedFontSize(val);
                  exec('fontSize', val);
                }}
                size="xs"
                options={[
                  { value: '1', label: '8pt' },
                  { value: '2', label: '10pt' },
                  { value: '3', label: '12pt' },
                  { value: '4', label: '14pt' },
                  { value: '5', label: '18pt' },
                  { value: '6', label: '24pt' },
                  { value: '7', label: '36pt' },
                ]}
                buttonClassName="bg-[#f8fafc] text-[#0f172a] border-[#cbd5e1] rounded-lg font-semibold w-16"
              />
            </div>

            {/* Basic Typography Styles */}
            <div className="flex items-center space-x-0.5 pr-2.5 border-r border-[#e2e8f0]">
              <button
                onClick={() => exec('bold')}
                title="Bold (Ctrl+B)"
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
              >
                <Bold className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => exec('italic')}
                title="Italic (Ctrl+I)"
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
              >
                <Italic className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => exec('underline')}
                title="Underline (Ctrl+U)"
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
              >
                <Underline className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => exec('strikeThrough')}
                title="Strikethrough"
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] transition-colors"
              >
                <Strikethrough className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Font Color & Highlight Dropdown Popovers */}
            <div className="flex items-center space-x-1.5 pr-2.5 border-r border-[#e2e8f0] relative">
              {/* Font Color Button */}
              <div className="relative">
                <div className="flex items-center rounded-lg border border-[#cbd5e1] hover:bg-[#f8fafc] bg-white overflow-hidden shadow-xs">
                  <button
                    onClick={() => exec('foreColor', selectedTextColor)}
                    title={`Apply Font Color (${selectedTextColor})`}
                    className="p-1.5 flex flex-col items-center justify-center text-[#0f172a]"
                  >
                    <span className="font-extrabold text-xs leading-none font-serif">A</span>
                    <div
                      className="h-1 w-3.5 rounded-full mt-0.5"
                      style={{ backgroundColor: selectedTextColor }}
                    />
                  </button>
                  <button
                    onClick={() => {
                      setShowColorDropdown(!showColorDropdown);
                      setShowHighlightDropdown(false);
                    }}
                    className="px-1 py-1.5 border-l border-[#e2e8f0] text-[#64748b] hover:text-[#0f172a]"
                    title="Choose Font Color"
                  >
                    <ChevronDown className="h-2.5 w-2.5" />
                  </button>
                </div>

                {/* Font Color Popover */}
                {showColorDropdown && (
                  <div className="absolute left-0 top-full mt-1.5 w-52 p-3 bg-white border border-[#cbd5e1] rounded-2xl shadow-2xl z-50">
                    <div className="text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-2">
                      Document Colors
                    </div>
                    <div className="grid grid-cols-5 gap-1.5 mb-3">
                      {FONT_COLORS.map((c) => (
                        <button
                          key={c.value}
                          onClick={() => applyFontColor(c.value)}
                          title={c.label}
                          style={{ backgroundColor: c.value }}
                          className="h-6 w-6 rounded-lg border border-[#cbd5e1] hover:scale-110 transition-transform shadow-xs cursor-pointer"
                        />
                      ))}
                    </div>
                    <div className="pt-2 border-t border-[#e2e8f0] flex items-center justify-between">
                      <span className="text-[11px] text-[#475569] font-medium">Custom Color:</span>
                      <input
                        type="color"
                        value={selectedTextColor}
                        onChange={(e) => applyFontColor(e.target.value)}
                        className="h-6 w-8 cursor-pointer rounded border border-[#cbd5e1] p-0.5 bg-transparent"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Text Highlight Button */}
              <div className="relative">
                <div className="flex items-center rounded-lg border border-[#cbd5e1] hover:bg-[#f8fafc] bg-white overflow-hidden shadow-xs">
                  <button
                    onClick={() => exec('hiliteColor', selectedHighlightColor)}
                    title={`Highlight Text (${selectedHighlightColor})`}
                    className="p-1.5 flex flex-col items-center justify-center text-[#0f172a]"
                  >
                    <Highlighter className="h-3.5 w-3.5 text-amber-600" />
                    <div
                      className="h-1 w-3.5 rounded-full mt-0.5"
                      style={{ backgroundColor: selectedHighlightColor }}
                    />
                  </button>
                  <button
                    onClick={() => {
                      setShowHighlightDropdown(!showHighlightDropdown);
                      setShowColorDropdown(false);
                    }}
                    className="px-1 py-1.5 border-l border-[#e2e8f0] text-[#64748b] hover:text-[#0f172a]"
                    title="Choose Highlight Color"
                  >
                    <ChevronDown className="h-2.5 w-2.5" />
                  </button>
                </div>

                {/* Highlight Popover */}
                {showHighlightDropdown && (
                  <div className="absolute left-0 top-full mt-1.5 w-52 p-3 bg-white border border-[#cbd5e1] rounded-2xl shadow-2xl z-50">
                    <div className="text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-2">
                      Highlight Colors
                    </div>
                    <div className="grid grid-cols-6 gap-1.5 mb-2">
                      {HIGHLIGHT_COLORS.map((c) => (
                        <button
                          key={c.value}
                          onClick={() => applyHighlightColor(c.value)}
                          title={c.label}
                          style={{ backgroundColor: c.value === 'transparent' ? '#ffffff' : c.value }}
                          className="h-6 w-6 rounded-lg border border-[#cbd5e1] hover:scale-110 transition-transform shadow-xs flex items-center justify-center text-[10px] cursor-pointer"
                        >
                          {c.value === 'transparent' ? '✕' : ''}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Clear Format */}
              <button
                onClick={() => exec('removeFormat')}
                title="Clear Formatting"
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#64748b] hover:text-[#0f172a] transition-colors"
              >
                <Eraser className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Paragraph Alignment */}
            <div className="flex items-center space-x-0.5 pr-2.5 border-r border-[#e2e8f0]">
              <button onClick={() => exec('justifyLeft')} title="Align Left" className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]">
                <AlignLeft className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => exec('justifyCenter')} title="Center" className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]">
                <AlignCenter className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => exec('justifyRight')} title="Align Right" className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]">
                <AlignRight className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => exec('justifyFull')} title="Justify" className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]">
                <AlignJustify className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Lists & Bullets */}
            <div className="flex items-center space-x-0.5 pr-2.5 border-r border-[#e2e8f0]">
              <button onClick={() => exec('insertUnorderedList')} title="Bullet List" className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]">
                <List className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => exec('insertOrderedList')} title="Numbered List" className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155]">
                <ListOrdered className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Quick Headings */}
            <div className="flex items-center space-x-1">
              <button
                onClick={() => exec('formatBlock', '<h1>')}
                className="px-2.5 py-1 rounded-lg hover:bg-[#f1f5f9] text-[#0f172a] font-bold text-xs"
              >
                H1
              </button>
              <button
                onClick={() => exec('formatBlock', '<h2>')}
                className="px-2.5 py-1 rounded-lg hover:bg-[#f1f5f9] text-[#0f172a] font-semibold text-xs"
              >
                H2
              </button>
              <button
                onClick={() => exec('formatBlock', '<p>')}
                className="px-2.5 py-1 rounded-lg hover:bg-[#f1f5f9] text-[#475569] text-xs font-medium"
              >
                Normal
              </button>
            </div>
          </>
        )}

        {activeTab === 'insert' && (
          <div className="flex items-center space-x-2.5">
            <button
              onClick={() =>
                insertCustomHtml(`
                <table style="width: 100%; border-collapse: collapse; margin: 16px 0; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden;">
                  <thead>
                    <tr style="background-color: #f1f5f9;">
                      <th style="border: 1px solid #cbd5e1; padding: 10px; text-align: left; color: #0f172a; font-weight: 700;">Parameter</th>
                      <th style="border: 1px solid #cbd5e1; padding: 10px; text-align: right; color: #0f172a; font-weight: 700;">Target Value</th>
                      <th style="border: 1px solid #cbd5e1; padding: 10px; text-align: center; color: #0f172a; font-weight: 700;">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style="border: 1px solid #e2e8f0; padding: 10px; color: #334155;">Pressure Gauge P-102</td>
                      <td style="border: 1px solid #e2e8f0; padding: 10px; text-align: right; color: #334155; font-weight: 600;">14.2 bar</td>
                      <td style="border: 1px solid #e2e8f0; padding: 10px; text-align: center; color: #16a34a; font-weight: 700;">NORMAL</td>
                    </tr>
                  </tbody>
                </table>
              `)
              }
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Table className="h-3.5 w-3.5 text-blue-600" />
              <span>Insert Data Table</span>
            </button>

            <button
              onClick={() =>
                insertCustomHtml(`
                <div style="margin: 18px 0; padding: 14px 18px; border-left: 4px solid #ea580c; background: #fff7ed; border-radius: 8px; color: #9a3412; font-size: 13.5px; line-height: 1.6;">
                  <strong>⚠️ MANDATORY SAFETY ADVISORY:</strong> Strict personal protective equipment (PPE Level C) must be worn at all times in this operational perimeter.
                </div>
              `)
              }
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#fff7ed] hover:bg-[#ffedd5] border border-[#fed7aa] text-[#c2410c] font-semibold transition-colors"
            >
              <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
              <span>Safety Callout</span>
            </button>

            <button
              onClick={() =>
                insertCustomHtml(`
                <div style="margin-top: 24px; padding: 14px 18px; border: 1.5px dashed #16a34a; border-radius: 12px; background: #f0fdf4; display: inline-block;">
                  <strong style="color: #15803d; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;">✓ AIR-GAPPED DIGITAL APPROVAL STAMP</strong>
                  <div style="font-size: 11px; color: #4b5563; margin-top: 4px;">Certified by Sovereign Intelligence System &bull; ${new Date().toLocaleString()}</div>
                </div>
              `)
              }
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f0fdf4] hover:bg-[#dcfce7] border border-[#bbf7d0] text-[#15803d] font-semibold transition-colors"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              <span>Digital Stamp</span>
            </button>

            <button
              onClick={() =>
                insertCustomHtml(`
                <hr style="border: none; border-top: 1.5px solid #e2e8f0; margin: 24px 0;" />
              `)
              }
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Minus className="h-3.5 w-3.5 text-slate-500" />
              <span>Divider Rule</span>
            </button>
          </div>
        )}

        {activeTab === 'layout' && (
          <div className="flex items-center space-x-4">
            {/* Page Theme Presets */}
            <div className="flex items-center space-x-2">
              <span className="text-[#64748b] font-semibold text-[11px] uppercase tracking-wider">Sheet Color:</span>
              <div className="flex items-center space-x-1.5">
                {PAGE_BG_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => setPageBgColor(preset.value)}
                    className={`h-7 px-3 rounded-lg border text-xs font-semibold transition-all ${
                      pageBgColor === preset.value
                        ? 'border-[#2563eb] ring-2 ring-[#2563eb]/20 text-[#2563eb] shadow-xs'
                        : 'border-[#cbd5e1] text-[#475569] hover:border-[#94a3b8]'
                    }`}
                    style={{ backgroundColor: preset.value }}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Paper Details */}
            <div className="flex items-center space-x-2 pl-3 border-l border-[#e2e8f0] text-[#475569] text-xs">
              <span>Size: <strong className="text-[#0f172a]">A4 Standard</strong></span>
              <span>&bull;</span>
              <span>Margins: <strong className="text-[#0f172a]">25.4 mm (Normal)</strong></span>
            </div>
          </div>
        )}

        {activeTab === 'review' && (
          <div className="flex items-center space-x-3 text-xs">
            <span className="flex items-center space-x-1 text-emerald-600 font-bold bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>OISD-STD-105 Statutory Standard Compliant</span>
            </span>
            <span className="text-[#94a3b8]">&bull;</span>
            <span className="text-[#475569] font-medium">
              Estimated Reading Time: <strong className="text-[#0f172a]">{Math.max(1, Math.ceil(wordCount / 200))} min</strong>
            </span>
          </div>
        )}

        {activeTab === 'view' && (
          <div className="flex items-center space-x-4">
            {/* Zoom Stepper */}
            <div className="flex items-center space-x-1.5 bg-[#f8fafc] border border-[#cbd5e1] rounded-lg px-2.5 py-1">
              <button
                onClick={() => setZoomLevel((z) => Math.max(50, z - 15))}
                className="p-1 hover:bg-[#e2e8f0] rounded text-[#475569]"
                title="Zoom Out"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span className="text-[11px] font-mono text-[#0f172a] font-bold">{zoomLevel}%</span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(200, z + 15))}
                className="p-1 hover:bg-[#e2e8f0] rounded text-[#475569]"
                title="Zoom In"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setZoomLevel(100)}
                className="text-[10px] font-semibold text-[#64748b] hover:text-[#0f172a] px-1.5 py-0.5 rounded"
              >
                Reset
              </button>
            </div>

            {/* Toggle Ruler */}
            <button
              onClick={() => setShowRuler(!showRuler)}
              className={`px-3 py-1 rounded-lg border text-xs font-semibold transition-colors ${
                showRuler ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-[#f8fafc] text-[#475569] border-[#cbd5e1]'
              }`}
            >
              Margin Ruler: {showRuler ? 'Visible' : 'Hidden'}
            </button>
          </div>
        )}
      </div>

      {/* 3. DOCUMENT STAGE / CANVAS AREA */}
      <div
        onClick={() => {
          setShowColorDropdown(false);
          setShowHighlightDropdown(false);
        }}
        className="flex-1 overflow-auto p-2 sm:p-8 flex flex-col items-center bg-[#f1f5f9] relative"
        style={{ backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)', backgroundSize: '20px 20px' }}
      >
        {/* Simulated Top Margin Ruler */}
        {showRuler && (
          <div className="w-full max-w-4xl bg-white border border-slate-200/80 rounded-t-xl h-6 hidden sm:flex items-end px-12 mb-0.5 text-[8px] font-mono text-[#94a3b8] justify-between shadow-xs select-none">
            {Array.from({ length: 17 }).map((_, i) => (
              <div key={i} className="flex flex-col items-center">
                <div className="h-1.5 w-[1px] bg-slate-300" />
                <span>{i}</span>
              </div>
            ))}
          </div>
        )}

        {/* Paper Sheet Document Canvas */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          style={{
            transform: `scale(${zoomLevel / 100})`,
            transformOrigin: 'top center',
            backgroundColor: pageBgColor,
          }}
          className={`w-full max-w-4xl min-h-[450px] sm:min-h-[900px] text-[#0f172a] border border-slate-200/80 ${
            showRuler ? 'sm:rounded-b-2xl sm:border-t-0 rounded-xl' : 'rounded-xl sm:rounded-2xl'
          } p-3.5 xs:p-6 sm:p-14 shadow-sm sm:shadow-[0_10px_35px_rgba(0,0,0,0.06)] relative transition-all overflow-hidden bg-white`}
        >
          {/* Subtle Top Header Tag */}
          <div className="flex items-center justify-between text-[9px] sm:text-[10px] text-[#94a3b8] border-b border-slate-100 pb-2.5 sm:pb-3 mb-3 sm:mb-4 select-none font-mono font-medium">
            <span>MRPL SOP ENGINE</span>
            <span>INTERNAL USE</span>
          </div>

          {/* Real Editable HTML Content */}
          <div
            ref={editorRef}
            contentEditable
            suppressContentEditableWarning
            onInput={handleInput}
            className="outline-none text-[13.5px] sm:text-[14.5px] leading-relaxed font-sans max-w-none focus:outline-none min-h-[400px] sm:min-h-[700px] text-[#0f172a]"
          />

          {/* Bottom Sheet Footer Tag */}
          <div className="flex items-center justify-between text-[9px] sm:text-[10px] text-[#94a3b8] border-t border-slate-100 pt-4 sm:pt-6 mt-8 sm:mt-12 select-none font-mono">
            <span>Form B / Ref: OISD-STD-105</span>
            <span>Page 1 of 1</span>
          </div>
        </motion.div>
      </div>

      {/* 4. BOTTOM STATISTICS & STATUS FOOTER */}
      <div className="flex items-center justify-between px-3 sm:px-5 py-2 sm:py-2.5 bg-white border-t border-[#e2e8f0] text-[11px] sm:text-xs text-[#64748b] shrink-0 shadow-xs overflow-x-auto scrollbar-none gap-2">
        <div className="flex items-center space-x-2 sm:space-x-3 font-mono shrink-0">
          <span>Words: <strong className="text-[#0f172a]">{wordCount}</strong></span>
          <span>&bull;</span>
          <span>Chars: <strong className="text-[#0f172a]">{charCount}</strong></span>
          <span className="hidden sm:inline">&bull;</span>
          <span className="hidden sm:inline">Page 1 of 1</span>
          <span>&bull;</span>
          <span className="text-[#2563eb] font-sans font-bold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 sm:h-2 sm:w-2 rounded-full bg-[#2563eb] animate-pulse" />
            Word Studio
          </span>
        </div>
      </div>
    </div>
  );
}
