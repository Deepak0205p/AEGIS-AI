'use client';

import React, { useState, useEffect } from 'react';
import { DeliverableItem } from '@/store/useDeliverableStore';
import { useCanvasStore } from '@/store/useCanvasStore';
import {
  Presentation,
  Plus,
  Trash2,
  Play,
  ChevronLeft,
  ChevronRight,
  Copy,
  Layout,
  Table,
  Sparkles,
  Printer,
  X,
  MessageSquare,
  ArrowUp,
  ArrowDown,
  Layers,
  Palette,
  Sliders,
  ZoomIn,
  ZoomOut,
  Maximize2,
  CheckCircle2,
  Quote,
  Clock,
  TrendingUp,
  FileCheck2,
  FileSpreadsheet
} from 'lucide-react';
import { CustomDropdown } from '@/components/ui/CustomDropdown';
import { motion, AnimatePresence } from 'framer-motion';

export interface SlideData {
  id: number;
  layout: 'title' | 'content' | 'two-column' | 'kpi-grid' | 'timeline' | 'quote' | 'table';
  title: string;
  subtitle: string;
  bullets: string[];
  kpis: { label: string; value: string; change?: string }[];
  timeline: { step: string; title: string; desc: string }[];
  tableData?: { headers: string[]; rows: string[][] };
  quoteText?: string;
  quoteAuthor?: string;
  notes: string;
  bgColor?: string;
  accentColor?: string;
}

interface UniverSlideEditorProps {
  deliverable: DeliverableItem;
}

const ACCENT_COLOR_PRESETS = [
  { label: 'Amber Flame', value: '#ea580c' },
  { label: 'Emerald Tech', value: '#16a34a' },
  { label: 'Royal Blue', value: '#2563eb' },
  { label: 'Indigo Core', value: '#4f46e5' },
  { label: 'Purple Apex', value: '#7c3aed' },
  { label: 'Rose Safety', value: '#e11d48' },
  { label: 'Slate Neutral', value: '#334155' },
];

const SLIDE_BG_PRESETS = [
  { label: 'Pure White', value: '#ffffff' },
  { label: 'Soft Ivory', value: '#fdfbf7' },
  { label: 'Ice Blue', value: '#f0f9ff' },
  { label: 'Subtle Slate', value: '#f8fafc' },
  { label: 'Clean Mint', value: '#f0fdf4' },
];

// Live Real-Time Dynamic Slide Content Miniature Renderer
function SlideMiniatureSkeleton({ slide }: { slide: SlideData }) {
  const accent = slide.accentColor || '#ea580c';

  if (slide.layout === 'title') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-2.5 text-center pointer-events-none overflow-hidden">
        <div
          className="text-[9px] font-black leading-tight line-clamp-2"
          style={{ color: accent }}
        >
          {slide.title || 'Untitled Slide'}
        </div>
        {slide.subtitle && (
          <div className="text-[6.5px] text-[#64748b] line-clamp-1 mt-0.5 font-medium leading-tight">
            {slide.subtitle}
          </div>
        )}
      </div>
    );
  }

  if (slide.layout === 'two-column') {
    return (
      <div className="flex-1 flex flex-col p-2 pointer-events-none overflow-hidden justify-between">
        <div className="text-[8.5px] font-bold text-[#0f172a] line-clamp-1 leading-tight">
          {slide.title || 'Untitled Slide'}
        </div>
        <div className="grid grid-cols-2 gap-1.5 flex-1 mt-1">
          <div className="bg-slate-50 border border-slate-200/80 rounded-md p-1 flex flex-col justify-start">
            <div className="text-[6px] font-bold text-[#0f172a] uppercase truncate">Focus</div>
            <div className="text-[5.5px] text-[#475569] line-clamp-2 leading-tight mt-0.5 font-medium">
              {slide.bullets[0] || 'Operational parameter'}
            </div>
          </div>
          <div className="bg-slate-50 border border-slate-200/80 rounded-md p-1 flex flex-col justify-start">
            <div className="text-[6px] font-bold text-blue-700 uppercase truncate">Takeaway</div>
            <div className="text-[5.5px] text-[#475569] line-clamp-2 leading-tight mt-0.5 font-medium">
              {slide.bullets[2] || slide.bullets[1] || 'Engineering criteria'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (slide.layout === 'kpi-grid') {
    return (
      <div className="flex-1 flex flex-col p-2 pointer-events-none overflow-hidden justify-between">
        <div className="text-[8.5px] font-bold text-[#0f172a] line-clamp-1 leading-tight">
          {slide.title || 'Untitled Slide'}
        </div>
        <div className="grid grid-cols-3 gap-1 flex-1 mt-1 items-center">
          {slide.kpis && slide.kpis.slice(0, 3).map((k, idx) => (
            <div key={idx} className="bg-slate-50 border border-slate-200/80 rounded-md p-1 flex flex-col justify-center items-center text-center">
              <div className="text-[5px] font-bold text-[#64748b] uppercase truncate w-full">{k.label}</div>
              <div className="text-[7.5px] font-black font-mono text-[#0f172a] truncate w-full" style={{ color: idx === 0 ? accent : '#0f172a' }}>{k.value}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (slide.layout === 'table') {
    return (
      <div className="flex-1 flex flex-col p-2 pointer-events-none overflow-hidden justify-between">
        <div className="text-[8.5px] font-bold text-[#0f172a] line-clamp-1 leading-tight">
          {slide.title || 'Untitled Slide'}
        </div>
        {slide.tableData && (
          <div className="border border-slate-200 rounded-md overflow-hidden flex-1 mt-1 text-[5px]">
            <div className="bg-slate-100 font-bold text-[#0f172a] grid grid-cols-3 px-1 py-0.5 border-b border-slate-200">
              {slide.tableData.headers.slice(0, 3).map((h, i) => (
                <span key={i} className="truncate">{h}</span>
              ))}
            </div>
            {slide.tableData.rows.slice(0, 2).map((r, rIdx) => (
              <div key={rIdx} className="grid grid-cols-3 px-1 py-0.5 border-b border-slate-100 text-[#475569] truncate">
                {r.slice(0, 3).map((c, cIdx) => (
                  <span key={cIdx} className="truncate">{c}</span>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (slide.layout === 'timeline') {
    return (
      <div className="flex-1 flex flex-col p-2 pointer-events-none overflow-hidden justify-between">
        <div className="text-[8.5px] font-bold text-[#0f172a] line-clamp-1 leading-tight">
          {slide.title || 'Untitled Slide'}
        </div>
        <div className="flex items-center justify-between gap-1 flex-1 mt-1">
          {slide.timeline && slide.timeline.slice(0, 3).map((t, idx) => (
            <div key={idx} className="bg-slate-50 border border-slate-200/80 rounded-md p-1 flex-1 flex flex-col">
              <div className="text-[5px] font-extrabold uppercase truncate" style={{ color: accent }}>{t.step}</div>
              <div className="text-[5.5px] font-bold text-[#0f172a] truncate leading-tight">{t.title}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (slide.layout === 'quote') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-2 text-center pointer-events-none overflow-hidden">
        <div className="text-[10px] leading-none font-serif" style={{ color: accent }}>“</div>
        <div className="text-[6.5px] italic text-[#1e293b] line-clamp-2 leading-tight font-medium mt-0.5">
          {slide.quoteText || slide.title}
        </div>
        <div className="text-[5.5px] font-bold text-[#64748b] truncate mt-0.5">
          — {slide.quoteAuthor || 'Author'}
        </div>
      </div>
    );
  }

  // Default 'content' / bullets layout
  return (
    <div className="flex-1 flex flex-col p-2 pointer-events-none overflow-hidden justify-between">
      <div className="text-[8.5px] font-bold text-[#0f172a] line-clamp-1 leading-tight">
        {slide.title || 'Untitled Slide'}
      </div>
      <div className="space-y-1 flex-1 justify-center flex flex-col mt-0.5">
        {slide.bullets && slide.bullets.slice(0, 3).map((b, idx) => (
          <div key={idx} className="flex items-center space-x-1">
            <div className="h-1 w-1 rounded-full shrink-0" style={{ backgroundColor: accent }} />
            <div className="text-[6.5px] text-[#334155] line-clamp-1 leading-tight font-medium">
              {b}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function UniverSlideEditor({ deliverable }: UniverSlideEditorProps) {
  const { updateEditedContent, editedContent } = useCanvasStore();
  const [activeRibbonTab, setActiveRibbonTab] = useState<'home' | 'insert' | 'design' | 'transitions' | 'slideshow'>('home');
  const [isPresenting, setIsPresenting] = useState(false);
  const [showNotesDrawer, setShowNotesDrawer] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '4:3'>('16:9');
  const [transitionEffect, setTransitionEffect] = useState<'fade' | 'slide' | 'zoom'>('fade');
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [selectedAccentColor, setSelectedAccentColor] = useState('#ea580c');
  const [laserPointer, setLaserPointer] = useState<{ x: number; y: number } | null>(null);

  const getInitialSlides = (): SlideData[] => {
    if (editedContent[deliverable.id]?.slides) {
      return editedContent[deliverable.id].slides;
    }

    return [
      {
        id: 1,
        layout: 'title',
        title: 'Monthly Apex Safety & Refinery Operations Review',
        subtitle: 'Executive Engineering Briefing • Q2 FY26 Statutory Compliance',
        bullets: [
          'Zero Loss Time Incidents (LTI) maintained across all process complexes.',
          '100% compliance with OISD-STD-105 Form B hot work & atmospheric gas safety norms.'
        ],
        kpis: [
          { label: 'Safe Man-Hours', value: '4.82 M', change: '+12% YoY' },
          { label: 'LTIFR Score', value: '0.00', change: 'Zero Target' },
          { label: 'Compliance', value: '100%', change: 'Certified' }
        ],
        timeline: [
          { step: '01', title: 'Process Unit Pre-Audit', desc: '4-gas testing verified' },
          { step: '02', title: 'LOTO Lockout', desc: 'Blind tags installed' },
          { step: '03', title: 'Hot Work', desc: 'Continuous firewatch' },
        ],
        notes: 'Introduce refinery leadership team and emphasize statutory OISD zero-harm targets.',
        bgColor: '#ffffff',
        accentColor: '#ea580c'
      },
      {
        id: 2,
        layout: 'content',
        title: 'Operational Highlights & Safe Man-Hours',
        subtitle: 'Key Achievements across Process Units & Contractor Zones',
        bullets: [
          '4.82 Million Safe Man-Hours achieved with zero recorded hydrocarbon loss of containment.',
          'Near-Miss reporting elevated by 38% through real-time mobile safety station logging.',
          'Contractor safety onboarding program certified with 100% attendance.'
        ],
        kpis: [
          { label: 'Near Miss Log', value: '209', change: 'Addressed' },
          { label: 'Audits Passed', value: '84', change: '100%' },
          { label: 'Uptime Score', value: '99.9%', change: 'Nominal' }
        ],
        timeline: [],
        notes: 'Walk through zone breakdown. Compliment the operations team on fast audit closure.',
        bgColor: '#ffffff',
        accentColor: '#2563eb'
      },
      {
        id: 3,
        layout: 'two-column',
        title: 'Refinery Yield & Energy Optimization Matrix',
        subtitle: 'Process Unit Performance Benchmarks',
        bullets: [
          'High Sulphur Crude blend ratio optimized from 68% to 74% yielding +$1.42/bbl margin uplift.',
          'FCCU Catalyst circulation rate maintained at 24.2 tons/min with zero slide-valve sticking.',
          'Specific Energy Consumption (MBN) reduced to 54.2 vs statutory ceiling of 58.0.'
        ],
        kpis: [
          { label: 'GRM Realization', value: '$12.45/bbl', change: '+$1.42' },
          { label: 'Throughput', value: '310 KBPD', change: 'Optimal' },
          { label: 'MBN Energy', value: '54.2', change: '-3.8 MBN' }
        ],
        timeline: [],
        notes: 'Highlight FCCU catalyst savings and steam generation efficiency.',
        bgColor: '#ffffff',
        accentColor: '#16a34a'
      },
      {
        id: 4,
        layout: 'timeline',
        title: 'Statutory SOP Verification & Milestone Timeline',
        subtitle: 'Multi-Stage HSE Governance Roadmap',
        bullets: [],
        kpis: [],
        timeline: [
          { step: 'Phase 1', title: 'Atmospheric Gas Matrix', desc: '%LEL=0.0%, O2=20.8%, H2S=0.0ppm verified' },
          { step: 'Phase 2', title: 'Mechanical Isolation', desc: 'Spectacle blinds BL-4402 locked in place' },
          { step: 'Phase 3', title: 'Permit Authorization', desc: 'Digital shift in-charge sign-off' },
          { step: 'Phase 4', title: 'Continuous Firewatch', desc: 'Dual 10kg DCP extinguishers active' },
        ],
        notes: 'Detail the 4-phase sequential workflow required for any category B hot work.',
        bgColor: '#ffffff',
        accentColor: '#7c3aed'
      },
      {
        id: 5,
        layout: 'table',
        title: 'Process Parameters & Tolerance Limits',
        subtitle: 'Standard Operating Matrix (OISD-STD-105)',
        bullets: [],
        kpis: [],
        timeline: [],
        tableData: {
          headers: ['Parameter / Stream', 'Design Limit', 'Measured Value', 'Safety Status'],
          rows: [
            ['Combustible Hydrocarbons', '0.0% LEL', '0.0%', 'PASS'],
            ['Oxygen Concentration (O₂)', '19.5% - 21.0%', '20.8%', 'SAFE'],
            ['Hydrogen Sulfide (H₂S)', '< 10.0 ppm', '0.0 ppm', 'PASS'],
            ['Carbon Monoxide (CO)', '< 25.0 ppm', '2.1 ppm', 'PASS'],
          ]
        },
        notes: 'All atmospheric telemetry measured using calibrated portable multi-gas detectors.',
        bgColor: '#ffffff',
        accentColor: '#ea580c'
      }
    ];
  };

  const [slides, setSlides] = useState<SlideData[]>(getInitialSlides);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);

  useEffect(() => {
    const initial = getInitialSlides();
    setSlides(initial);

    // Automatically fetch genuine parsed .pptx slides from backend
    const fetchLiveContent = async () => {
      const cleanId = deliverable.id.replace(/^\/api\/files\/(download\/)?/, '').trim();
      if (!cleanId) return;

      const host = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
      try {
        const res = await fetch(`http://${host}:8000/api/files/${cleanId}/content`);
        if (res.ok) {
          const data = await res.json();
          if (data.slides && Array.isArray(data.slides) && data.slides.length > 0) {
            setSlides(data.slides);
            updateEditedContent(deliverable.id, { slides: data.slides });
          }
        }
      } catch (err) {
        console.warn('[UniverSlideEditor] Fallback to initial slides:', err);
      }
    };

    fetchLiveContent();
  }, [deliverable.id]);

  const currentSlide = slides[activeSlideIndex] || slides[0];

  const handleUpdateSlide = (updatedFields: Partial<SlideData>) => {
    const updated = [...slides];
    updated[activeSlideIndex] = {
      ...updated[activeSlideIndex],
      ...updatedFields,
    };
    setSlides(updated);
    updateEditedContent(deliverable.id, { slides: updated });
  };

  const handleAddSlide = (layout: SlideData['layout'] = 'content') => {
    const newSlide: SlideData = {
      id: Date.now(),
      layout,
      title: 'New Executive Slide',
      subtitle: 'Technical Briefing & Operational Analysis',
      bullets: ['Key takeaway or operational observation 1.', 'Supporting metric or engineering standard 2.'],
      kpis: [{ label: 'Performance', value: '100%', change: 'Nominal' }, { label: 'Audit Status', value: 'PASS', change: 'Certified' }],
      timeline: [
        { step: 'Phase 1', title: 'Initiation', desc: 'Pre-operational verification' },
        { step: 'Phase 2', title: 'Execution', desc: 'Standard workflow compliance' }
      ],
      notes: '',
      bgColor: '#ffffff',
      accentColor: selectedAccentColor
    };
    const updated = [...slides, newSlide];
    setSlides(updated);
    setActiveSlideIndex(updated.length - 1);
    updateEditedContent(deliverable.id, { slides: updated });
  };

  const handleDeleteSlide = () => {
    if (slides.length <= 1) return;
    const updated = slides.filter((_, idx) => idx !== activeSlideIndex);
    setSlides(updated);
    setActiveSlideIndex(Math.max(0, activeSlideIndex - 1));
    updateEditedContent(deliverable.id, { slides: updated });
  };

  const handleDeleteSlideAt = (indexToDelete: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (slides.length <= 1) return;
    const updated = slides.filter((_, idx) => idx !== indexToDelete);
    setSlides(updated);
    if (activeSlideIndex >= updated.length) {
      setActiveSlideIndex(updated.length - 1);
    } else if (activeSlideIndex === indexToDelete) {
      setActiveSlideIndex(Math.max(0, indexToDelete - 1));
    }
    updateEditedContent(deliverable.id, { slides: updated });
  };

  const handleDuplicateSlide = () => {
    const clone: SlideData = {
      ...currentSlide,
      id: Date.now(),
      title: `${currentSlide.title} (Copy)`,
    };
    const updated = [...slides];
    updated.splice(activeSlideIndex + 1, 0, clone);
    setSlides(updated);
    setActiveSlideIndex(activeSlideIndex + 1);
    updateEditedContent(deliverable.id, { slides: updated });
  };

  const handleDuplicateSlideAt = (indexToDup: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const target = slides[indexToDup];
    if (!target) return;
    const clone: SlideData = {
      ...target,
      id: Date.now(),
      title: `${target.title} (Copy)`,
    };
    const updated = [...slides];
    updated.splice(indexToDup + 1, 0, clone);
    setSlides(updated);
    setActiveSlideIndex(indexToDup + 1);
    updateEditedContent(deliverable.id, { slides: updated });
  };

  const handleMoveSlide = (direction: 'up' | 'down') => {
    if (direction === 'up' && activeSlideIndex === 0) return;
    if (direction === 'down' && activeSlideIndex === slides.length - 1) return;

    const newIndex = direction === 'up' ? activeSlideIndex - 1 : activeSlideIndex + 1;
    const updated = [...slides];
    const item = updated.splice(activeSlideIndex, 1)[0];
    updated.splice(newIndex, 0, item);
    setSlides(updated);
    setActiveSlideIndex(newIndex);
    updateEditedContent(deliverable.id, { slides: updated });
  };

  // Keyboard navigation for presentation mode
  useEffect(() => {
    if (!isPresenting) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'Space') {
        setActiveSlideIndex((curr) => Math.min(slides.length - 1, curr + 1));
      } else if (e.key === 'ArrowLeft') {
        setActiveSlideIndex((curr) => Math.max(0, curr - 1));
      } else if (e.key === 'Escape') {
        setIsPresenting(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPresenting, slides.length]);

  return (
    <div className="flex flex-col h-full bg-[#f8fafc] text-[#1e293b] select-none font-sans relative overflow-hidden">
      {/* 1. TOP STUDIO RIBBON HEADER (Mobile Scrollable) */}
      <div className="flex items-center justify-between px-2 sm:px-4 pt-2 pb-1 bg-white border-b border-[#e2e8f0] text-xs shrink-0 shadow-xs gap-2 overflow-x-auto scrollbar-none">
        {/* Left: Tab Switcher Bar */}
        <div className="flex items-center space-x-1 p-0.5 sm:p-1 bg-[#f1f5f9] rounded-xl border border-[#e2e8f0] shrink-0">
          {(['home', 'insert', 'design', 'transitions', 'slideshow'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveRibbonTab(tab)}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg font-semibold text-xs transition-all capitalize whitespace-nowrap ${
                activeRibbonTab === tab
                  ? 'bg-white text-[#ea580c] shadow-sm font-bold'
                  : 'text-[#64748b] hover:text-[#0f172a] hover:bg-white/50'
              }`}
            >
              {tab === 'slideshow' ? 'Slide Show' : tab === 'insert' ? 'Insert' : tab}
            </button>
          ))}
        </div>

        {/* Right Header Actions: Speaker Notes & Fullscreen Present */}
        <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0">
          <button
            onClick={() => setShowNotesDrawer(!showNotesDrawer)}
            className={`flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showNotesDrawer
                ? 'bg-[#ffedd5] text-[#c2410c] border-[#fed7aa] shadow-xs'
                : 'bg-white text-[#475569] border-[#cbd5e1] hover:bg-[#f8fafc]'
            }`}
            title="Toggle Speaker Notes Drawer"
          >
            <MessageSquare className="h-3.5 w-3.5 text-[#ea580c]" />
            <span className="hidden sm:inline">Notes</span>
          </button>

          <button
            onClick={() => setIsPresenting(true)}
            className="flex items-center space-x-1 sm:space-x-1.5 px-3 sm:px-4 py-1.5 rounded-xl bg-gradient-to-r from-[#ea580c] to-[#c2410c] hover:from-[#c2410c] hover:to-[#9a3412] text-white text-xs font-bold shadow-md shadow-orange-500/20 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer shrink-0"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span className="hidden xs:inline">Present</span>
          </button>
        </div>
      </div>

      {/* 2. RIBBON ACTION TOOLBAR */}
      <div className="flex items-center gap-2.5 px-2 sm:px-4 py-2 bg-white border-b border-[#e2e8f0] text-xs shadow-xs shrink-0 overflow-x-auto scrollbar-none flex-nowrap">
        {activeRibbonTab === 'home' && (
          <>
            {/* Slide Operations */}
            <div className="flex items-center space-x-1.5 pr-3 border-r border-[#e2e8f0]">
              <button
                onClick={() => handleAddSlide('content')}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#fff7ed] hover:bg-[#ffedd5] border border-[#fed7aa] text-[#c2410c] font-bold text-xs shadow-xs transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>New Slide</span>
              </button>
              <button
                onClick={handleDuplicateSlide}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] transition-colors"
                title="Duplicate Current Slide"
              >
                <Copy className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={handleDeleteSlide}
                disabled={slides.length <= 1}
                className="p-1.5 rounded-lg hover:bg-rose-50 text-rose-600 border border-[#cbd5e1] disabled:opacity-30 transition-colors"
                title="Delete Current Slide"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Slide Reordering */}
            <div className="flex items-center space-x-1 pr-3 border-r border-[#e2e8f0]">
              <button
                onClick={() => handleMoveSlide('up')}
                disabled={activeSlideIndex === 0}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] disabled:opacity-30 transition-colors"
                title="Move Slide Up"
              >
                <ArrowUp className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleMoveSlide('down')}
                disabled={activeSlideIndex === slides.length - 1}
                className="p-1.5 rounded-lg hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] disabled:opacity-30 transition-colors"
                title="Move Slide Down"
              >
                <ArrowDown className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Layout Selector (Custom Dropdown) */}
            <div className="flex items-center space-x-2 pr-3 border-r border-[#e2e8f0]">
              <span className="text-[#64748b] font-semibold text-[11px] uppercase tracking-wider">Layout:</span>
              <CustomDropdown
                value={currentSlide.layout}
                onChange={(val) => handleUpdateSlide({ layout: val as any })}
                size="xs"
                options={[
                  { value: 'title', label: 'Title Slide' },
                  { value: 'content', label: 'Content & Bullets' },
                  { value: 'two-column', label: 'Two-Column Comparison' },
                  { value: 'kpi-grid', label: 'Executive Metrics Grid' },
                  { value: 'timeline', label: 'Milestone Timeline' },
                  { value: 'table', label: 'Data Table' },
                  { value: 'quote', label: 'Executive Quote' },
                ]}
                buttonClassName="bg-[#f8fafc] text-[#0f172a] border-[#cbd5e1] rounded-lg font-semibold"
              />
            </div>

            {/* Accent Color Palette Selector */}
            <div className="flex items-center space-x-2">
              <span className="text-[#64748b] font-semibold text-[11px] uppercase tracking-wider">Accent:</span>
              <div className="flex items-center space-x-1.5">
                {ACCENT_COLOR_PRESETS.map((color) => (
                  <button
                    key={color.value}
                    onClick={() => {
                      setSelectedAccentColor(color.value);
                      handleUpdateSlide({ accentColor: color.value });
                    }}
                    className={`h-5 w-5 rounded-full transition-transform ${
                      currentSlide.accentColor === color.value
                        ? 'ring-2 ring-offset-2 ring-[#0f172a] scale-110 shadow-xs'
                        : 'hover:scale-105 opacity-80 hover:opacity-100'
                    }`}
                    style={{ backgroundColor: color.value }}
                    title={color.label}
                  />
                ))}
              </div>
            </div>
          </>
        )}

        {activeRibbonTab === 'insert' && (
          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => {
                const bullets = [...currentSlide.bullets, 'New engineering observation or key operational takeaway.'];
                handleUpdateSlide({ bullets });
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Plus className="h-3.5 w-3.5 text-blue-600" />
              <span>Add Bullet Point</span>
            </button>

            <button
              onClick={() => {
                const kpis = [...currentSlide.kpis, { label: 'New Metric', value: '100%', change: 'Nominal' }];
                handleUpdateSlide({ kpis });
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Plus className="h-3.5 w-3.5 text-emerald-600" />
              <span>Add KPI Metric Card</span>
            </button>

            <button
              onClick={() => {
                const timeline = [
                  ...currentSlide.timeline,
                  { step: `Phase ${currentSlide.timeline.length + 1}`, title: 'Milestone Gate', desc: 'Milestone operational criteria' }
                ];
                handleUpdateSlide({ timeline });
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Plus className="h-3.5 w-3.5 text-purple-600" />
              <span>Add Timeline Step</span>
            </button>

            <button
              onClick={() => handleAddSlide('table')}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors"
            >
              <Table className="h-3.5 w-3.5 text-orange-600" />
              <span>Insert Table Slide</span>
            </button>
          </div>
        )}

        {activeRibbonTab === 'design' && (
          <div className="flex items-center space-x-4">
            {/* Background Presets */}
            <div className="flex items-center space-x-2">
              <span className="text-[#64748b] font-semibold text-[11px] uppercase tracking-wider">Slide Canvas Background:</span>
              <div className="flex items-center space-x-1.5">
                {SLIDE_BG_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => handleUpdateSlide({ bgColor: preset.value })}
                    className={`h-7 px-3 rounded-lg border text-xs font-semibold transition-all ${
                      currentSlide.bgColor === preset.value
                        ? 'border-[#ea580c] ring-2 ring-[#ea580c]/20 text-[#ea580c] shadow-xs'
                        : 'border-[#cbd5e1] text-[#475569] hover:border-[#94a3b8]'
                    }`}
                    style={{ backgroundColor: preset.value }}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Aspect Ratio Switcher */}
            <div className="flex items-center space-x-2 pl-3 border-l border-[#e2e8f0]">
              <span className="text-[#64748b] font-semibold text-[11px] uppercase tracking-wider">Ratio:</span>
              <button
                onClick={() => setAspectRatio('16:9')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  aspectRatio === '16:9'
                    ? 'bg-[#ea580c] text-white shadow-xs'
                    : 'bg-[#f8fafc] border border-[#cbd5e1] text-[#475569]'
                }`}
              >
                16:9 Widescreen
              </button>
              <button
                onClick={() => setAspectRatio('4:3')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  aspectRatio === '4:3'
                    ? 'bg-[#ea580c] text-white shadow-xs'
                    : 'bg-[#f8fafc] border border-[#cbd5e1] text-[#475569]'
                }`}
              >
                4:3 Standard
              </button>
            </div>
          </div>
        )}

        {activeRibbonTab === 'transitions' && (
          <div className="flex items-center space-x-3 text-xs">
            <span className="text-[#64748b] font-semibold text-[11px] uppercase tracking-wider">Slide Transition:</span>
            {(['fade', 'slide', 'zoom'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTransitionEffect(t)}
                className={`px-3.5 py-1.5 rounded-lg capitalize font-bold transition-all ${
                  transitionEffect === t
                    ? 'bg-[#ea580c] text-white shadow-sm'
                    : 'bg-[#f8fafc] border border-[#cbd5e1] text-[#475569] hover:bg-[#f1f5f9]'
                }`}
              >
                {t} Effect
              </button>
            ))}
          </div>
        )}

        {activeRibbonTab === 'slideshow' && (
          <div className="flex items-center space-x-3 text-xs">
            <button
              onClick={() => {
                setActiveSlideIndex(0);
                setIsPresenting(true);
              }}
              className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-[#ea580c] hover:bg-[#c2410c] text-white font-bold shadow-sm cursor-pointer"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>From Beginning (Slide 1)</span>
            </button>
            <button
              onClick={() => setIsPresenting(true)}
              className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-bold cursor-pointer"
            >
              <Play className="h-3.5 w-3.5" />
              <span>From Current Slide (#{activeSlideIndex + 1})</span>
            </button>
          </div>
        )}
      </div>

      {/* 3. MAIN WORKSPACE: DESKTOP SIDEBAR + CENTRAL SLIDE CANVAS */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
        {/* Desktop-Only Left Sidebar: Slide Thumbnails Navigator */}
        {showSidebar && (
          <div className="hidden md:flex w-44 lg:w-48 xl:w-52 border-r border-[#e2e8f0] bg-[#f8fafc] flex-col shrink-0 select-none shadow-xs">
            {/* Header Bar */}
            <div className="flex items-center justify-between px-3 py-2.5 border-b border-[#e2e8f0] bg-white/80 backdrop-blur-sm shrink-0">
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-extrabold text-[#0f172a] uppercase tracking-wider">Slides</span>
                <span className="px-1.5 py-0.5 rounded-full bg-[#f1f5f9] text-[#475569] font-mono text-[10px] font-bold border border-[#e2e8f0]">
                  {slides.length}
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => handleAddSlide('content')}
                  className="p-1 rounded-lg text-[#ea580c] hover:bg-[#ea580c]/10 transition-colors"
                  title="Add New Slide"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setShowSidebar(false)}
                  className="p-1 rounded-lg text-[#64748b] hover:text-[#0f172a] hover:bg-[#e2e8f0] transition-colors"
                  title="Collapse Sidebar"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Vertical Thumbnails Scroll Area */}
            <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5 scrollbar-none">
              {slides.map((s, idx) => {
                const isSelected = activeSlideIndex === idx;
                return (
                  <div
                    key={s.id}
                    onClick={() => setActiveSlideIndex(idx)}
                    className={`group relative flex flex-col p-2 rounded-xl transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-white border-[#ea580c] shadow-md ring-2 ring-[#ea580c]/20'
                        : 'bg-white border-[#e2e8f0] hover:border-[#cbd5e1] hover:shadow-xs'
                    }`}
                  >
                    {/* Top Bar: Index & Layout Tag */}
                    <div className="flex items-center justify-between mb-1.5 px-0.5">
                      <span className={`text-[10px] font-mono font-bold ${isSelected ? 'text-[#ea580c]' : 'text-[#64748b]'}`}>
                        #{idx + 1}
                      </span>
                      <span className="text-[8px] font-mono font-semibold uppercase px-1 py-0.2 rounded bg-[#f1f5f9] text-[#475569] border border-[#e2e8f0]/80">
                        {s.layout}
                      </span>
                    </div>

                    {/* 16:9 Realistic Miniature Slide Wireframe Box */}
                    <div
                      style={{ backgroundColor: s.bgColor || '#ffffff' }}
                      className={`relative w-full aspect-[16/9] rounded-lg border overflow-hidden flex flex-col transition-all shadow-inner ${
                        isSelected ? 'border-[#ea580c]/40 ring-1 ring-[#ea580c]/30' : 'border-[#e2e8f0]'
                      }`}
                    >
                      {/* Top Accent Strip */}
                      <div
                        className="h-1 w-full shrink-0"
                        style={{ backgroundColor: s.accentColor || '#ea580c' }}
                      />

                      {/* Miniature Layout Representation */}
                      <SlideMiniatureSkeleton slide={s} />

                      {/* Hover Quick Action Buttons */}
                      <div className="absolute top-1 right-1 flex items-center space-x-0.5 opacity-0 group-hover:opacity-100 transition-opacity bg-white/95 backdrop-blur-sm p-0.5 rounded shadow-xs border border-[#e2e8f0]">
                        <button
                          type="button"
                          onClick={(e) => handleDuplicateSlideAt(idx, e)}
                          className="p-0.5 rounded hover:bg-[#f1f5f9] text-[#475569] hover:text-[#0f172a] transition-colors"
                          title="Duplicate Slide"
                        >
                          <Copy className="h-2.5 w-2.5" />
                        </button>
                        {slides.length > 1 && (
                          <button
                            type="button"
                            onClick={(e) => handleDeleteSlideAt(idx, e)}
                            className="p-0.5 rounded hover:bg-red-50 text-[#64748b] hover:text-red-600 transition-colors"
                            title="Delete Slide"
                          >
                            <Trash2 className="h-2.5 w-2.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Bottom Add Slide Button */}
              <button
                onClick={() => handleAddSlide('content')}
                className="w-full flex items-center justify-center space-x-1.5 py-2 rounded-xl border border-dashed border-[#cbd5e1] hover:border-[#ea580c] hover:bg-[#ea580c]/5 text-[11px] font-bold text-[#64748b] hover:text-[#ea580c] transition-all cursor-pointer"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>New Slide</span>
              </button>
            </div>
          </div>
        )}

        {/* Center Canvas & Mobile Workspace (Full Priority on Mobile & Desktop Split Screen) */}
        <div className="flex-1 flex flex-col overflow-hidden bg-[#f1f5f9] relative">
          {/* Uncollapse Sidebar Floating Tab on Desktop when hidden */}
          {!showSidebar && (
            <button
              onClick={() => setShowSidebar(true)}
              className="hidden md:flex absolute top-3 left-3 z-10 items-center space-x-1.5 px-2.5 py-1.5 bg-white/95 backdrop-blur-sm border border-[#cbd5e1] rounded-xl shadow-md text-xs font-bold text-[#0f172a] hover:bg-slate-50 transition-all cursor-pointer"
              title="Show Slide Thumbnails"
            >
              <ChevronRight className="h-3.5 w-3.5 text-[#ea580c]" />
              <span>Slides ({slides.length})</span>
            </button>
          )}

          {/* Main Slide Presentation Stage Area */}
          <div
            className="flex-1 overflow-y-auto p-2.5 xs:p-4 sm:p-6 lg:p-8 flex flex-col items-center justify-start sm:justify-center relative"
            style={{ backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)', backgroundSize: '20px 20px' }}
          >
            {/* The Responsive Slide Card */}
            <motion.div
              key={currentSlide.id}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: zoomLevel / 100 }}
              transition={{ duration: 0.2 }}
              style={{
                backgroundColor: currentSlide.bgColor || '#ffffff',
                transformOrigin: 'center center',
              }}
              className="w-full max-w-4xl min-h-[360px] sm:min-h-[420px] aspect-auto lg:aspect-[16/9] text-[#0f172a] rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-lg sm:shadow-[0_20px_50px_rgba(0,0,0,0.08)] p-4 sm:p-6 lg:p-8 xl:p-10 flex flex-col justify-between relative transition-all bg-white overflow-hidden"
            >
              {/* Top Accent Strip */}
              <div
                className="absolute top-0 inset-x-0 h-1.5 sm:h-2.5"
                style={{ backgroundColor: currentSlide.accentColor || '#ea580c' }}
              />

              {/* Slide Header Section */}
              <div className="space-y-1 mb-3 sm:mb-4">
                <input
                  type="text"
                  value={currentSlide.title}
                  onChange={(e) => handleUpdateSlide({ title: e.target.value })}
                  className="w-full text-base xs:text-lg sm:text-2xl md:text-3xl font-extrabold tracking-tight bg-transparent border-none focus:outline-none focus:ring-1 sm:focus:ring-2 focus:ring-[#ea580c]/30 rounded-lg sm:rounded-xl px-1 sm:px-2 py-0.5 text-[#0f172a]"
                  placeholder="Slide Title"
                />

                <input
                  type="text"
                  value={currentSlide.subtitle}
                  onChange={(e) => handleUpdateSlide({ subtitle: e.target.value })}
                  className="w-full text-[11px] xs:text-xs sm:text-sm text-[#64748b] font-medium bg-transparent border-none focus:outline-none focus:ring-1 sm:focus:ring-2 focus:ring-[#ea580c]/30 rounded-lg sm:rounded-xl px-1 sm:px-2 py-0.5"
                  placeholder="Subtitle & Context"
                />
              </div>

              {/* Slide Dynamic Content based on Layout */}
              <div className="my-auto flex-1 flex flex-col justify-center py-2 sm:py-4">
                {/* 1. Content & Bullets Layout */}
                {currentSlide.layout === 'content' && (
                  <div className="space-y-2 sm:space-y-3.5">
                    {currentSlide.bullets.map((bullet, bIdx) => (
                      <div key={bIdx} className="group flex items-start space-x-2.5 p-1 rounded-xl hover:bg-slate-50 transition-colors">
                        <div
                          className="h-2 w-2 sm:h-2.5 sm:w-2.5 rounded-full mt-1.5 sm:mt-2 shrink-0 shadow-xs"
                          style={{ backgroundColor: currentSlide.accentColor || '#ea580c' }}
                        />
                        <input
                          type="text"
                          value={bullet}
                          onChange={(e) => {
                            const updatedBullets = [...currentSlide.bullets];
                            updatedBullets[bIdx] = e.target.value;
                            handleUpdateSlide({ bullets: updatedBullets });
                          }}
                          className="flex-1 text-xs xs:text-sm sm:text-base font-medium text-[#1e293b] bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#ea580c]/30 rounded px-1"
                        />
                        <button
                          onClick={() => {
                            const updatedBullets = currentSlide.bullets.filter((_, idx) => idx !== bIdx);
                            handleUpdateSlide({ bullets: updatedBullets });
                          }}
                          className="opacity-0 group-hover:opacity-100 text-xs text-[#94a3b8] hover:text-rose-600 p-1 transition-opacity"
                          title="Remove Bullet"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* 2. Two-Column Layout */}
                {currentSlide.layout === 'two-column' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-6">
                    <div className="p-3.5 sm:p-5 rounded-2xl bg-[#f8fafc] border border-[#e2e8f0] space-y-2 sm:space-y-3 shadow-xs">
                      <h4 className="font-bold text-xs text-[#0f172a] uppercase tracking-wider flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-[#ea580c]" />
                        <span>Operational Focus</span>
                      </h4>
                      {currentSlide.bullets.slice(0, 2).map((b, idx) => (
                        <p key={idx} className="text-xs sm:text-sm text-[#334155] leading-relaxed font-medium">&bull; {b}</p>
                      ))}
                    </div>
                    <div className="p-3.5 sm:p-5 rounded-2xl bg-[#f8fafc] border border-[#e2e8f0] space-y-2 sm:space-y-3 shadow-xs">
                      <h4 className="font-bold text-xs text-[#0f172a] uppercase tracking-wider flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-blue-600" />
                        <span>Engineering Takeaways</span>
                      </h4>
                      {currentSlide.bullets.slice(2).map((b, idx) => (
                        <p key={idx} className="text-xs sm:text-sm text-[#334155] leading-relaxed font-medium">&bull; {b}</p>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Milestone Timeline Layout */}
                {currentSlide.layout === 'timeline' && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3.5">
                    {currentSlide.timeline.map((t, idx) => (
                      <div key={idx} className="p-2.5 sm:p-4 rounded-xl sm:rounded-2xl bg-[#f8fafc] border border-[#e2e8f0] flex flex-col justify-between shadow-xs hover:border-[#cbd5e1] transition-all">
                        <div>
                          <span
                            className="text-[9px] sm:text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white border border-[#e2e8f0] inline-block shadow-xs"
                            style={{ color: currentSlide.accentColor || '#ea580c' }}
                          >
                            {t.step}
                          </span>
                          <input
                            type="text"
                            value={t.title}
                            onChange={(e) => {
                              const newTl = [...currentSlide.timeline];
                              newTl[idx].title = e.target.value;
                              handleUpdateSlide({ timeline: newTl });
                            }}
                            className="font-bold text-[11px] sm:text-sm text-[#0f172a] mt-2 sm:mt-2.5 w-full bg-transparent border-none focus:outline-none"
                          />
                        </div>
                        <input
                          type="text"
                          value={t.desc}
                          onChange={(e) => {
                            const newTl = [...currentSlide.timeline];
                            newTl[idx].desc = e.target.value;
                            handleUpdateSlide({ timeline: newTl });
                          }}
                          className="text-[10px] sm:text-[11px] text-[#64748b] mt-1 sm:mt-2 w-full bg-transparent border-none focus:outline-none leading-relaxed"
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* 4. Table Layout */}
                {currentSlide.layout === 'table' && currentSlide.tableData && (
                  <div className="overflow-x-auto rounded-xl sm:rounded-2xl border border-[#cbd5e1] shadow-xs">
                    <table className="w-full text-[11px] sm:text-xs text-left border-collapse">
                      <thead className="bg-[#f1f5f9] text-[#0f172a] font-bold border-b border-[#cbd5e1]">
                        <tr>
                          {currentSlide.tableData.headers.map((h, hIdx) => (
                            <th key={hIdx} className="p-2 sm:p-3 border-r border-[#cbd5e1]">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {currentSlide.tableData.rows.map((row, rIdx) => (
                          <tr key={rIdx} className="border-b border-[#e2e8f0] hover:bg-[#f8fafc] transition-colors">
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="p-2 sm:p-3 border-r border-[#e2e8f0] text-[#334155] font-medium">{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 5. KPI Grid Layout / Generic */}
                {(currentSlide.layout === 'kpi-grid' || currentSlide.layout === 'title') && currentSlide.kpis && (
                  <div className="grid grid-cols-1 xs:grid-cols-3 gap-2.5 sm:gap-4">
                    {currentSlide.kpis.map((kpi, kIdx) => (
                      <div key={kIdx} className="p-3 sm:p-5 rounded-xl sm:rounded-2xl bg-[#f8fafc] border border-[#e2e8f0] flex flex-col justify-between shadow-xs hover:shadow-sm transition-shadow">
                        <div className="flex items-center justify-between">
                          <input
                            type="text"
                            value={kpi.label}
                            onChange={(e) => {
                              const newKpis = [...currentSlide.kpis];
                              newKpis[kIdx].label = e.target.value;
                              handleUpdateSlide({ kpis: newKpis });
                            }}
                            className="text-[10px] sm:text-[11px] text-[#64748b] uppercase font-bold tracking-wider bg-transparent border-none focus:outline-none"
                          />
                          {kpi.change && (
                            <span className="text-[9px] sm:text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                              {kpi.change}
                            </span>
                          )}
                        </div>
                        <input
                          type="text"
                          value={kpi.value}
                          onChange={(e) => {
                            const newKpis = [...currentSlide.kpis];
                            newKpis[kIdx].value = e.target.value;
                            handleUpdateSlide({ kpis: newKpis });
                          }}
                          className="text-xl sm:text-3xl font-extrabold font-mono text-[#0f172a] mt-1 sm:mt-2 bg-transparent border-none focus:outline-none tracking-tight"
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* 6. Quote Layout */}
                {currentSlide.layout === 'quote' && (
                  <div className="flex flex-col items-center justify-center text-center px-4 sm:px-8 py-2 sm:py-4 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl text-[#ea580c] font-serif leading-none">“</div>
                    <textarea
                      value={currentSlide.quoteText || currentSlide.title}
                      onChange={(e) => handleUpdateSlide({ quoteText: e.target.value })}
                      className="w-full text-base sm:text-xl font-medium text-center text-[#1e293b] italic bg-transparent border-none focus:outline-none resize-none"
                      rows={3}
                    />
                    <div className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-[#64748b]">
                      — {currentSlide.quoteAuthor || 'Executive Engineering Board'}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Mobile-Only Bottom Thumbnails & Navigation Tray */}
          <div className="md:hidden flex flex-col bg-white border-t border-[#e2e8f0] shrink-0 shadow-sm">
            {/* Slide Navigation Bar */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-[#f1f5f9]">
              <div className="flex items-center space-x-1.5">
                <button
                  onClick={() => setActiveSlideIndex((curr) => Math.max(0, curr - 1))}
                  disabled={activeSlideIndex === 0}
                  className="p-1.5 rounded-lg bg-[#f8fafc] border border-[#cbd5e1] disabled:opacity-30 text-[#0f172a]"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-xs font-mono font-bold text-[#0f172a] px-1">
                  #{activeSlideIndex + 1} / {slides.length}
                </span>
                <button
                  onClick={() => setActiveSlideIndex((curr) => Math.min(slides.length - 1, curr + 1))}
                  disabled={activeSlideIndex === slides.length - 1}
                  className="p-1.5 rounded-lg bg-[#f8fafc] border border-[#cbd5e1] disabled:opacity-30 text-[#0f172a]"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleAddSlide('content')}
                  className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-[#ea580c] text-white text-xs font-bold shadow-xs active:scale-95 cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>New Slide</span>
                </button>
              </div>
            </div>

            {/* Bottom Horizontal Miniature Thumbnails Strip */}
            <div className="flex items-center space-x-2 p-2 overflow-x-auto scrollbar-none">
              {slides.map((s, idx) => {
                const isSelected = activeSlideIndex === idx;
                return (
                  <button
                    key={s.id}
                    onClick={() => setActiveSlideIndex(idx)}
                    className={`relative flex flex-col p-1 rounded-lg transition-all shrink-0 w-20 aspect-[16/9] border ${
                      isSelected
                        ? 'border-[#ea580c] ring-2 ring-[#ea580c]/30 shadow-xs'
                        : 'border-[#cbd5e1] bg-white opacity-70'
                    }`}
                    style={{ backgroundColor: s.bgColor || '#ffffff' }}
                  >
                    <div
                      className="h-1 w-full shrink-0 rounded-t"
                      style={{ backgroundColor: s.accentColor || '#ea580c' }}
                    />
                    <div className="flex-1 flex items-center justify-center text-[9px] font-mono font-bold text-[#0f172a]">
                      #{idx + 1}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* 4. SPEAKER NOTES COLLAPSIBLE DRAWER */}
      <AnimatePresence>
        {showNotesDrawer && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-white border-t border-[#cbd5e1] p-3.5 shrink-0 flex flex-col space-y-2 z-10 shadow-lg"
          >
            <div className="flex items-center justify-between text-xs text-[#64748b]">
              <span className="font-bold flex items-center gap-1.5 text-[#0f172a]">
                <MessageSquare className="h-4 w-4 text-[#ea580c]" />
                <span>Private Speaker Notes (Slide #{activeSlideIndex + 1})</span>
              </span>
              <button onClick={() => setShowNotesDrawer(false)} className="text-xs font-bold hover:text-[#0f172a] p-1">✕</button>
            </div>
            <textarea
              value={currentSlide.notes}
              onChange={(e) => handleUpdateSlide({ notes: e.target.value })}
              placeholder="Type private speaker talking points and presentation cues here..."
              className="w-full h-20 p-2.5 rounded-xl border border-[#cbd5e1] text-xs font-sans text-[#0f172a] focus:outline-none focus:ring-1 focus:ring-[#ea580c] resize-none leading-relaxed"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 5. BOTTOM NAVIGATION & STATUS FOOTER */}
      <div className="flex items-center justify-between px-5 py-2.5 bg-white border-t border-[#e2e8f0] text-xs text-[#64748b] shrink-0 shadow-xs">
        {/* Left: Slide Index Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveSlideIndex((curr) => Math.max(0, curr - 1))}
            disabled={activeSlideIndex === 0}
            className="p-1.5 rounded-lg hover:bg-[#f1f5f9] border border-[#cbd5e1] disabled:opacity-30 transition-colors cursor-pointer"
            title="Previous Slide"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="font-bold text-[#0f172a] font-mono px-1">
            Slide {activeSlideIndex + 1} of {slides.length}
          </span>
          <button
            onClick={() => setActiveSlideIndex((curr) => Math.min(slides.length - 1, curr + 1))}
            disabled={activeSlideIndex === slides.length - 1}
            className="p-1.5 rounded-lg hover:bg-[#f1f5f9] border border-[#cbd5e1] disabled:opacity-30 transition-colors cursor-pointer"
            title="Next Slide"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        {/* Center: Quick Zoom Controls */}
        <div className="flex items-center space-x-1.5 bg-[#f8fafc] px-2 py-1 rounded-lg border border-[#e2e8f0]">
          <button
            onClick={() => setZoomLevel((z) => Math.max(50, z - 15))}
            className="p-1 hover:bg-[#e2e8f0] rounded text-[#475569]"
            title="Zoom Out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="text-[11px] font-mono font-bold text-[#0f172a]">{zoomLevel}%</span>
          <button
            onClick={() => setZoomLevel((z) => Math.min(150, z + 15))}
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

        {/* Right: Print & Mode Status */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => window.print()}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#f8fafc] hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#0f172a] font-semibold transition-colors cursor-pointer"
          >
            <Printer className="h-3.5 w-3.5" />
            <span>Print Deck</span>
          </button>
          <span className="font-bold text-[#ea580c] flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#ea580c] animate-pulse" />
            PowerPoint Studio
          </span>
        </div>
      </div>

      {/* 6. FULLSCREEN PRESENTATION MODE */}
      <AnimatePresence>
        {isPresenting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-[#000000] text-white flex flex-col justify-between p-6 sm:p-12 select-none"
            onMouseMove={(e) => setLaserPointer({ x: e.clientX, y: e.clientY })}
          >
            {/* Simulated Laser Pointer */}
            {laserPointer && (
              <div
                className="pointer-events-none fixed h-3.5 w-3.5 rounded-full bg-red-500/80 shadow-[0_0_12px_#ef4444] z-[110] -translate-x-1/2 -translate-y-1/2"
                style={{ left: laserPointer.x, top: laserPointer.y }}
              />
            )}

            {/* Top SlideShow Controls */}
            <div className="flex items-center justify-between text-xs text-white/80">
              <div className="flex items-center space-x-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-mono font-semibold">LIVE SLIDESHOW &bull; {deliverable.filename}</span>
              </div>

              <div className="flex items-center space-x-4">
                <span className="font-mono">Slide {activeSlideIndex + 1} / {slides.length}</span>
                <button
                  onClick={() => setIsPresenting(false)}
                  className="px-3.5 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
                >
                  <X className="h-4 w-4" />
                  <span>Exit (Esc)</span>
                </button>
              </div>
            </div>

            {/* Active Presentation Slide Screen */}
            <div className="my-auto flex justify-center items-center">
              <div
                style={{ backgroundColor: currentSlide.bgColor || '#ffffff' }}
                className="w-full max-w-5xl aspect-[16/9] text-[#0f172a] rounded-3xl p-10 sm:p-16 flex flex-col justify-between shadow-2xl relative"
              >
                <div
                  className="absolute top-0 inset-x-0 h-3 rounded-t-3xl"
                  style={{ backgroundColor: currentSlide.accentColor || '#ea580c' }}
                />

                <div>
                  <h1 className="text-3xl sm:text-4xl font-extrabold text-[#0f172a] tracking-tight">
                    {currentSlide.title}
                  </h1>
                  <p className="text-base text-[#64748b] mt-2 font-medium">
                    {currentSlide.subtitle}
                  </p>
                </div>

                <div className="my-auto py-6 space-y-4">
                  {currentSlide.bullets.map((b, idx) => (
                    <div key={idx} className="flex items-start space-x-3 text-lg text-[#1e293b]">
                      <div
                        className="h-2.5 w-2.5 rounded-full mt-2.5 shrink-0"
                        style={{ backgroundColor: currentSlide.accentColor || '#ea580c' }}
                      />
                      <span className="font-medium">{b}</span>
                    </div>
                  ))}

                  {currentSlide.kpis && currentSlide.kpis.length > 0 && (
                    <div className="grid grid-cols-3 gap-6 pt-4">
                      {currentSlide.kpis.map((k, idx) => (
                        <div key={idx} className="p-5 rounded-2xl bg-[#f8fafc] border border-[#e2e8f0] shadow-xs">
                          <div className="text-xs font-bold text-[#64748b] uppercase">{k.label}</div>
                          <div className="text-2xl font-mono font-extrabold text-[#0f172a] mt-1">{k.value}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-[#94a3b8] border-t border-[#e2e8f0] pt-4">
                  <span className="font-medium">MRPL Presentation Studio</span>
                  <span className="font-mono">Slide {activeSlideIndex + 1} of {slides.length}</span>
                </div>
              </div>
            </div>

            {/* Bottom SlideShow Control Pills */}
            <div className="flex items-center justify-center space-x-4">
              <button
                onClick={() => setActiveSlideIndex((curr) => Math.max(0, curr - 1))}
                disabled={activeSlideIndex === 0}
                className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold disabled:opacity-30 transition-colors cursor-pointer"
              >
                ◀ Previous Slide
              </button>
              <button
                onClick={() => setActiveSlideIndex((curr) => Math.min(slides.length - 1, curr + 1))}
                disabled={activeSlideIndex === slides.length - 1}
                className="px-6 py-2.5 rounded-xl bg-[#ea580c] hover:bg-[#c2410c] text-white font-bold shadow-lg shadow-orange-500/20 transition-all active:scale-95 cursor-pointer"
              >
                Next Slide ▶
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
