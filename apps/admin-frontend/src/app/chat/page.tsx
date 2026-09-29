'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { ChatWorkspace } from '@/components/Chat/ChatWorkspace';
import { ExternalLink, MessageSquare, ShieldCheck } from 'lucide-react';

export default function ChatPage() {
  const [chatUrl, setChatUrl] = useState('http://localhost:3000');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname || 'localhost';
      setChatUrl(`http://${hostname}:3000`);
    }
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-900 font-sans">
      <Header />
      <main className="flex-1 w-full mx-auto px-4 sm:px-6 py-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900 dark:text-white">Operational Chat Console</h1>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                Streaming Q&amp;A against the local sovereign backend (no attachments or document canvas in this view).
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-mono">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Local backend only</span>
            </span>
            <a
              href={chatUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
              title="Open the full chat application (canvas, attachments, document preview)"
            >
              Full Chat App
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        <div className="max-w-7xl mx-auto">
          <ChatWorkspace />
        </div>
      </main>
    </div>
  );
}
