'use client';

import { useCallback, useMemo, useState } from 'react';
import { RunResult, SSEEvent, StageId, StageState, StageStatus } from '@/lib/types';
import { useSSE } from './useSSE';
import { getStreamUrl } from '@/lib/api';

const STAGE_DEFS: Omit<StageState, 'status'>[] = [
  { id: 'ad_analyzer', label: 'Analyzing Ad Creative', icon: '🎨' },
  { id: 'page_scraper', label: 'Scraping Landing Page', icon: '🌐' },
  { id: 'cro_strategist', label: 'CRO Analysis', icon: '📊' },
  { id: 'copywriter', label: 'Generating Copy', icon: '✍️' },
  { id: 'code_modifier', label: 'Applying Changes', icon: '🔧' },
  { id: 'qa_verifier', label: 'Quality Assurance', icon: '✅' },
];

export function usePipelineRun(runId: string | null) {
  const streamUrl = runId ? getStreamUrl(runId) : null;
  const { events, isConnected, isDone, error } = useSSE(streamUrl);

  const stages: StageState[] = useMemo(() => {
    const stageMap = new Map<StageId, StageState>(
      STAGE_DEFS.map((s) => [s.id, { ...s, status: 'pending' }])
    );

    for (const ev of events) {
      const { event, data, timestamp } = ev;

      if (event === 'stage_start') {
        const stage = stageMap.get(data.stage as StageId);
        if (stage) {
          stageMap.set(stage.id, { ...stage, status: 'running', message: data.message as string, startedAt: timestamp });
        }
      }

      if (event === 'stage_complete') {
        const stage = stageMap.get(data.stage as StageId);
        if (stage) {
          stageMap.set(stage.id, { ...stage, status: 'complete', message: data.message as string, completedAt: timestamp });
        }
      }

      if (event === 'run_error') {
        // Mark current running stage as error
        for (const [id, s] of stageMap) {
          if (s.status === 'running') stageMap.set(id, { ...s, status: 'error' });
        }
      }
    }

    return Array.from(stageMap.values());
  }, [events]);

  const result: RunResult | null = useMemo(() => {
    const completeEv = events.findLast((e) => e.event === 'run_complete');
    return completeEv ? (completeEv.data as unknown as RunResult) : null;
  }, [events]);

  const liveMessages = useMemo(
    () => events.filter((e) => ['stage_start', 'stage_progress', 'stage_complete'].includes(e.event)),
    [events]
  );

  return { stages, result, liveMessages, isConnected, isDone, error };
}
