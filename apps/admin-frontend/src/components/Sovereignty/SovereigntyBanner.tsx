'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, Wifi, Laptop, GlobeLock, Radio } from 'lucide-react';

export function SovereigntyBanner() {
  const { metrics, deploymentMode, hostIp, port } = useSovereigntyStore();

  // Only a *measured* zero counts as zero. A null packet count is "unknown".
  const isExternalZero = metrics.external_packets === 0 && metrics.external_sockets === 0;
  const packetText = (value: number | null) =>
    typeof value === 'number' ? value.toLocaleString() : '—';

  return (
    <div className="space-y-3">
      {/* Primary 3-Tier Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Tier 1: Local Loopback */}
        <Card className="border-gray-200 bg-gray-100 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-2 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Laptop className="h-4 w-4 text-gray-500" />
              <span className="text-xs font-semibold text-gray-900">
                Tier 1: Localhost IPC
              </span>
            </div>
            <Badge variant="secondary" className="font-mono text-[10px]">
              127.0.0.1
            </Badge>
          </div>

          <div className="py-3">
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-gray-900">
                {metrics.localhost_sockets}
              </span>
              <span className="text-xs text-gray-500">active internal sockets</span>
            </div>
            <p className="text-[11px] font-mono text-gray-400 mt-1">
              Local processes observed via psutil socket inspection
            </p>
          </div>

          <div className="pt-2 border-t border-gray-200/60 flex items-center justify-between text-[11px] font-mono text-gray-500">
            <span>Local Packets:</span>
            <span className="text-gray-900 font-medium">{packetText(metrics.localhost_packets)}</span>
          </div>
        </Card>

        {/* Tier 2: Authorized LAN / Hotspot Multi-Device */}
        <Card className="border-gray-200 bg-gray-100 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-2 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Wifi className="h-4 w-4 text-blue-600" />
              <span className="text-xs font-semibold text-gray-900">
                Tier 2: LAN / Hotspot
              </span>
            </div>
            <Badge variant="outline" className="font-mono text-[10px] text-blue-600">
              {deploymentMode === 'STANDALONE_LOCAL' ? 'Standalone' : 'Multi-Device'}
            </Badge>
          </div>

          <div className="py-3">
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-gray-900">
                {metrics.lan_hotspot_sockets}
              </span>
              <span className="text-xs text-gray-500">connected remote clients</span>
            </div>
            <p className="text-[11px] font-mono text-gray-400 mt-1">
              {deploymentMode === 'STANDALONE_LOCAL' 
                ? 'Host only (LAN listener ready on demand)' 
                : `Active Judge Session (${hostIp}:${port})`}
            </p>
          </div>

          <div className="pt-2 border-t border-gray-200/60 flex items-center justify-between text-[11px] font-mono text-gray-500">
            <span>Private LAN Packets:</span>
            <span className="text-gray-900 font-medium">{packetText(metrics.lan_hotspot_packets)}</span>
          </div>
        </Card>

        {/* Tier 3: External Internet Egress (measured sockets) */}
        <Card className={`p-4 flex flex-col justify-between border ${
          isExternalZero
            ? 'border-emerald-600/40 bg-emerald-50'
            : metrics.external_packets === null
            ? 'border-gray-300 bg-gray-50'
            : 'border-red-600 bg-red-600/10'
        }`}>
          <div className="flex items-center justify-between pb-2 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <GlobeLock className="h-4 w-4 text-emerald-600" />
              <span className="text-xs font-semibold text-gray-900">
                Tier 3: External WAN Egress
              </span>
            </div>
            <div className="flex items-center space-x-1.5">
              <motion.span
                animate={{ scale: [1, 1.3, 1], opacity: [1, 0.6, 1] }}
                transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                className={`h-2 w-2 rounded-full inline-block ${isExternalZero ? 'bg-emerald-600' : 'bg-gray-400'}`}
              />
              <span className={`text-[10px] font-mono font-bold tracking-wider uppercase ${isExternalZero ? 'text-emerald-600' : 'text-gray-500'}`}>
                {isExternalZero ? 'No External Sockets' : metrics.external_packets === null ? 'Not Measured' : 'Egress Observed'}
              </span>
            </div>
          </div>

          <div className="py-3">
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-black font-mono text-gray-900">
                {packetText(metrics.external_packets)}
              </span>
              <span className="text-xs text-gray-500">
                external packets
                {typeof metrics.external_bytes === 'number'
                  ? ` (${metrics.external_bytes.toLocaleString()} bytes)`
                  : ' (bytes not measured)'}
              </span>
            </div>
            <p className="text-[11px] font-mono text-emerald-600 mt-1 font-medium flex items-center">
              <ShieldCheck className="h-3.5 w-3.5 mr-1" />
              {metrics.verdict || 'UNKNOWN - no verdict reported'}
            </p>
            <p className="text-[10px] font-mono text-gray-400 mt-1">
              Socket counts are measured with psutil; packet totals are not counted on this deployment.
            </p>
          </div>

          <div className="pt-2 border-t border-gray-200/60 flex items-center justify-between text-[11px] font-mono text-gray-500">
            <span>External Sockets:</span>
            {/* "Blocked" is only accurate when the count is non-zero. The old
                label printed "0 (Blocked)", which reads as a claim rather than
                a measurement. */}
            <span className={metrics.external_sockets > 0 ? 'text-rose-600 font-semibold' : 'text-emerald-600 font-semibold'}>
              {metrics.external_sockets}
              {metrics.external_sockets > 0 ? ' (blocked)' : ' (none observed)'}
            </span>
          </div>
        </Card>
      </div>
    </div>
  );
}
