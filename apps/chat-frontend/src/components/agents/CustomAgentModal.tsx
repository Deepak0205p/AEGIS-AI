'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCustomAgentStore, CustomAgent } from '@/store/useCustomAgentStore';
import {
  Bot,
  Sparkles,
  Plus,
  Trash2,
  CheckCircle2,
  Sliders,
  Workflow,
  Wrench,
  FileCode,
  FileSpreadsheet,
  Database,
  FlaskConical,
  Cpu,
  Flame,
  Check,
  Zap,
  ArrowRight,
  Shield,
  Clock,
  X
} from 'lucide-react';

const AVATAR_OPTIONS = ['🤖', '⚡', '🛡️', '⚙️', '🔬', '🔥', '📊', '🚀', '💡', '🔍', '👷‍♂️', '🛠️'];

const TOOL_OPTIONS = [
  { id: 'rag', label: 'SOP RAG Vector Search', icon: Database, desc: 'Indexes & retrieves internal plant operating procedures' },
  { id: 'sandbox', label: 'Python Code Sandbox', icon: FileCode, desc: 'Executes isolated engineering math & calculations' },
  { id: 'deliverables', label: 'Office Deliverable Synthesis', icon: FileSpreadsheet, desc: 'Generates Word (.docx), Excel (.xlsx), and PPT reports' },
  { id: 'chemicals', label: 'Chemical Safety & MSDS KB', icon: FlaskConical, desc: 'Instant exposure limits and medical first-aid thresholds' },
];

const WORKFLOW_MODES = [
  {
    id: 'sequential_agentic',
    name: 'Multi-Step Plan & Execute',
    desc: 'Decomposes complex requests into steps: Analyze -> Retrieve -> Compute -> Synthesize Report'
  },
  {
    id: 'direct_fast',
    name: 'Direct Fast Execution',
    desc: 'Fast single-pass response with instant tool grounding for real-time field operations'
  },
  {
    id: 'autonomous_loop',
    name: 'Autonomous Self-Healing Loop',
    desc: 'Runs sandbox code iteratively, fixes syntax errors, and validates output against engineering constraints'
  }
];

export function CustomAgentModal() {
  const {
    showBuilderModal,
    closeBuilder,
    editingAgent,
    saveAgent,
    agents,
    activeAgentId,
    setActiveAgent,
    deleteAgent
  } = useCustomAgentStore();

  const [activeTab, setActiveTab] = useState<'create' | 'gallery'>('create');
  
  // Form state
  const [name, setName] = useState('');
  const [avatar, setAvatar] = useState('🤖');
  const [role, setRole] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [workflowMode, setWorkflowMode] = useState<'sequential_agentic' | 'direct_fast' | 'autonomous_loop'>('sequential_agentic');
  const [selectedTools, setSelectedTools] = useState<string[]>(['rag', 'sandbox', 'deliverables']);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (editingAgent) {
      setName(editingAgent.name);
      setAvatar(editingAgent.avatar || '🤖');
      setRole(editingAgent.role);
      setDescription(editingAgent.description);
      setSystemPrompt(editingAgent.system_prompt);
      setWorkflowMode(editingAgent.workflow_mode || 'sequential_agentic');
      setSelectedTools(editingAgent.tools || ['rag', 'sandbox', 'deliverables']);
      setActiveTab('create');
    } else {
      resetForm();
    }
  }, [editingAgent, showBuilderModal]);

  const resetForm = () => {
    setName('');
    setAvatar('🤖');
    setRole('Refinery Operations Specialist');
    setDescription('Custom automated agentic workflow for unit monitoring.');
    setSystemPrompt('You are an expert refinery operations agent. Follow plant SOPs and execute Python calculations when needed.');
    setWorkflowMode('sequential_agentic');
    setSelectedTools(['rag', 'sandbox', 'deliverables']);
  };

  const handleApplyTemplate = (tmpl: CustomAgent) => {
    setName(tmpl.name);
    setAvatar(tmpl.avatar);
    setRole(tmpl.role);
    setDescription(tmpl.description);
    setSystemPrompt(tmpl.system_prompt);
    setWorkflowMode(tmpl.workflow_mode);
    setSelectedTools(tmpl.tools);
    setActiveTab('create');
  };

  const toggleTool = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      setSelectedTools(selectedTools.filter((t) => t !== toolId));
    } else {
      setSelectedTools([...selectedTools, toolId]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    await saveAgent({
      id: editingAgent?.id,
      name,
      avatar,
      role,
      description,
      system_prompt: systemPrompt,
      workflow_mode: workflowMode,
      tools: selectedTools,
    });
    setIsSubmitting(false);
  };

  if (!showBuilderModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-3 sm:p-4 overflow-y-auto font-sans">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        className="w-full max-w-2xl bg-white dark:bg-[#10121a] border border-slate-200 dark:border-[#22283a] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        {/* Modal Top Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-white/5 flex items-center justify-between shrink-0 bg-slate-50/50 dark:bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 text-lg">
              {avatar}
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>Custom Agent Builder</span>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-[#a8c7fa] border border-blue-500/20">
                  Agentic Workflow
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-[#8e918f]">
                Build autonomous AI agents with custom roles, tools, and execution rules.
              </p>
            </div>
          </div>

          <button
            onClick={closeBuilder}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-3 flex items-center gap-2 border-b border-slate-100 dark:border-white/5 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('create')}
            className={`pb-2.5 px-3 border-b-2 transition-all cursor-pointer ${
              activeTab === 'create'
                ? 'border-blue-600 text-blue-600 dark:text-[#a8c7fa] dark:border-[#a8c7fa]'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            {editingAgent ? 'Edit Agent Configuration' : 'Create New Agent'}
          </button>
          <button
            onClick={() => setActiveTab('gallery')}
            className={`pb-2.5 px-3 border-b-2 transition-all cursor-pointer ${
              activeTab === 'gallery'
                ? 'border-blue-600 text-blue-600 dark:text-[#a8c7fa] dark:border-[#a8c7fa]'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            Agent Gallery &amp; Starter Templates ({agents.length})
          </button>
        </div>

        {/* Modal Body Container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {activeTab === 'create' ? (
            <form onSubmit={handleSave} className="space-y-4">
              {/* Agent Name & Avatar */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="sm:col-span-3 space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Agent Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Flare & Steam Balance Auditor"
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Avatar Icon</label>
                  <div className="flex items-center gap-1.5 overflow-x-auto py-1">
                    {AVATAR_OPTIONS.slice(0, 5).map((emoji) => (
                      <button
                        key={emoji}
                        type="button"
                        onClick={() => setAvatar(emoji)}
                        className={`w-8 h-8 rounded-xl flex items-center justify-center text-sm transition-all ${
                          avatar === emoji
                            ? 'bg-blue-600 text-white scale-110 shadow-sm'
                            : 'bg-slate-100 dark:bg-white/5 hover:bg-slate-200'
                        }`}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Role Title */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Role / Designation Title</label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g. Senior Process Engineer (CDU / Flare)"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Short Purpose Description */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Brief Purpose</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Audits flare network gas flows, detects relief valve leaks, and calculates steam ratios."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Agentic Workflow Execution Mode */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Workflow className="w-3.5 h-3.5 text-blue-500" />
                  <span>Agentic Workflow Architecture</span>
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {WORKFLOW_MODES.map((wm) => {
                    const isSelected = workflowMode === wm.id;
                    return (
                      <button
                        key={wm.id}
                        type="button"
                        onClick={() => setWorkflowMode(wm.id as any)}
                        className={`p-3 rounded-2xl border text-left flex flex-col justify-between transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-500 text-slate-900 dark:text-white shadow-xs'
                            : 'bg-slate-50 dark:bg-white/[0.02] border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-400 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-xs">{wm.name}</span>
                          {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 dark:text-[#a8c7fa]" />}
                        </div>
                        <p className="text-[10px] text-slate-500 dark:text-[#8e918f] leading-normal">
                          {wm.desc}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tool Integrations */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Wrench className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Enabled Tools &amp; Sandbox Subsystems</span>
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {TOOL_OPTIONS.map((tool) => {
                    const Icon = tool.icon;
                    const isChecked = selectedTools.includes(tool.id);
                    return (
                      <button
                        key={tool.id}
                        type="button"
                        onClick={() => toggleTool(tool.id)}
                        className={`p-2.5 rounded-xl border text-left flex items-start gap-2.5 transition-all cursor-pointer ${
                          isChecked
                            ? 'bg-emerald-50/70 dark:bg-emerald-950/30 border-emerald-500/60 text-slate-900 dark:text-white'
                            : 'bg-slate-50 dark:bg-white/[0.02] border-slate-200 dark:border-white/10 text-slate-500'
                        }`}
                      >
                        <div className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${isChecked ? 'bg-emerald-500 text-white' : 'bg-slate-200 dark:bg-white/10'}`}>
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-bold text-xs">{tool.label}</div>
                          <div className="text-[10px] text-slate-500 dark:text-[#8e918f] line-clamp-1">{tool.desc}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Custom System Prompt Directive */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Specialized System Instructions &amp; Behavioral Rules
                  </label>
                  <span className="text-[10px] text-slate-400 font-mono">Dynamic System Date-Time Auto-Injected</span>
                </div>
                <textarea
                  rows={4}
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="Define your agent's exact instructions, formulas, safety guardrails, or output format..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono leading-relaxed"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-white/5">
                <button
                  type="button"
                  onClick={closeBuilder}
                  className="px-4 py-2 rounded-xl border border-slate-200 dark:border-white/10 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/5 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !name.trim()}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{editingAgent ? 'Update Agent' : 'Activate Custom Agent'}</span>
                </button>
              </div>
            </form>
          ) : (
            /* Gallery & Templates View */
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-1">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Select an Agent or Clone a Template
                </span>
                <button
                  onClick={() => {
                    resetForm();
                    setActiveTab('create');
                  }}
                  className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa] flex items-center gap-1 hover:underline"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create from Scratch</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {agents.map((agent) => {
                  const isActive = activeAgentId === agent.id;
                  return (
                    <div
                      key={agent.id}
                      className={`p-4 rounded-2xl border transition-all flex flex-col justify-between space-y-3 ${
                        isActive
                          ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-500 shadow-sm'
                          : 'bg-slate-50/60 dark:bg-white/[0.02] border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20'
                      }`}
                    >
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2.5">
                            <span className="text-2xl">{agent.avatar || '🤖'}</span>
                            <div>
                              <h3 className="font-bold text-xs text-slate-900 dark:text-white leading-tight">
                                {agent.name}
                              </h3>
                              <span className="text-[10px] text-blue-600 dark:text-[#a8c7fa] font-semibold">
                                {agent.role}
                              </span>
                            </div>
                          </div>

                          {agent.is_template && (
                            <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-slate-400">
                              TEMPLATE
                            </span>
                          )}
                        </div>

                        <p className="text-[11px] text-slate-500 dark:text-[#8e918f] line-clamp-2 leading-relaxed">
                          {agent.description}
                        </p>

                        <div className="flex flex-wrap gap-1 pt-1">
                          {agent.tools?.map((t) => (
                            <span key={t} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white dark:bg-white/5 border border-slate-200 dark:border-white/5 text-slate-600 dark:text-slate-400">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 dark:border-white/5">
                        <button
                          type="button"
                          onClick={() => handleApplyTemplate(agent)}
                          className="text-[11px] font-bold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
                        >
                          Customize / Edit
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            setActiveAgent(agent.id);
                            closeBuilder();
                          }}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1 cursor-pointer ${
                            isActive
                              ? 'bg-emerald-600 text-white shadow-xs'
                              : 'bg-blue-600 hover:bg-blue-500 text-white'
                          }`}
                        >
                          {isActive ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              <span>Active</span>
                            </>
                          ) : (
                            <>
                              <Zap className="w-3.5 h-3.5" />
                              <span>Use Agent</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
