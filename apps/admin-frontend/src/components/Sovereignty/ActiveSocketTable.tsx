'use client';

import React, { useState } from 'react';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Network, ShieldCheck, Search } from 'lucide-react';

export function ActiveSocketTable() {
  const { sockets, metrics } = useSovereigntyStore();
  const [filterQuery, setFilterQuery] = useState('');

  const filteredSockets = sockets.filter((s) => 
    s.process_name.toLowerCase().includes(filterQuery.toLowerCase()) ||
    s.local_address.includes(filterQuery) ||
    s.remote_address.includes(filterQuery)
  );

  return (
    <Card className="border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] shadow-sm">
      <CardHeader className="py-3 px-4 border-b border-gray-100 dark:border-gray-800">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <Network className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <CardTitle className="text-xs font-semibold text-gray-900 dark:text-gray-100">
              Project Socket Sniffer &amp; Air-Gap Guard (psutil Daemon)
            </CardTitle>
            <Badge variant="active" className="font-mono text-[10px]">
              {sockets.length} Project Sockets Filtered
            </Badge>
          </div>

          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="h-3 w-3 absolute left-2.5 top-2 text-gray-400" />
              <input
                type="text"
                placeholder="Filter project services / IPs..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                className="h-7 pl-7 pr-2.5 rounded bg-gray-50 dark:bg-[#0c0e14] border border-gray-200 dark:border-gray-700 text-[11px] text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:border-blue-600"
              />
            </div>
            <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 flex items-center">
              <ShieldCheck className="h-3.5 w-3.5 mr-1" />
              WAN Auto-Block Active
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-gray-50 text-gray-500 text-[11px] font-mono border-b border-gray-200">
              <tr>
                <th className="py-2.5 px-3.5">PID</th>
                <th className="py-2.5 px-3.5">Process Name</th>
                <th className="py-2.5 px-3.5">Local Binding</th>
                <th className="py-2.5 px-3.5">Remote Endpoint</th>
                <th className="py-2.5 px-3.5">Tier Classification</th>
                <th className="py-2.5 px-3.5">Status</th>
                <th className="py-2.5 px-3.5 text-right">Security Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200/50 font-mono text-[11px]">
              {filteredSockets.map((sock) => (
                <tr key={sock.id} className="hover:bg-gray-200">
                  <td className="py-2 px-3.5 text-gray-400">{sock.pid}</td>
                  <td className="py-2 px-3.5 text-gray-900 font-medium">{sock.process_name}</td>
                  <td className="py-2 px-3.5 text-gray-500">{sock.local_address}</td>
                  <td className="py-2 px-3.5 text-gray-900">{sock.remote_address}</td>
                  <td className="py-2 px-3.5">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                      sock.tier === 'LOCALHOST'
                        ? 'border-gray-300 bg-gray-200 text-gray-500'
                        : sock.tier === 'LAN_HOTSPOT'
                        ? 'border-blue-600/40 bg-blue-50 text-blue-600'
                        : 'border-red-600 bg-red-600/10 text-red-600'
                    }`}>
                      {sock.tier}
                    </span>
                  </td>
                  <td className="py-2 px-3.5 text-gray-500">{sock.status}</td>
                  <td className="py-2 px-3.5 text-right">
                    <Badge variant={sock.security_verdict === 'BREACH_FLAGGED' ? 'destructive' : 'success'} className="text-[10px] py-0">
                      {sock.security_verdict}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
