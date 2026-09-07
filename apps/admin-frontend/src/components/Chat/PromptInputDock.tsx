'use client';

import React, { useState } from 'react';
import { useChatStore } from '@/store/useChatStore';
import { socketManager } from '@/lib/socket';
import { Button } from '@/components/ui/button';
import { ArrowUp, Paperclip, Square, Sparkles, Code, Eye, FileText, FileSpreadsheet, Presentation, ScanText, Layers } from 'lucide-react';

const MODEL_ROLES = [
  { id: 'orchestrator', label: 'Orchestrator', icon: <Layers className="h-4 w-4" />, color: 'text-blue-400' },
  { id: 'code', label: 'Code', icon: <Code className="h-4 w-4" />, color: 'text-blue-400' },
  { id: 'vision', label: 'Vision', icon: <Eye className="h-4 w-4" />, color: 'text-emerald-400' },
  { id: 'docs', label: 'Docs', icon: <FileText className="h-4 w-4" />, color: 'text-blue-500' },
  { id: 'excel', label: 'Excel', icon: <FileSpreadsheet className="h-4 w-4" />, color: 'text-emerald-500' },
  { id: 'ppt', label: 'PPT', icon: <Presentation className="h-4 w-4" />, color: 'text-orange-500' },
  { id: 'ocr', label: 'OCR', icon: <ScanText className="h-4 w-4" />, color: 'text-purple-400' },
];

export function PromptInputDock() {
  const { currentInput, setCurrentInput, addMessage, isStreaming, setStreaming } = useChatStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeModelRole, setActiveModelRole] = useState<string>('orchestrator');
  const [showRoleSelector, setShowRoleSelector] = useState(false);

  const handleSend = () => {
    if (!currentInput.trim() || isSubmitting || isStreaming) return;

    const userPrompt = currentInput.trim();
    setCurrentInput('');
    setIsSubmitting(true);

    // 1. Add User Message to UI
    addMessage({
      id: `usr-${Date.now()}`,
      role: 'user',
      content: userPrompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });

    // 2. Submit Task over WebSocket with role
    socketManager.sendChatTask(userPrompt, [], activeModelRole);
    setIsSubmitting(false);
  };

  const handleStop = () => {
    setStreaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const currentRole = MODEL_ROLES.find(r => r.id === activeModelRole);

  return (
    <div className="relative rounded-xl border border-gray-200 bg-white/95 shadow-2xl backdrop-blur-md p-3 transition-all focus-within:border-gray-300 focus-within:ring-1 focus-within:ring-gray-300/40">
      {/* Dynamic input area with comfortable typography */}
      <textarea
        value={currentInput}
        onChange={(e) => setCurrentInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={`Ask ${currentRole?.label || 'Sovereign AI'} or query refinery operating standards...`}
        rows={2}
        className="w-full bg-transparent text-xs text-gray-900 placeholder-gray-400 outline-none resize-none leading-relaxed font-sans min-h-[52px] max-h-[140px]"
      />

      {/* Action Footer Bar */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-200 mt-1">
        <div className="flex items-center space-x-2">
          {/* Role Selector Button */}
          <div className="relative">
            <Button 
              size="sm" 
              variant="ghost" 
              onClick={() => setShowRoleSelector(!showRoleSelector)}
              className="min-h-[36px] h-8 px-2.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all flex items-center gap-1.5"
            >
              {currentRole?.icon}
              <span className="text-[11px] font-mono">{currentRole?.label}</span>
            </Button>

            {/* Role Dropdown */}
            {showRoleSelector && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowRoleSelector(false)} />
                <div className="absolute bottom-full left-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1 min-w-[140px]">
                  {MODEL_ROLES.map((role) => {
                    const isDisabled = role.id === 'vision' || role.id === 'ocr';
                    return (
                      <button
                        key={role.id}
                        disabled={isDisabled}
                        title={isDisabled ? "Coming soon" : undefined}
                        onClick={() => {
                          if (isDisabled) return;
                          setActiveModelRole(role.id);
                          setShowRoleSelector(false);
                        }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-xs transition-colors ${
                          isDisabled
                            ? 'opacity-40 cursor-not-allowed grayscale'
                            : activeModelRole === role.id
                            ? 'bg-gray-100 font-semibold cursor-pointer'
                            : 'hover:bg-gray-50 cursor-pointer'
                        }`}
                      >
                        <span className={role.color}>{role.icon}</span>
                        <span>{role.label}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          <Button 
            size="sm" 
            variant="ghost" 
            className="min-h-[36px] h-8 px-2.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all"
          >
            <Paperclip className="h-3.5 w-3.5 mr-1.5" />
            <span className="text-[11px] font-mono">Attach</span>
          </Button>

          <span className="text-[10px] font-mono text-gray-500 hidden sm:inline flex items-center">
            <Sparkles className="h-3 w-3 mr-1 text-blue-600" />
            Sovereign AI
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {isStreaming ? (
            <Button
              size="sm"
              variant="outline"
              onClick={handleStop}
              className="min-h-[36px] h-8 px-3 text-xs font-mono text-[#e5484d] border-[#e5484d]/40 hover:bg-[#e5484d]/10 rounded-lg transition-all"
            >
              <Square className="h-3 w-3 mr-1.5 fill-current" />
              <span>Stop</span>
            </Button>
          ) : (
            <Button
              size="sm"
              variant="primary"
              onClick={handleSend}
              disabled={!currentInput.trim() || isSubmitting}
              className="min-h-[36px] h-8 w-8 p-0 rounded-lg bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-30 disabled:hover:bg-gray-900 transition-all flex items-center justify-center"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
