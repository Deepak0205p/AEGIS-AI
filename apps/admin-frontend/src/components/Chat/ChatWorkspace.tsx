'use client';

import React, { useEffect, useState } from 'react';
import { ChatContainer } from './ChatContainer';
import { PromptInputDock } from './PromptInputDock';
import { ScenarioSelector } from './ScenarioSelector';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Bot, Zap, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface SandboxStatus {
  active_backend?: string;
  docker_available?: boolean;
  job_object_available?: boolean;
  filesystem_jailed?: boolean;
  memory_limit?: string;
  timeout_seconds?: number;
  static_screen?: {
    basis?: string;
    forbidden_module_prefixes?: number;
    forbidden_attributes?: number;
  };
  not_enforced_without_docker?: string[];
}

export function ChatWorkspace() {
  const [sandbox, setSandbox] = useState<SandboxStatus | null>(null);
  const [sandboxError, setSandboxError] = useState<string | null>(null);

  // Guardrail values are read from the backend, never hard-coded.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.get<SandboxStatus>('/api/sandbox/status');
        if (!cancelled) setSandbox(data);
      } catch (err: any) {
        if (!cancelled) setSandboxError(err?.message || 'Sandbox status unavailable.');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      {/* Main Conversation & Trace Viewport (3 Cols) */}
      <div className="lg:col-span-3 space-y-3 flex flex-col">
        {/* Scenario Quick-Launch Bar */}
        <ScenarioSelector />

        {/* Chat Scroll Container */}
        <Card className="flex-1 border-gray-200 bg-gray-100 p-4 flex flex-col justify-between min-h-[460px]">
          <ChatContainer />
          
          {/* Input Dock at Bottom */}
          <div className="pt-3 border-t border-gray-200/80 mt-2">
            <PromptInputDock />
          </div>
        </Card>
      </div>

      {/* Side Telemetry & Router Panel (1 Col) */}
      <div className="space-y-3">
        <Card className="border-gray-200 bg-gray-100">
          <CardHeader className="py-2.5 px-3.5 border-b border-gray-200">
            <div className="flex items-center space-x-1.5">
              <Bot className="h-3.5 w-3.5 text-blue-600" />
              <CardTitle className="text-xs font-semibold text-gray-900">
                Execution Guardrails
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-3 text-xs space-y-2.5 font-mono text-[11px]">
            {!sandbox && !sandboxError && (
              <div className="flex items-center gap-1.5 text-gray-500">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Reading sandbox status...</span>
              </div>
            )}
            {sandboxError && (
              <p className="text-rose-600">{sandboxError}</p>
            )}
            {sandbox && (
              <>
                <div>
                  <p className="text-gray-500">Runner:</p>
                  <p className="text-gray-900 font-medium">{sandbox.active_backend || 'unknown'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Network isolation:</p>
                  <p className={sandbox.docker_available ? 'text-emerald-600 font-medium' : 'text-amber-600 font-medium'}>
                    {/* Must not claim "None" when Docker is absent: the no-Docker
                        path still enforces limits via a Windows Job Object plus
                        an injected in-process network guard. */}
                    {sandbox.docker_available
                      ? 'Docker (--network none)'
                      : (sandbox.job_object_available
                          ? 'In-process guard (loopback + RFC 1918 only)'
                          : 'In-process guard only')}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Memory limit:</p>
                  <p className="text-gray-900 font-medium">{sandbox.memory_limit || 'n/a'}</p>
                </div>
                <div>
                  <p className="text-gray-500">CPU cap:</p>
                  <p className="text-gray-900 font-medium">
                    {sandbox.docker_available ? '1 vCPU' : (sandbox.job_object_available ? 'CPU-time limited' : 'timeout only')}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Execution timeout:</p>
                  <p className="text-gray-900 font-medium">
                    {sandbox.timeout_seconds != null ? `${sandbox.timeout_seconds}s` : 'n/a'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Static screen:</p>
                  <p className="text-gray-900 font-medium">
                    {sandbox.static_screen?.basis === 'ast_static_analysis'
                      ? `AST (${sandbox.static_screen.forbidden_module_prefixes} modules, ${sandbox.static_screen.forbidden_attributes} attrs)`
                      : 'none'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Filesystem jail:</p>
                  <p className={sandbox.filesystem_jailed ? 'text-emerald-600 font-medium' : 'text-amber-600 font-medium'}>
                    {sandbox.filesystem_jailed ? 'Yes (container namespace)' : 'No (not enforced without Docker)'}
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="border-gray-200 bg-gray-100">
          <CardHeader className="py-2.5 px-3.5 border-b border-gray-200">
            <div className="flex items-center space-x-1.5">
              <Zap className="h-3.5 w-3.5 text-amber-500" />
              <CardTitle className="text-xs font-semibold text-gray-900">
                Two-Stage Router
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-3 text-xs space-y-2 text-[11px]">
            <p className="text-gray-500">
              <strong className="text-gray-900">Stage 1:</strong> Compiled keyword / regex rules (sub-millisecond).
            </p>
            <p className="text-gray-500">
              <strong className="text-gray-900">Stage 2:</strong>{' '}
              Not configured. This deployment resolves routing on stage-1 rules
              and equipment tags only, so no semantic stage runs.
            </p>
            <p className="text-gray-400">
              The router does not produce a calibrated confidence value.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
