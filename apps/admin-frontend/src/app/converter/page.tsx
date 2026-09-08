'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { DocumentConverterObservatory } from '@/components/DocumentConverterObservatory';

export default function DocumentConverterPage() {
  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-900 font-sans">
      <Header />
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        <DocumentConverterObservatory />
      </main>
    </div>
  );
}
