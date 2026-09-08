'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useModelStore } from '@/store/useModelStore';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRightLeft, CheckCircle2 } from 'lucide-react';

export function ModelCardGrid() {
  const { models, activePrimaryId, activeSecondaryId, isSwapping, triggerModelSwap, nodes, bindModelToNode } = useModelStore();

  if (models.length === 0) {
    return (
      <div className="p-8 text-center rounded-md bg-gray-50 border border-gray-200 font-mono text-xs text-gray-500 space-y-2">
        <p className="text-gray-900 font-semibold">No LLM weights (.gguf / Ollama models) detected in local codebase</p>
        <p className="text-gray-400 text-[11px]">
          Place GGUF models in <code className="text-emerald-600">/models/gguf</code> or pull via Ollama to activate dynamic LLM orchestration.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {models.map((model) => {
        const isPrimaryActive = model.id === activePrimaryId;
        const isSecondaryActive = model.id === activeSecondaryId;
        const isLoadedInVram = isPrimaryActive || isSecondaryActive;

        return (
          <motion.div
            key={model.id}
            initial={{ opacity: 0, transform: "scale(0.98) translateY(4px)" }}
            animate={{ opacity: 1, transform: "scale(1) translateY(0px)" }}
            transition={{ type: "spring", stiffness: 120, damping: 22 }}
          >
            <Card className={`border transition-colors min-h-[220px] flex flex-col justify-between ${
              isLoadedInVram 
                ? 'border-blue-600/40 bg-gray-100' 
                : 'border-gray-200 bg-gray-100'
            }`}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
                      {model.domain}
                    </span>
                    <CardTitle className="text-xs font-semibold text-gray-900">
                      {model.display_name || model.name}
                    </CardTitle>
                  </div>

                  <div className="flex items-center space-x-1.5 min-w-[70px] justify-end">
                    {isPrimaryActive && (
                      <Badge variant="active">PRIMARY</Badge>
                    )}
                    {isSecondaryActive && (
                      <Badge variant="active">ACTIVE</Badge>
                    )}
                    {!isLoadedInVram && (
                      <Badge variant="secondary">STANDBY</Badge>
                    )}
                  </div>
                </div>
                {/* Reserved height to prevent CLS */}
                <CardDescription className="text-xs text-gray-500 mt-1 min-h-[32px] line-clamp-2">
                  {model.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="py-2 text-xs">
                <div className="grid grid-cols-2 gap-2 p-2.5 rounded bg-gray-50 border border-gray-200 font-mono text-[11px]">
                  <div>
                    <span className="text-gray-400">Architecture: </span>
                    <span className="text-gray-900">Air-Gapped Sovereign</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Quant: </span>
                    <span className="text-gray-900">{model.quantization}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Footprint: </span>
                    <span className="text-gray-900 font-medium tabular-nums">{model.vram_mb} MB</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Memory State: </span>
                    <span className={isLoadedInVram ? "text-emerald-600" : "text-gray-400"}>
                      {isLoadedInVram ? "Loaded in VRAM" : "Paged out (LRU)"}
                    </span>
                  </div>
                </div>

                {/* 1-IP Hybrid Node Binding with Selector */}
                <div className="mt-2.5 flex items-center justify-between px-2.5 py-1.5 rounded bg-gray-50 border border-gray-100 font-mono text-[11px]">
                  <div className="flex items-center space-x-1.5">
                    <div className={`h-1.5 w-1.5 rounded-full ${model.node_ip && model.node_ip !== '127.0.0.1' ? 'bg-blue-600 animate-pulse' : 'bg-emerald-600'}`} />
                    <span className="text-gray-500">Compute Node:</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <select
                      value={nodes.find(n => n.host_ip === model.node_ip)?.id || 'node-local'}
                      onChange={(e) => bindModelToNode(model.id, e.target.value)}
                      className="text-[10px] bg-white border border-gray-200 rounded px-1.5 py-0.5 text-gray-900 font-mono focus:outline-none focus:border-blue-500"
                    >
                      {nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.host_ip}:{n.port} ({n.is_local ? 'Local GPU' : n.device_type})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </CardContent>

              <CardFooter className="pt-2 flex justify-between items-center mt-2 border-t border-gray-200/50 min-h-[52px]">
                <span className="text-[11px] text-gray-400 font-mono">
                  Swap Latency: &lt;1.2s
                </span>

                {!model.is_primary && (
                  /* 44px touch target envelope (ui-ux-pro-max Priority 2) */
                  <div className="flex items-center min-h-[44px]">
                    <Button
                      size="sm"
                      variant={isSecondaryActive ? "secondary" : "outline"}
                      disabled={isSecondaryActive || isSwapping}
                      onClick={() => triggerModelSwap(model.id)}
                      className="h-9 px-3.5 text-xs flex items-center space-x-1.5 active:scale-[0.97] transition-transform"
                    >
                      <ArrowRightLeft className={`h-3.5 w-3.5 ${isSwapping ? 'animate-spin' : ''}`} />
                      <span>{isSecondaryActive ? 'Loaded in VRAM' : 'Swap In (LRU)'}</span>
                    </Button>
                  </div>
                )}

                {model.is_primary && (
                  <div className="flex items-center space-x-1.5 text-emerald-600 text-xs font-mono min-h-[44px]">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Permanent Lock</span>
                  </div>
                )}
              </CardFooter>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}

