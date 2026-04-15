"use client";

/**
 * useSSE — connects to the RetroFit backend SSE stream and manages pipeline state.
 *
 * Fixes vs. the old implementation:
 * 1. Listens to ALL agent events: stage_start, stage_progress, stage_complete, stage_error
 * 2. Prevents EventSource auto-reconnect after stream completes
 * 3. Exposes rich StageState map for the PipelineTimeline component
 * 4. Exposes typed RunResult for the results dashboard
 */

import { useEffect, useRef, useState, useCallback } from "react";
import type { RunResult, StageId, StageState, LogEntry } from "@/lib/types";

export type PipelineStatus = "idle" | "running" | "complete" | "error";

export const STAGE_META: Record<StageId, { label: string; description: string }> = {
  ad_analyzer:    { label: "Ad Analysis",       description: "Analyzing ad creative with Gemini vision" },
  page_scraper:   { label: "Page Scraping",      description: "Scraping + semantically mapping the landing page" },
  cro_strategist: { label: "CRO Strategy",       description: "Scoring message match, hero clarity, CTAs" },
  copywriter:     { label: "Copy Generation",    description: "Writing personalized replacement copy" },
  code_modifier:  { label: "DOM Patching",       description: "Applying surgical HTML modifications" },
  qa_verifier:    { label: "QA Verification",    description: "Hallucination + structural + visual checks" },
};

const STAGE_ORDER: StageId[] = [
  "ad_analyzer",
  "page_scraper",
  "cro_strategist",
  "copywriter",
  "code_modifier",
  "qa_verifier",
];

function initialStages(): Record<StageId, StageState> {
  const stages = {} as Record<StageId, StageState>;
  for (const id of STAGE_ORDER) {
    stages[id] = { id, status: "pending", message: "" };
  }
  return stages;
}

export function useSSE(runId: string) {
  const [status, setStatus] = useState<PipelineStatus>("idle");
  const [stages, setStages] = useState<Record<StageId, StageState>>(initialStages);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [finalResult, setFinalResult] = useState<RunResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Prevent double-connect in React StrictMode and prevent reconnect after done
  const isDone = useRef(false);
  const hasConnected = useRef(false);

  const addLog = useCallback((entry: Omit<LogEntry, "id" | "timestamp">) => {
    setLogs((prev) => [
      ...prev,
      {
        ...entry,
        id: Math.random().toString(36).slice(2, 10),
        timestamp: new Date().toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      },
    ]);
  }, []);

  const updateStage = useCallback((stageId: StageId, update: Partial<StageState>) => {
    setStages((prev) => ({
      ...prev,
      [stageId]: { ...prev[stageId], ...update },
    }));
  }, []);

  useEffect(() => {
    if (!runId || hasConnected.current) return;
    hasConnected.current = true;
    isDone.current = false;

    setStatus("running");
    setStages(initialStages());
    setLogs([]);

    // ⚠️  Connect DIRECTLY to the FastAPI backend — not through the Next.js proxy.
    // Next.js dev Turbopack buffers the rewritten response, breaking SSE delivery.
    // The backend CORS config explicitly allows http://localhost:3000, so this is safe.
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8080";
    const es = new EventSource(`${BACKEND_URL}/api/runs/${runId}/stream`);

    // ── Generic onerror (network drop / server close) ────────────────────────
    es.onerror = () => {
      // If pipeline already finished, the server closed the connection on purpose — ignore.
      if (isDone.current) return;
      // If we're still running, this is a real connection error
      setStatus("error");
      setErrorMessage("SSE connection lost. The backend may have crashed.");
      addLog({ stage: "system", message: "Connection lost — check backend terminal for errors.", type: "error" });
      es.close();
    };

    es.onopen = () => {
      addLog({ stage: "system", message: "Connected to pipeline node stream.", type: "system" });
    };

    // ── Stage lifecycle events (emitted by agent writer() calls) ─────────────

    es.addEventListener("stage_start", (e) => {
      const d = JSON.parse(e.data);
      const id = d.stage as StageId;
      updateStage(id, { status: "running", message: d.message, startedAt: Date.now() });
      addLog({ stage: id, message: d.message, type: "start" });
    });

    es.addEventListener("stage_progress", (e) => {
      const d = JSON.parse(e.data);
      const id = d.stage as StageId;
      updateStage(id, { message: d.message });
      addLog({ stage: id, message: d.message, type: "progress" });
    });

    es.addEventListener("stage_complete", (e) => {
      const d = JSON.parse(e.data);
      const id = d.stage as StageId;
      updateStage(id, {
        status: "complete",
        message: d.message,
        completedAt: Date.now(),
        data: d.data,
      });
      addLog({ stage: id, message: d.message, type: "complete" });
    });

    es.addEventListener("stage_error", (e) => {
      const d = JSON.parse(e.data);
      const id = d.stage as StageId;
      updateStage(id, { status: "error", message: d.message });
      addLog({ stage: id, message: `Error: ${d.message}`, type: "error" });
    });

    // ── LangGraph node completion events ─────────────────────────────────────

    es.addEventListener("node_complete", (e) => {
      const d = JSON.parse(e.data);
      addLog({
        stage: d.node || "system",
        message: `Node complete — updated: ${(d.keys_updated || []).join(", ")}`,
        type: "node",
      });
    });

    // ── Final result (pipeline done) ─────────────────────────────────────────

    es.addEventListener("run_complete", (e) => {
      isDone.current = true;
      const result: RunResult = JSON.parse(e.data);
      setFinalResult(result);
      setStatus("complete");
      // Mark any still-running stages as complete (safety net for races)
      setStages((prev) => {
        const next = { ...prev };
        for (const id of STAGE_ORDER) {
          if (next[id].status === "running") {
            next[id] = { ...next[id], status: "complete" };
          }
        }
        return next;
      });
      addLog({ stage: "system", message: `Pipeline complete — status: ${result.status}`, type: "complete" });
      es.close();
    });

    // ── Fatal pipeline error ──────────────────────────────────────────────────

    es.addEventListener("run_error", (e) => {
      isDone.current = true;
      const d = JSON.parse(e.data);
      setStatus("error");
      setErrorMessage(d.error || "Unknown pipeline error");
      addLog({ stage: "system", message: `Fatal: ${d.error}`, type: "error" });
      es.close();
    });

    return () => {
      es.close();
      hasConnected.current = false;
    };
  }, [runId, addLog, updateStage]);

  return {
    status,
    stages,
    stageOrder: STAGE_ORDER,
    logs,
    finalResult,
    errorMessage,
  };
}
