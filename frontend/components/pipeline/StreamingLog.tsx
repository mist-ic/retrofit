'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { SSEEvent } from '@/lib/types';
import { useEffect, useRef } from 'react';

interface StreamingLogProps {
  events: SSEEvent[];
}

const EVENT_COLORS: Record<string, string> = {
  stage_start: 'text-cyan-400',
  stage_progress: 'text-slate-300',
  stage_complete: 'text-emerald-400',
  run_complete: 'text-purple-400',
  run_error: 'text-red-400',
};

export function StreamingLog({ events }: StreamingLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  return (
    <div className="h-48 overflow-y-auto rounded-xl bg-[var(--bg-elevated)] border border-[var(--border)] p-3 font-mono text-xs">
      <AnimatePresence initial={false}>
        {events.map((ev, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className={`leading-5 ${EVENT_COLORS[ev.event] || 'text-slate-400'}`}
          >
            <span className="text-slate-600 mr-2">[{new Date(ev.timestamp).toLocaleTimeString()}]</span>
            {(ev.data.message as string) || ev.event}
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
