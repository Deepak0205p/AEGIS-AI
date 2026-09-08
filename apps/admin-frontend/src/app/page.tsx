'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { OverviewDeck } from '@/components/OverviewDeck';
import { socketManager } from '@/lib/socket';
import { useModelStore } from '@/store/useModelStore';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import { useRouter } from 'next/navigation';
import { 
  Cpu, 
  GitFork, 
  Box, 
  Database, 
  UploadCloud, 
  Shield, 
  FileText, 
  MessageSquare, 
  Users,
  ArrowRight
} from 'lucide-react';

const subsystemTiles = [
  {
    title: 'Two-Stage Query Router',
    href: '/router',
    icon: GitFork,
    description: 'Interactive route tester (<2ms Regex vs <25ms BGE-small semantic fallback).'
  },
  {
    title: 'RAG Knowledge & Converter',
    href: '/rag',
    icon: Database,
    description: 'Upload SOP/MOP to build ChromaDB embeddings + universal document format converter.'
  },
  {
    title: 'OCR Hub',
    href: '/ocr',
    icon: UploadCloud,
    description: 'Offline PaddleOCR & Tesseract pipeline with ISA 5.1 P&ID tag extraction.'
  },
  {
    title: 'Sovereignty Watchdog',
    href: '/sovereignty',
    icon: Shield,
    description: 'psutil real-time socket inspection & SHA-256 tamper-evident blockchain ledger.'
  },
  {
    title: 'Enterprise Deliverables',
    href: '/deliverables',
    icon: FileText,
    description: 'Programmatic synthesis of Word (.docx), Excel (.xlsx), and PowerPoint (.pptx).'
  },
  {
    title: 'Operator & User Accounts',
    href: '/users',
    icon: Users,
    description: 'Provision and manage operator logins with XAMPP MySQL and air-gapped sovereign SQLite sync.'
  },
];

export default function WorkbenchHomePage() {
  const router = useRouter();
  const fetchModels = useModelStore((s) => s.fetchModels);
  const fetchVRAM = useModelStore((s) => s.fetchVRAM);
  const fetchNetworkStatus = useSovereigntyStore((s) => s.fetchNetworkStatus);

  useEffect(() => {
    socketManager.connectAuditStream();
    fetchModels();
    fetchVRAM();
    fetchNetworkStatus();
  }, [fetchModels, fetchVRAM, fetchNetworkStatus]);

  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-900 font-sans">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {/* Executive Overview Deck */}
        <OverviewDeck onNavigate={(tab) => {
          const mapping: Record<string, string> = {
            router: '/router',
            rag: '/rag',
            upload: '/ocr',
            sovereignty: '/sovereignty',
            deliverables: '/deliverables',
            chat: '/chat'
          };
          router.push(mapping[tab] || '/');
        }} />

        {/* Subsystem Navigation Grid */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Modules
            </h2>
            
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {subsystemTiles.map((tile) => {
              const Icon = tile.icon;
              return (
                <Link
                  key={tile.href}
                  href={tile.href}
                  className="rounded-md bg-gray-50 border border-gray-200 p-4 hover:border-gray-300 hover:bg-gray-100 transition-all group flex flex-col justify-between space-y-3 cursor-pointer"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-gray-500 group-hover:text-gray-900 transition-colors" />
                        <h3 className="text-xs font-medium text-gray-900 group-hover:text-gray-900 transition-colors">
                          {tile.title}
                        </h3>
                      </div>
                      <ArrowRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-900 group-hover:translate-x-0.5 transition-all" />
                    </div>
                    <p className="text-[11px] text-gray-500 leading-relaxed">
                      {tile.description}
                    </p>
                  </div>

                  <div className="pt-2 flex items-center justify-between text-[10px] font-mono border-t border-gray-200">
                    <span className="text-gray-400">Path: {tile.href}</span>
                    <span className="px-2 py-0.5 rounded bg-gray-100 border border-gray-200 text-gray-900">
                      LAUNCH
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
