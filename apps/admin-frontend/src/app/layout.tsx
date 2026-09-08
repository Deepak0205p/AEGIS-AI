import './globals.css';
import React from 'react';
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import { AuthGuard } from '@/components/AuthGuard';

export const metadata = {
  title: 'AEGIS AI Admin',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="bg-white dark:bg-[#000000] text-gray-900 dark:text-[#ededed] font-sans antialiased min-h-screen flex flex-col selection:bg-cyan-500/20 selection:text-cyan-300">
        <AuthGuard>{children}</AuthGuard>
      </body>
    </html>
  );
}
