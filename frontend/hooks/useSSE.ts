'use client';

import { useEffect, useRef, useState } from 'react';
import { SSEEvent } from '@/lib/types';

export function useSSE(url: string | null) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!url) return;

    const source = new EventSource(url);
    sourceRef.current = source;

    source.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    source.onerror = () => {
      setError('Connection lost');
      setIsConnected(false);
    };

    const eventTypes = [
      'stage_start',
      'stage_progress',
      'stage_complete',
      'node_complete',
      'run_complete',
      'run_error',
    ];

    eventTypes.forEach((type) => {
      source.addEventListener(type, (e: MessageEvent) => {
        let data: Record<string, unknown> = {};
        try { data = JSON.parse(e.data); } catch {}

        const newEvent: SSEEvent = { event: type, data, timestamp: Date.now() };
        setEvents((prev) => [...prev, newEvent]);

        if (type === 'run_complete' || type === 'run_error') {
          source.close();
          setIsConnected(false);
          setIsDone(true);
        }
      });
    });

    return () => {
      source.close();
      setIsConnected(false);
    };
  }, [url]);

  return { events, isConnected, isDone, error };
}
