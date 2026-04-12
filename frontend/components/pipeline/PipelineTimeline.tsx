'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { StageState } from '@/lib/types';
import { cn, formatDuration, elapsedSince } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface PipelineTimelineProps {
  stages: StageState[];
}

export function PipelineTimeline({ stages }: PipelineTimelineProps) {
  const [tick, setTick] = useState(0);

  // Update elapsed timer every second for running stages
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-1">
      {stages.map((stage, i) => (
        <StageRow key={stage.id} stage={stage} index={i} tick={tick} />
      ))}
    </div>
  );
}

function StageRow({ stage, index, tick }: { stage: StageState; index: number; tick: number }) {
  const isRunning = stage.status === 'running';
  const isComplete = stage.status === 'complete';
  const isError = stage.status === 'error';
  const isPending = stage.status === 'pending';

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className={cn(
        'flex items-start gap-3 px-4 py-3 rounded-xl transition-all duration-300',
        isRunning && 'bg-cyan-500/5 border border-cyan-500/15',
        isComplete && 'opacity-80',
        isPending && 'opacity-40',
        isError && 'bg-red-500/5 border border-red-500/15'
      )}
    >
      {/* Icon / status indicator */}
      <div className="relative mt-0.5 flex-shrink-0">
        <div className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center text-base transition-all duration-300',
          isRunning && 'bg-cyan-500/20',
          isComplete && 'bg-emerald-500/15',
          isError && 'bg-red-500/15',
          isPending && 'bg-[var(--bg-elevated)]'
        )}>
          {isComplete ? '✓' : isError ? '✗' : stage.icon}
        </div>
        {isRunning && (
          <span className="absolute inset-0 rounded-full animate-ping bg-cyan-500/25" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className={cn(
            'text-sm font-medium',
            isComplete ? 'text-emerald-400' : isRunning ? 'text-white' : isError ? 'text-red-400' : 'text-slate-500'
          )}>
            {stage.label}
          </span>
          <span className="text-xs text-slate-500 flex-shrink-0">
            {isComplete && stage.startedAt && stage.completedAt &&
              formatDuration(stage.startedAt, stage.completedAt)}
            {isRunning && stage.startedAt &&
              <span className="text-cyan-400">{elapsedSince(stage.startedAt)}…</span>}
          </span>
        </div>
        {stage.message && (isRunning || isComplete || isError) && (
          <p className="text-xs text-slate-400 mt-0.5 truncate">{stage.message}</p>
        )}
      </div>
    </motion.div>
  );
}
