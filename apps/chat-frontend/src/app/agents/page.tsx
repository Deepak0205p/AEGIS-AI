'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Cpu,
  Plus,
  Search,
  Sparkles,
  Bot,
  Layers,
  Database,
  Terminal,
  FileSpreadsheet,
  FileText,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Trash2,
  Edit3,
  ArrowRight,
  Code2,
  Check,
  RefreshCw,
  Play,
  FlaskConical,
  Flame,
  Activity,
  ArrowLeft,
  SlidersHorizontal,
  Wrench,
  Settings2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import { SearchChatsModal } from '@/components/SearchChatsModal';
import { useCustomAgentStore, CustomAgent } from '@/store/useCustomAgentStore';
import { useSidebarStore } from '@/store/useSidebarStore';

const WORKFLOW_MODES = [
  {
    id: 'sequential_agentic',
    title: 'Multi-Step Plan & Execute',
    badge: 'Recommended',
    desc: 'Decomposes complex requests into steps: Analyze -> Retrieve -> Compute -> Synthesize Report.',
    icon: Layers,
    color: 'from-blue-600 to-indigo-600'
  },
  {
    id: 'direct_fast',
    title: 'Direct Fast Execution',
    badge: 'Low Latency',
    desc: 'Fast single-pass response with instant tool grounding for real-time plant field operations.',
    icon: Zap,
    color: 'from-amber-500 to-orange-500'
  },
  {
    id: 'autonomous_loop',
    title: 'Autonomous Self-Healing Loop',
    badge: 'Code & Calculations',
    desc: 'Runs sandbox code iteratively, fixes syntax/runtime errors, and validates output against engineering constraints.',
    icon: RefreshCw,
    color: 'from-emerald-500 to-teal-600'
  }
];

const AVAILABLE_TOOLS = [
  {
    id: 'rag',
    name: 'SOP RAG Vector Search',
    desc: 'Indexes & retrieves internal plant operating procedures and safety standards.',
    icon: Database,
    color: 'emerald'
  },
  {
    id: 'sandbox',
    name: 'Python Code Sandbox',
    desc: 'Executes isolated engineering math, thermodynamics, and calculations.',
    icon: Terminal,
    color: 'cyan'
  },
  {
    id: 'deliverables',
    name: 'Office Deliverable Synthesis',
    desc: 'Generates Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) reports.',
    icon: FileText,
    color: 'blue'
  },
  {
    id: 'chemicals',
    name: 'Chemical Safety & MSDS KB',
    desc: 'Instant exposure limits, H2S thresholds, and medical first-aid protocols.',
    icon: FlaskConical,
    color: 'purple'
  }
];

const STARTER_EMOJIS = ['🤖', '⚡', '🛡️', '⚙️', '🔍', '🔥', '🔬', '📊', '🏭', '🧪', '💡', '🚀'];

export default function AgentsPage() {
  const router = useRouter();
  const { toggle: toggleSidebar } = useSidebarStore();
  const {
    agents,
    activeAgentId,
    setActiveAgent,
    fetchAgents,
    saveAgent,
    deleteAgent,
    isLoading
  } = useCustomAgentStore();

  const [showSearchModal, setShowSearchModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'create' | 'gallery'>('gallery');
  const [searchQuery, setSearchQuery] = useState('');

  // Form State
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [avatar, setAvatar] = useState('🤖');
  const [role, setRole] = useState('');
  const [description, setDescription] = useState('');
  const [workflowMode, setWorkflowMode] = useState<'sequential_agentic' | 'direct_fast' | 'autonomous_loop'>('sequential_agentic');
  const [selectedTools, setSelectedTools] = useState<string[]>(['rag', 'sandbox', 'deliverables']);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleStartCreate = () => {
    setEditingId(null);
    setName('');
    setAvatar('🤖');
    setRole('');
    setDescription('');
    setWorkflowMode('sequential_agentic');
    setSelectedTools(['rag', 'sandbox', 'deliverables']);
    setSystemPrompt('You are a specialized Sovereign Refinery AI Assistant. Ground all answers in engineering principles and execute Python calculations when necessary.');
    setActiveTab('create');
  };

  const handleEditAgent = (agent: CustomAgent) => {
    setEditingId(agent.id);
    setName(agent.name);
    setAvatar(agent.avatar || '🤖');
    setRole(agent.role);
    setDescription(agent.description);
    setWorkflowMode(agent.workflow_mode || 'sequential_agentic');
    setSelectedTools(agent.tools || ['rag', 'sandbox']);
    setSystemPrompt(agent.system_prompt);
    setActiveTab('create');
  };

  const handleCloneTemplate = (agent: CustomAgent) => {
    setEditingId(null);
    setName(`${agent.name} (Custom)`);
    setAvatar(agent.avatar || '🤖');
    setRole(agent.role);
    setDescription(agent.description);
    setWorkflowMode(agent.workflow_mode || 'sequential_agentic');
    setSelectedTools([...(agent.tools || ['rag'])]);
    setSystemPrompt(agent.system_prompt);
    setActiveTab('create');
  };

  const toggleTool = (toolId: string) => {
    setSelectedTools((prev) =>
      prev.includes(toolId) ? prev.filter((t) => t !== toolId) : [...prev, toolId]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !systemPrompt.trim()) return;

    setIsSaving(true);
    const success = await saveAgent({
      id: editingId || `agent-${Date.now()}`,
      name: name.trim(),
      avatar,
      role: role.trim() || 'Process AI Specialist',
      description: description.trim() || 'Custom agentic workflow.',
      system_prompt: systemPrompt.trim(),
      workflow_mode: workflowMode,
      tools: selectedTools,
      is_template: false,
      author: 'Operations Engineer'
    });

    setIsSaving(false);
    if (success) {
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        setActiveTab('gallery');
      }, 1000);
    }
  };

  const filteredAgents = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 dark:bg-[#050507] dark:text-[#e3e3e3] font-sans antialiased selection:bg-blue-500/20 dark:selection:bg-[#4285f4]/30">
      {/* 1. Standard Shared Sidebar */}
      <AppSidebar
        onOpenSearchModal={() => setShowSearchModal(true)}
        activePage="agents"
      />

      {/* 2. Main Workstation Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-100/60 dark:bg-[#07070a] relative">
        {/* Top Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-[#0c0c0e] border-b border-slate-200 dark:border-[#1f1f26] shrink-0 z-10">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/chat')}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#181820] dark:hover:bg-[#22222c] text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-[#282834] transition-colors cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5 text-blue-600 dark:text-[#a8c7fa]" />
              <span>Back to Chat</span>
            </button>

            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                <Cpu className="h-5 w-5 text-blue-600 dark:text-[#a8c7fa]" />
              </div>
              <div>
                <h1 className="text-sm sm:text-base font-bold text-slate-900 dark:text-[#f1f3f4]">
                  Custom AI Agent Builder
                </h1>
                <p className="text-[11px] text-slate-500 dark:text-[#8e918f]">
                  Design, orchestrate, and deploy autonomous AI personas with custom tools and grounding
                </p>
              </div>
            </div>
          </div>

          {/* Action Tabs */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center p-1 bg-slate-100 dark:bg-[#15151c] border border-slate-200 dark:border-[#22222d] rounded-xl text-xs font-semibold">
              <button
                onClick={() => setActiveTab('gallery')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'gallery'
                    ? 'bg-white dark:bg-[#20202c] text-blue-600 dark:text-[#a8c7fa] shadow-xs'
                    : 'text-slate-600 dark:text-[#8e918f] hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Agent Gallery
              </button>
              <button
                onClick={handleStartCreate}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'create'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 dark:text-[#8e918f] hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Plus className="h-3.5 w-3.5" />
                <span>{editingId ? 'Edit Agent' : 'Create Agent'}</span>
              </button>
            </div>
          </div>
        </header>

        {/* Dynamic Content Body */}
        <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-6xl mx-auto w-full">
            {activeTab === 'gallery' ? (
              /* ─── GALLERY VIEW ─── */
              <div className="space-y-6">
                {/* Search & Stats Bar */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="relative w-full sm:w-80">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search agents by role, name, or capability..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-900 placeholder-slate-400 dark:bg-[#0e0e12] dark:border-[#22222a] dark:text-[#e3e3e3] dark:placeholder-[#8e918f] focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all"
                    />
                  </div>

                  <button
                    onClick={handleStartCreate}
                    className="w-full sm:w-auto flex items-center justify-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-98 text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Build New Custom Agent</span>
                  </button>
                </div>

                {/* Agents Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 sm:gap-6">
                  {filteredAgents.map((agent) => {
                    const isActive = activeAgentId === agent.id;
                    const workflowMeta = WORKFLOW_MODES.find(m => m.id === agent.workflow_mode) || WORKFLOW_MODES[0];

                    return (
                      <motion.div
                        key={agent.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`group relative flex flex-col justify-between p-5 rounded-2xl border transition-all duration-200 ${
                          isActive
                            ? 'bg-blue-500/[0.04] border-blue-500/50 shadow-lg shadow-blue-500/5 ring-1 ring-blue-500/30 dark:bg-blue-500/[0.06] dark:border-blue-500/40'
                            : 'bg-white border-slate-200 hover:border-slate-300 dark:bg-[#0c0c10] dark:border-[#1e1e26] dark:hover:border-[#2c2c38] shadow-xs'
                        }`}
                      >
                        {/* Header Info */}
                        <div>
                          <div className="flex items-start justify-between gap-3 mb-3">
                            <div className="flex items-center space-x-3">
                              <div className="h-12 w-12 rounded-2xl bg-slate-100 dark:bg-[#16161e] border border-slate-200 dark:border-[#262634] flex items-center justify-center text-2xl shrink-0 group-hover:scale-105 transition-transform">
                                {agent.avatar || '🤖'}
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <h3 className="text-sm font-bold text-slate-900 dark:text-[#f1f3f4]">
                                    {agent.name}
                                  </h3>
                                </div>
                                <p className="text-[11px] font-medium text-blue-600 dark:text-[#a8c7fa] mt-0.5">
                                  {agent.role}
                                </p>
                              </div>
                            </div>

                            {/* Active Status Badge */}
                            {isActive ? (
                              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Active</span>
                              </span>
                            ) : null}
                          </div>

                          <p className="text-xs text-slate-600 dark:text-[#c4c7c5] leading-relaxed line-clamp-2 mb-4">
                            {agent.description}
                          </p>

                          {/* Workflow Architecture Tag */}
                          <div className="flex items-center space-x-2 text-[11px] px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-[#121217] border border-slate-200/80 dark:border-[#1e1e26] text-slate-600 dark:text-[#8e918f] mb-3">
                            <Layers className="h-3.5 w-3.5 text-blue-500" />
                            <span className="font-semibold text-slate-800 dark:text-[#d0d3d6]">{workflowMeta.title}</span>
                          </div>

                          {/* Enabled Tools Row */}
                          <div className="flex flex-wrap gap-1.5 mb-4">
                            {agent.tools?.map((t) => {
                              const toolMeta = AVAILABLE_TOOLS.find(at => at.id === t);
                              return (
                                <span
                                  key={t}
                                  className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-[#16161e] border border-slate-200 dark:border-[#22222e] text-slate-600 dark:text-[#a0a3a6]"
                                >
                                  {toolMeta?.name || t}
                                </span>
                              );
                            })}
                          </div>
                        </div>

                        {/* Action Buttons Footer */}
                        <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-[#181820] mt-auto">
                          <div className="flex items-center space-x-2">
                            {isActive ? (
                              <button
                                onClick={() => setActiveAgent(null)}
                                className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#1a1a22] dark:hover:bg-[#22222c] text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] transition-colors"
                              >
                                Deactivate
                              </button>
                            ) : (
                              <button
                                onClick={() => {
                                  setActiveAgent(agent.id);
                                  router.push('/chat');
                                }}
                                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                              >
                                <Play className="h-3 w-3 fill-current" />
                                <span>Activate & Chat</span>
                              </button>
                            )}
                          </div>

                          <div className="flex items-center space-x-1">
                            {agent.is_template ? (
                              <button
                                onClick={() => handleCloneTemplate(agent)}
                                className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-[#181822] text-slate-600 dark:text-[#8e918f] hover:text-blue-600 dark:hover:text-[#a8c7fa] text-xs font-semibold transition-colors"
                                title="Clone & Customize Template"
                              >
                                <SlidersHorizontal className="h-3.5 w-3.5 text-blue-600 dark:text-[#a8c7fa]" />
                                <span>Customize</span>
                              </button>
                            ) : (
                              <>
                                <button
                                  onClick={() => handleEditAgent(agent)}
                                  className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-[#181822] text-slate-500 hover:text-slate-900 dark:text-[#8e918f] dark:hover:text-white transition-colors"
                                  title="Edit Agent"
                                >
                                  <Edit3 className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => deleteAgent(agent.id)}
                                  className="p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-400 hover:text-rose-600 dark:text-[#8e918f] dark:hover:text-rose-400 transition-colors"
                                  title="Delete Agent"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ) : (
              /* ─── CREATION & EDITING FORM ─── */
              <div className="bg-white dark:bg-[#0b0b0f] border border-slate-200 dark:border-[#1e1e26] rounded-3xl p-6 sm:p-8 shadow-xl max-w-4xl mx-auto">
                <form onSubmit={handleSave} className="space-y-6">
                  {/* Identity Row */}
                  <div className="space-y-4">
                    <h3 className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa] uppercase tracking-wider flex items-center gap-2">
                      <Bot className="h-4 w-4" />
                      <span>1. Persona Identity & Purpose</span>
                    </h3>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      {/* Avatar Picker */}
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] mb-1.5">
                          Agent Avatar
                        </label>
                        <div className="flex flex-wrap gap-1.5 p-2 bg-slate-50 dark:bg-[#121217] border border-slate-200 dark:border-[#202028] rounded-2xl">
                          {STARTER_EMOJIS.map((e) => (
                            <button
                              key={e}
                              type="button"
                              onClick={() => setAvatar(e)}
                              className={`h-9 w-9 rounded-xl flex items-center justify-center text-lg transition-all ${
                                avatar === e
                                  ? 'bg-blue-600 text-white shadow-sm scale-110'
                                  : 'hover:bg-slate-200 dark:hover:bg-[#20202c]'
                              }`}
                            >
                              {e}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Name & Role */}
                      <div className="sm:col-span-2 space-y-3">
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] mb-1">
                            Agent Display Name <span className="text-rose-500">*</span>
                          </label>
                          <input
                            type="text"
                            required
                            placeholder="e.g. Crude Column Yield Optimizer"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 dark:bg-[#121217] dark:border-[#202028] dark:text-white dark:placeholder-[#8e918f] focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] mb-1">
                            Engineering Role / Discipline
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. Lead Process Automation Engineer"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="w-full px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 dark:bg-[#121217] dark:border-[#202028] dark:text-white dark:placeholder-[#8e918f] focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-[#c4c7c5] mb-1">
                        Brief Capability Description
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Performs real-time material balance audits and computes Gross Refining Margins."
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 dark:bg-[#121217] dark:border-[#202028] dark:text-white dark:placeholder-[#8e918f] focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                      />
                    </div>
                  </div>

                  {/* Workflow Mode Selector */}
                  <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-[#1a1a22]">
                    <h3 className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa] uppercase tracking-wider flex items-center gap-2">
                      <Layers className="h-4 w-4" />
                      <span>2. Agentic Workflow Architecture</span>
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {WORKFLOW_MODES.map((mode) => {
                        const isSelected = workflowMode === mode.id;
                        const Icon = mode.icon;
                        return (
                          <div
                            key={mode.id}
                            onClick={() => setWorkflowMode(mode.id as any)}
                            className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                              isSelected
                                ? 'bg-blue-50/60 border-blue-500 shadow-md ring-1 ring-blue-500/30 dark:bg-blue-500/10 dark:border-blue-500/60'
                                : 'bg-slate-50 border-slate-200 hover:border-slate-300 dark:bg-[#121217] dark:border-[#1e1e26] dark:hover:border-[#2a2a38]'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="h-8 w-8 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-[#a8c7fa]">
                                <Icon className="h-4 w-4" />
                              </div>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-[#1e1e28] text-slate-700 dark:text-[#c4c7c5]">
                                {mode.badge}
                              </span>
                            </div>
                            <h4 className="text-xs font-bold text-slate-900 dark:text-[#f1f3f4] mb-1">
                              {mode.title}
                            </h4>
                            <p className="text-[11px] text-slate-500 dark:text-[#8e918f] leading-relaxed">
                              {mode.desc}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Tool Assignments */}
                  <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-[#1a1a22]">
                    <h3 className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa] uppercase tracking-wider flex items-center gap-2">
                      <Terminal className="h-4 w-4" />
                      <span>3. Enabled Subsystems & Tools</span>
                    </h3>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {AVAILABLE_TOOLS.map((tool) => {
                        const isEnabled = selectedTools.includes(tool.id);
                        const Icon = tool.icon;
                        return (
                          <div
                            key={tool.id}
                            onClick={() => toggleTool(tool.id)}
                            className={`flex items-center space-x-3 p-3.5 rounded-2xl border cursor-pointer transition-all ${
                              isEnabled
                                ? 'bg-emerald-50/50 border-emerald-500/60 ring-1 ring-emerald-500/20 dark:bg-emerald-500/10 dark:border-emerald-500/40'
                                : 'bg-slate-50 border-slate-200 dark:bg-[#121217] dark:border-[#1e1e26] opacity-60 hover:opacity-100'
                            }`}
                          >
                            <div className="h-9 w-9 rounded-xl bg-white dark:bg-[#1a1a22] border border-slate-200 dark:border-[#282834] flex items-center justify-center shrink-0">
                              <Icon className="h-4.5 w-4.5 text-slate-700 dark:text-[#c4c7c5]" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-900 dark:text-[#f1f3f4]">
                                  {tool.name}
                                </span>
                                {isEnabled && (
                                  <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                                )}
                              </div>
                              <p className="text-[10px] text-slate-500 dark:text-[#8e918f] truncate mt-0.5">
                                {tool.desc}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* System Prompt & Instructions */}
                  <div className="space-y-2 pt-4 border-t border-slate-100 dark:border-[#1a1a22]">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa] uppercase tracking-wider flex items-center gap-2">
                        <Code2 className="h-4 w-4" />
                        <span>4. System Directives & Behavioral Constraints</span>
                      </h3>
                      <span className="text-[10px] font-mono text-slate-400 dark:text-[#8e918f]">
                        Local Date & Shift Auto-Injected
                      </span>
                    </div>

                    <textarea
                      required
                      rows={6}
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="Specify exact domain behavior, safety limits, calculation requirements, and output formats..."
                      className="w-full p-4 rounded-2xl bg-slate-50 border border-slate-200 font-mono text-xs text-slate-900 dark:bg-[#121217] dark:border-[#202028] dark:text-[#e3e3e3] focus:outline-none focus:ring-2 focus:ring-blue-500/30 leading-relaxed resize-none"
                    />
                  </div>

                  {/* Submission Row */}
                  <div className="flex items-center justify-between pt-6 border-t border-slate-100 dark:border-[#1a1a22]">
                    <button
                      type="button"
                      onClick={() => setActiveTab('gallery')}
                      className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#181820] dark:hover:bg-[#22222c] text-xs font-semibold text-slate-700 dark:text-[#c4c7c5]"
                    >
                      Cancel
                    </button>

                    <div className="flex items-center space-x-3">
                      {saveSuccess && (
                        <span className="flex items-center space-x-1 text-xs text-emerald-600 font-bold">
                          <CheckCircle2 className="h-4 w-4" />
                          <span>Saved Successfully!</span>
                        </span>
                      )}

                      <button
                        type="submit"
                        disabled={isSaving}
                        className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-98 text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 disabled:opacity-50"
                      >
                        {isSaving ? (
                          <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Sparkles className="h-4 w-4" />
                        )}
                        <span>{editingId ? 'Update Agent' : 'Deploy Custom Agent'}</span>
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Global Search Chats Modal */}
      <SearchChatsModal
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
      />
    </div>
  );
}
