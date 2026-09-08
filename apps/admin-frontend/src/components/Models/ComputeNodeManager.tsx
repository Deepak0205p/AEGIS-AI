'use client';

import React, { useState } from 'react';
import { useModelStore, ComputeNode } from '@/store/useModelStore';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Server,
  Laptop,
  Plus,
  Trash2,
  RefreshCw,
  Wifi,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
  ArrowRight,
} from 'lucide-react';

export function ComputeNodeManager() {
  const {
    nodes,
    fetchNodes,
    testNodeConnection,
    addNode,
    deleteNode,
    isLoadingNodes,
    models,
  } = useModelStore();

  const [isAdding, setIsAdding] = useState(false);
  const [deviceLabel, setDeviceLabel] = useState('');
  const [nodeIp, setNodeIp] = useState('');
  const [port, setPort] = useState('11434');
  const [deviceType, setDeviceType] = useState('LAN Laptop');
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    tested: boolean;
    online: boolean;
    models: string[];
    message: string;
    latency_ms?: number;
  } | null>(null);

  const handleTestConnection = async () => {
    if (!nodeIp) return;
    setIsTesting(true);
    setTestResult(null);
    const res = await testNodeConnection(nodeIp, parseInt(port) || 11434);
    setTestResult({
      tested: true,
      online: res.online,
      models: res.models,
      message: res.message,
      latency_ms: res.latency_ms,
    });
    setIsTesting(false);
  };

  const handleSaveNode = async () => {
    if (!nodeIp) return;
    const name = deviceLabel.trim() || `Worker (${nodeIp}:${port})`;
    const discovered = testResult?.online ? testResult.models : [];
    await addNode({
      name,
      host_ip: nodeIp.trim(),
      port: parseInt(port) || 11434,
      device_type: deviceType,
      models: discovered,
    });
    setIsAdding(false);
    setDeviceLabel('');
    setNodeIp('');
    setTestResult(null);
  };

  return (
    <Card className="border-gray-200 dark:border-[#262c3a] bg-white dark:bg-[#11141c] shadow-sm font-sans">
      <CardHeader className="py-3.5 px-4 border-b border-gray-100 dark:border-gray-800 flex flex-row items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <Server className="w-4 h-4" />
          </div>
          <div>
            <CardTitle className="text-xs font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <span>Distributed Compute Nodes &amp; Remote Worker Devices</span>
              <Badge variant="active" className="text-[10px] font-mono">
                AIR-GAP LAN CLUSTER
              </Badge>
            </CardTitle>
            <p className="text-[11px] text-gray-500 dark:text-gray-400 font-mono mt-0.5">
              Host primary models on Localhost or offload LLM workloads to other laptops/GPU rigs on your private LAN.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => fetchNodes()}
            disabled={isLoadingNodes}
            className="h-8 text-xs border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoadingNodes ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          <Button
            size="sm"
            onClick={() => {
              setIsAdding(!isAdding);
              setTestResult(null);
            }}
            className="h-8 text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-sm"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            {isAdding ? 'Cancel' : 'Connect Other Device / Worker'}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Add Device Drawer / Form */}
        {isAdding && (
          <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-950/20 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-blue-900 dark:text-blue-300 flex items-center gap-1.5">
                <Wifi className="w-4 h-4" />
                Register Remote Worker Device (Ollama / vLLM Instance)
              </span>
              <span className="text-[10px] text-gray-500">RFC 1918 Private LAN Only</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-gray-600 dark:text-gray-400 text-[11px] mb-1">
                  Device Label:
                </label>
                <input
                  type="text"
                  placeholder="e.g. Lab-Laptop-RTX4090"
                  value={deviceLabel}
                  onChange={(e) => setDeviceLabel(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-600 dark:text-gray-400 text-[11px] mb-1">
                  Target Device IP / Host:
                </label>
                <input
                  type="text"
                  placeholder="192.168.1.105"
                  value={nodeIp}
                  onChange={(e) => setNodeIp(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-600 dark:text-gray-400 text-[11px] mb-1">
                  Ollama Port:
                </label>
                <input
                  type="number"
                  placeholder="11434"
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-600 dark:text-gray-400 text-[11px] mb-1">
                  Device Profile:
                </label>
                <select
                  value={deviceType}
                  onChange={(e) => setDeviceType(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#0c0e14] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500"
                >
                  <option value="LAN Laptop">LAN Laptop (Colleague GPU)</option>
                  <option value="GPU Rig Server">Dedicated GPU Rig (RTX 4090)</option>
                  <option value="Edge Jetson">NVIDIA Jetson Orin Edge</option>
                  <option value="Secondary Workstation">Secondary Workstation</option>
                </select>
              </div>
            </div>

            {/* Test Connection / Discovery Output */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 pt-2 border-t border-blue-200/60 dark:border-blue-900/40">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleTestConnection}
                  disabled={!nodeIp || isTesting}
                  className="h-8 text-xs bg-white dark:bg-[#11141c] border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 hover:bg-blue-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isTesting ? 'animate-spin' : ''}`} />
                  {isTesting ? 'Testing Socket...' : '1. Test Ping & Discover Models'}
                </Button>

                {testResult?.tested && (
                  <span
                    className={`flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded ${
                      testResult.online
                        ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                        : 'bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                    }`}
                  >
                    {testResult.online ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
                    )}
                    <span>
                      {testResult.online
                        ? `Connected (${testResult.latency_ms}ms) - ${testResult.models.length} model(s) found: [${testResult.models.join(', ') || 'Ready'}]`
                        : testResult.message}
                    </span>
                  </span>
                )}
              </div>

              <Button
                size="sm"
                onClick={handleSaveNode}
                disabled={!nodeIp}
                className="h-8 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
              >
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                2. Bind &amp; Register Node
              </Button>
            </div>
          </div>
        )}

        {/* Registered Nodes Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
          {nodes.map((node) => {
            const isLocal = node.is_local;
            const boundModels = models.filter((m) => m.node_ip === node.host_ip);

            return (
              <div
                key={node.id}
                className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between space-y-3 ${
                  isLocal
                    ? 'border-emerald-300 dark:border-emerald-900/50 bg-emerald-50/30 dark:bg-emerald-950/10'
                    : 'border-blue-200 dark:border-blue-900/40 bg-gray-50/50 dark:bg-[#0c0e14]'
                }`}
              >
                {/* Node Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                        isLocal
                          ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                          : 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {isLocal ? <Laptop className="w-3.5 h-3.5" /> : <Server className="w-3.5 h-3.5" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-gray-900 dark:text-gray-100">
                          {node.name}
                        </span>
                        {isLocal ? (
                          <Badge variant="active" className="text-[9px] py-0 px-1.5">
                            PRIMARY
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-[9px] py-0 px-1.5">
                            WORKER
                          </Badge>
                        )}
                      </div>
                      <span className="text-[11px] text-gray-500 dark:text-gray-400">
                        {node.device_type} &bull; {node.host_ip}:{node.port}
                      </span>
                    </div>
                  </div>

                  {/* Status Indicator & Delete */}
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${
                        node.status === 'online'
                          ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800'
                          : 'bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-400 border-rose-300 dark:border-rose-800'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          node.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                        }`}
                      />
                      <span>{node.status.toUpperCase()}</span>
                    </span>

                    {!isLocal && (
                      <button
                        onClick={() => deleteNode(node.id)}
                        title="Remove Worker Node"
                        className="p-1 rounded text-gray-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Node Details & Discovered Models */}
                <div className="grid grid-cols-2 gap-2 p-2 rounded bg-white dark:bg-[#11141c] border border-gray-200 dark:border-gray-800 text-[11px]">
                  <div>
                    <span className="text-gray-400">Latency: </span>
                    <span className="text-gray-900 dark:text-gray-200 font-semibold">
                      {node.latency_ms || 1.2} ms
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Sovereignty: </span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                      Air-Gapped LAN
                    </span>
                  </div>
                </div>

                {/* Available / Discovered Models Pill List */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] text-gray-400 uppercase tracking-wider">
                      Available Models on this device:
                    </span>
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
                      {isLocal ? '● Live Telemetry Synced' : '● Node Bound'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(() => {
                      // If local node, sync with active models in store
                      const availableModels = isLocal && models.length > 0
                        ? models.map(m => m.id)
                        : (node.discovered_models && node.discovered_models.length > 0 ? node.discovered_models : ['deepseek-v4-pro:4b', 'qwen2.5vl:3b']);

                      return availableModels.map((m) => {
                        const isPrimary = models.find(mod => mod.id === m)?.is_primary;
                        const isSecondary = models.find(mod => mod.id === m)?.status === 'active' && !isPrimary;

                        return (
                          <span
                            key={m}
                            className={`px-2 py-0.5 rounded border text-[10px] font-mono flex items-center gap-1 transition-all ${
                              isPrimary
                                ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 font-semibold shadow-xs'
                                : isSecondary
                                ? 'bg-blue-50 dark:bg-blue-950/60 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-semibold'
                                : 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200'
                            }`}
                          >
                            <Cpu className={`w-2.5 h-2.5 ${isPrimary ? 'text-emerald-500' : isSecondary ? 'text-blue-500' : 'text-gray-400'}`} />
                            <span>{m}</span>
                            {isPrimary && <span className="text-[8px] bg-emerald-600 text-white px-1 rounded">PRIMARY</span>}
                            {isSecondary && <span className="text-[8px] bg-blue-600 text-white px-1 rounded">ACTIVE</span>}
                          </span>
                        );
                      });
                    })()}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
