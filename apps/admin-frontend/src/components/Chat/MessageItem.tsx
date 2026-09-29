'use client';

import React from 'react';
import { ChatMessage } from '@/store/useChatStore';
import { useDeliverableStore } from '@/store/useDeliverableStore';
import { AgentTraceAccordion } from './AgentTraceAccordion';
import { RouterTagBadge } from './RouterTagBadge';
import { User, Sparkles, FileText, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface MessageItemProps {
  message: ChatMessage;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const downloadDeliverable = useDeliverableStore((s) => s.downloadDeliverable);

  return (
    <div className={`w-full py-4 border-b border-gray-100/60 flex gap-3 sm:gap-4 ${
      isUser ? 'bg-transparent' : 'bg-gray-50/30'
    }`}>
      {/* Avatar Column */}
      <div className="shrink-0 pt-0.5">
        {isUser ? (
          <div className="h-7 w-7 rounded-lg bg-gray-200 border border-gray-200 flex items-center justify-center text-gray-900">
            <User className="h-4 w-4" />
          </div>
        ) : (
          <div className="h-7 w-7 rounded-lg bg-blue-600/15 border border-blue-600/30 flex items-center justify-center text-blue-600">
            <Sparkles className="h-4 w-4" />
          </div>
        )}
      </div>

      {/* Message Body Column */}
      <div className="flex-1 min-w-0 space-y-2">
        {/* Header Name & Timestamp */}
        <div className="flex items-center justify-between text-[11px] font-mono text-gray-500">
          <div className="flex items-center space-x-2">
            <span className={`font-medium ${isUser ? 'text-gray-900' : 'text-blue-600'}`}>
              {isUser ? 'Operator' : 'MRPL Sovereign Assistant'}
            </span>
            <span>&bull;</span>
            <span>{message.timestamp}</span>
          </div>

          {!isUser && message.model_id && (
            <RouterTagBadge
              modelId={message.model_id}
              routedBy={message.routed_by}
              confidence={message.confidence}
            />
          )}
        </div>

        {/* Collapsible Reasoning & Tool Execution Trace */}
        {!isUser && message.trace_steps && message.trace_steps.length > 0 && (
          <div className="w-full">
            <AgentTraceAccordion steps={message.trace_steps} />
          </div>
        )}

        {/* Main Response Content Text */}
        <div className="text-xs sm:text-[13px] leading-relaxed text-gray-900 font-sans whitespace-pre-wrap selection:bg-blue-600/30">
          {message.content}
        </div>

        {/* Operator aborted this run: the text above is incomplete */}
        {message.aborted && (
          <div className="flex items-center gap-2 text-[10px] font-mono text-amber-700 border-t border-amber-200/70 pt-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
            <span>Stopped by operator - response truncated, no final answer was produced.</span>
          </div>
        )}

        {/* Deliverable Download Chips */}
        {message.deliverable_ids && message.deliverable_ids.length > 0 && (
          <div className="pt-2 flex flex-wrap gap-2">
            {message.deliverable_ids.map((delivId) => (
              <div
                key={delivId}
                className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-[11px] font-mono hover:border-gray-300 transition-all"
              >
                <FileText className="h-3.5 w-3.5 text-blue-600" />
                <span className="text-gray-900 font-medium">{delivId}</span>
                <Button size="sm" variant="ghost" onClick={() => downloadDeliverable(delivId)} className="h-6 px-2 text-[10px] text-blue-600 hover:text-gray-900 hover:bg-blue-600/20 rounded transition-colors cursor-pointer">
                  <Download className="h-3 w-3 mr-1" />
                  Download
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
