'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Route } from 'lucide-react';

interface RouterTagBadgeProps {
  modelId?: string;
  routedBy?: 'stage1_regex' | 'stage2_semantic' | 'manual';
  confidence?: number | null;
}

export function RouterTagBadge({ modelId = '', routedBy = 'stage1_regex', confidence }: RouterTagBadgeProps) {
  const modelName = modelId || 'Sovereign Engine';
  const routeType = routedBy === 'stage1_regex' ? 'Stage 1 Rule' : routedBy === 'stage2_semantic' ? 'Stage 2 Semantic' : 'Manual';
  // The pipeline reports no calibrated confidence - never invent one.
  const confidenceLabel = typeof confidence === 'number' ? `${confidence}%` : 'confidence n/a';

  return (
    <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded border border-gray-200 bg-gray-50 text-[11px] font-mono">
      <Route className="h-3 w-3 text-blue-600" />
      <span className="text-gray-500">Routed:</span>
      <span className="text-gray-900 font-medium">{modelName}</span>
      <span className="text-gray-200">|</span>
      <span className="text-gray-500">{routeType} ({confidenceLabel})</span>
    </div>
  );
}
