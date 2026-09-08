'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { MessageSquare, ExternalLink, ShieldCheck, Sparkles } from 'lucide-react';

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
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 flex flex-col items-center justify-center">
        <div className="flex flex-col items-center justify-center gap-6 p-8 max-w-lg text-center bg-gray-50 dark:bg-[#111116] border border-gray-200 dark:border-white/[0.08] rounded-2xl shadow-sm">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 flex items-center justify-center">
            <MessageSquare className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Conversational Chat Workspace</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              The full sovereign multi-agent conversational AI interface runs on port 3000. It features live token streaming, reasoning canvas sidebars, OCR parsing, and artifact synthesis.
            </p>
          </div>
          <a
            href={chatUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            Launch Chat Interface
            <ExternalLink className="w-4 h-4 ml-1" />
          </a>
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-mono">
            <ShieldCheck className="w-4 h-4" />
            <span>Air-Gapped Local Host Connection</span>
          </div>
        </div>
      </main>
    </div>
  );
}
