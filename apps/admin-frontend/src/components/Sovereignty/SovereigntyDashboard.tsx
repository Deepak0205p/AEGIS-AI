'use client';

import React from 'react';
import { SovereigntyBanner } from './SovereigntyBanner';
import { ActiveSocketTable } from './ActiveSocketTable';
import { TamperEvidentLogViewer } from './TamperEvidentLogViewer';
import { ComputeNodeManager } from '../Models/ComputeNodeManager';

export function SovereigntyDashboard() {
  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* 3-Tier Traffic Breakdown Summary */}
      <SovereigntyBanner />

      {/* Multi-Node Compute & Remote Worker Devices Manager */}
      <ComputeNodeManager />

      {/* Active Sockets Live Sniffer Table */}
      <ActiveSocketTable />

      {/* SHA-256 Chained Immutable Audit Log */}
      <TamperEvidentLogViewer />
    </div>
  );
}
