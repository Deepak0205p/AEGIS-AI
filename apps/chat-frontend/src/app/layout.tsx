import './globals.css';
import React from 'react';
import type { Metadata, Viewport } from 'next';
import { ThemeProvider } from '@/components/ThemeProvider';

export const metadata: Metadata = {
  title: 'AEGIS AI',
  description: 'On-premise air-gapped sovereign industrial AI workbench with multi-model orchestrator.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-white text-slate-900 dark:bg-[#131314] dark:text-[#e3e3e3] font-sans antialiased h-screen h-[100dvh] flex flex-col selection:bg-blue-500/20 dark:selection:bg-[#a8c7fa]/30 overflow-hidden">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
