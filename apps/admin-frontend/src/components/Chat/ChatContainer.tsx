'use client';

import React, { useRef, useEffect } from 'react';
import { useChatStore } from '@/store/useChatStore';
import { MessageItem } from './MessageItem';
import { motion, AnimatePresence } from 'framer-motion';

export function ChatContainer() {
  const { messages, isStreaming, streamingContent } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming, streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto pr-2 space-y-2 min-h-[400px] max-h-[560px]">
      {messages.length === 0 && !isStreaming && (
        <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-center gap-1 text-gray-500">
          <p className="text-xs font-mono font-semibold text-gray-700 dark:text-gray-300">No messages yet</p>
          <p className="text-[11px] font-mono">
            Use a quick prompt below, or type a refinery question. Responses stream from the local backend.
          </p>
        </div>
      )}

      <AnimatePresence mode="popLayout">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, transform: "scale(0.98) translateY(6px)" }}
            animate={{ opacity: 1, transform: "scale(1) translateY(0px)" }}
            exit={{ opacity: 0, transform: "scale(0.98)" }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
          >
            <MessageItem message={msg} />
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Live token buffer (real tokens received so far) */}
      {isStreaming && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-1.5 py-2"
        >
          <div className="flex items-center space-x-2 text-xs font-mono text-gray-500">
            <span className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
            <span>Streaming from the local backend...</span>
          </div>
          {streamingContent && (
            <div className="text-xs text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap leading-relaxed pl-4 border-l-2 border-blue-200">
              {streamingContent}
            </div>
          )}
        </motion.div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
