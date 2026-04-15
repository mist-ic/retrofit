"use client";

import { use, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  LayoutGrid,
  SlidersHorizontal,
  BarChart3,
  FileText,
  Code2,
  ShieldCheck,
  PanelLeftClose,
  PanelLeftOpen,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

import { useSSE, STAGE_META } from "@/hooks/useSSE";
import { PipelineTimeline } from "@/components/pipeline/PipelineTimeline";
import { CROScorecard } from "@/components/results/CROScorecard";
import { BeforeAfterSlider } from "@/components/results/BeforeAfterSlider";
import { PagePreview } from "@/components/results/PagePreview";
import { ExplanationPanel } from "@/components/results/ExplanationPanel";
import { PatchDiffViewer } from "@/components/results/PatchDiffViewer";
import { QAReportPanel } from "@/components/results/QAReportPanel";

// ── Tab definition ───────────────────────────────────────────────────────────

type TabId = "compare" | "preview" | "scorecard" | "explanations" | "diff" | "qa";

// "fullbleed" tabs get zero padding and exact-height iframes; "scrollable" tabs get normal padding
const TABS: { id: TabId; label: string; icon: React.ReactNode; fullbleed: boolean }[] = [
  { id: "compare",      label: "Compare",    icon: <SlidersHorizontal className="w-3.5 h-3.5" />, fullbleed: true  },
  { id: "preview",      label: "Preview",    icon: <LayoutGrid className="w-3.5 h-3.5" />,        fullbleed: true  },
  { id: "scorecard",    label: "CRO Score",  icon: <BarChart3 className="w-3.5 h-3.5" />,         fullbleed: false },
  { id: "explanations", label: "Changes",    icon: <FileText className="w-3.5 h-3.5" />,           fullbleed: false },
  { id: "diff",         label: "Patch Ops",  icon: <Code2 className="w-3.5 h-3.5" />,              fullbleed: false },
  { id: "qa",           label: "QA Report",  icon: <ShieldCheck className="w-3.5 h-3.5" />,        fullbleed: false },
];

// ── Status pill ──────────────────────────────────────────────────────────────

function StatusPill({ status, runStatus }: { status: string; runStatus?: string }) {
  if (status === "complete" && runStatus) {
    const color =
      runStatus === "completed"               ? "text-[#D4FF26] border-[#D4FF26]/30" :
      runStatus === "completed_with_warnings" ? "text-amber-400 border-amber-700/40" :
                                                "text-red-400 border-red-900/40";
    return (
      <span className={`font-mono text-[9px] uppercase tracking-widest border px-2 py-1 ${color}`}>
        {runStatus.replace(/_/g, " ")}
      </span>
    );
  }
  const cfg: Record<string, string> = {
    idle:    "text-[#444] border-[#1a1a1a]",
    running: "text-[#D4FF26] border-[#D4FF26]/30",
    error:   "text-red-400 border-red-900/40",
  };
  return (
    <div className={`flex items-center gap-2 border px-2 py-1 ${cfg[status] ?? cfg.idle}`}>
      {status === "running" && (
        <span className="relative flex h-1.5 w-1.5 shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#D4FF26] opacity-60" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#D4FF26]" />
        </span>
      )}
      <span className="font-mono text-[9px] tracking-widest uppercase">{status}</span>
    </div>
  );
}

// ── Compact log line ─────────────────────────────────────────────────────────

function LogStream({ logs }: { logs: ReturnType<typeof useSSE>["logs"] }) {
  return (
    <div className="flex flex-col gap-1.5 font-mono text-[10px]">
      {logs.length === 0 && (
        <p className="text-[#2a2a2a] animate-pulse">Awaiting stream...</p>
      )}
      {[...logs].reverse().slice(0, 40).map((log) => {
        const color =
          log.type === "error"    ? "text-red-500/80" :
          log.type === "complete" ? "text-[#D4FF26]/80" :
          log.type === "start"    ? "text-white/70" :
                                    "text-[#3a3a3a]";
        const prefix =
          log.type === "start"    ? "▶" :
          log.type === "complete" ? "✓" :
          log.type === "error"    ? "✕" :
                                    "·";
        return (
          <div key={log.id} className="flex gap-2 leading-snug items-start">
            <span className="text-[#2a2a2a] shrink-0">{prefix}</span>
            <span className={`${color} flex-1 leading-snug`}>{log.message}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

// Header height + tab bar height — used for exact iframe sizing
const HEADER_H = 56;
const TABBAR_H = 44;

export default function RunDashboard({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { status, stages, stageOrder, logs, finalResult, errorMessage } = useSSE(id);

  const [activeTab, setActiveTab]     = useState<TabId>("compare");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const isRunning     = status === "idle" || status === "running";
  const activeTabMeta = TABS.find((t) => t.id === activeTab)!;

  // Backend URLs — served directly (no Next.js proxy)
  const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8080";

  const originalHtmlUrl  = finalResult ? `${BACKEND}${finalResult.original_html_url}` : "";
  const variantHtmlUrl   = finalResult ? `${BACKEND}${finalResult.modified_html_url}` : "";
  const originalSsUrl    = finalResult ? `${BACKEND}${finalResult.original_screenshot_url}` : "";
  const modifiedSsUrl    = finalResult ? `${BACKEND}${finalResult.modified_screenshot_url}` : "";

  const handleTabChange = useCallback((tabId: TabId) => {
    setActiveTab(tabId);
    // Auto-collapse sidebar when switching to a fullbleed tab for more space
    if (TABS.find((t) => t.id === tabId)?.fullbleed) {
      setSidebarOpen(false);
    } else {
      setSidebarOpen(true);
    }
  }, []);

  // Height available for fullbleed content below the tab bar
  const fullbleedH = `calc(100vh - ${HEADER_H}px - ${TABBAR_H}px)`;

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0a] text-white overflow-hidden">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header
        className="flex items-center justify-between px-5 shrink-0 border-b border-[#1a1a1a] z-30 bg-[#0a0a0a]"
        style={{ height: HEADER_H }}
      >
        <div className="flex items-center gap-4">
          <Link href="/" className="text-[#333] hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <span className="h-4 w-[1px] bg-[#1a1a1a]" />
          <h2 className="font-heading italic text-lg tracking-wide">RetroFit.</h2>
          <span className="h-4 w-[1px] bg-[#1a1a1a]" />
          <span className="font-mono text-[9px] text-[#2a2a2a] tracking-widest hidden sm:block">
            {id.slice(0, 8)}···{id.slice(-4)}
          </span>
        </div>
        <StatusPill status={status} runStatus={finalResult?.status} />
      </header>

      {/* ── Body ───────────────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── SIDEBAR ──────────────────────────────────────────────────────── */}
        <AnimatePresence initial={false}>
          {sidebarOpen && (
            <motion.aside
              key="sidebar"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 264, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col border-r border-[#1a1a1a] overflow-hidden shrink-0"
            >
              {/* Metrics (shown when done) */}
              {finalResult && (
                <div className="grid grid-cols-2 border-b border-[#1a1a1a] shrink-0">
                  <div className="flex flex-col p-4 border-r border-[#1a1a1a]">
                    <span className="font-mono text-[8px] uppercase tracking-widest text-[#333] mb-1">Lift</span>
                    <span className="font-heading text-2xl text-[#D4FF26]">+{finalResult.predicted_lift_range}</span>
                  </div>
                  <div className="flex flex-col p-4">
                    <span className="font-mono text-[8px] uppercase tracking-widest text-[#333] mb-1">Patches</span>
                    <span className="font-heading text-2xl">{finalResult.patch_spec.operations.length}</span>
                  </div>
                </div>
              )}

              {/* Pipeline stages */}
              <div className="flex-1 overflow-y-auto p-4" style={{ scrollbarWidth: "none" }}>
                <span className="font-mono text-[8px] uppercase tracking-widest text-[#2a2a2a] block mb-3">
                  Pipeline
                </span>
                <PipelineTimeline stages={stages} stageOrder={stageOrder} />
              </div>

              {/* Log stream */}
              <div className="border-t border-[#1a1a1a] p-3 overflow-y-auto" style={{ maxHeight: 180, scrollbarWidth: "none" }}>
                <span className="font-mono text-[8px] uppercase tracking-widest text-[#2a2a2a] block mb-2">Stream</span>
                <LogStream logs={logs} />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* ── MAIN PANEL ────────────────────────────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">

          {/* ── RUNNING STATE ─────────────────────────────────────────────── */}
          <AnimatePresence mode="wait">
            {isRunning && !errorMessage && (
              <motion.div
                key="running"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center gap-8 p-10"
              >
                <div className="relative w-20 h-20">
                  <motion.div
                    className="absolute inset-0 border border-[#D4FF26]/20 rotate-45"
                    animate={{ rotate: [45, 90, 45], scale: [1, 1.05, 1] }}
                    transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                  />
                  <motion.div
                    className="absolute inset-5 border border-[#D4FF26]/40 rotate-45"
                    animate={{ rotate: [45, 0, 45], scale: [1, 1.1, 1] }}
                    transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut", delay: 0.3 }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <motion.div
                      className="w-2.5 h-2.5 bg-[#D4FF26] rotate-45"
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                    />
                  </div>
                </div>

                <div className="text-center max-w-sm">
                  <h1 className="font-heading text-2xl mb-2">Processing Pipeline</h1>
                  <p className="font-body text-sm text-[#444] leading-relaxed">
                    {(() => {
                      const running = stageOrder.find((sid) => stages[sid].status === "running");
                      return running ? STAGE_META[running].description : "Initializing agents...";
                    })()}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-48 h-[1px] bg-[#1a1a1a] relative">
                    <motion.div
                      className="absolute left-0 top-0 h-full bg-[#D4FF26]"
                      style={{
                        width: `${(stageOrder.filter((sid) => stages[sid].status === "complete").length / stageOrder.length) * 100}%`,
                      }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                  <span className="font-mono text-[9px] text-[#2a2a2a]">
                    {stageOrder.filter((sid) => stages[sid].status === "complete").length}/{stageOrder.length}
                  </span>
                </div>
              </motion.div>
            )}

            {/* ── ERROR STATE ─────────────────────────────────────────────── */}
            {status === "error" && (
              <motion.div
                key="error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-1 flex flex-col items-center justify-center gap-5 p-10"
              >
                <div className="w-12 h-12 border border-red-900/40 flex items-center justify-center text-red-500 text-xl">
                  ✕
                </div>
                <h1 className="font-heading text-xl text-red-400">Pipeline Error</h1>
                <p className="font-mono text-xs text-[#444] max-w-md text-center bg-[#0d0d0d] border border-red-900/20 p-4 leading-relaxed">
                  {errorMessage || "Unknown error — check backend terminal."}
                </p>
                <Link
                  href="/"
                  className="font-mono text-[10px] uppercase tracking-widest text-[#444] hover:text-white border border-[#222] hover:border-[#444] px-4 py-2 transition-all"
                >
                  ← New run
                </Link>
              </motion.div>
            )}

            {/* ── RESULTS STATE ───────────────────────────────────────────── */}
            {status === "complete" && finalResult && (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-1 flex flex-col overflow-hidden"
              >
                {/* ── Tab bar ─────────────────────────────────────────────── */}
                <div
                  className="flex items-center border-b border-[#1a1a1a] shrink-0 bg-[#0a0a0a]"
                  style={{ height: TABBAR_H }}
                >
                  {/* Sidebar toggle */}
                  <button
                    onClick={() => setSidebarOpen((v) => !v)}
                    className="flex items-center justify-center w-10 h-full border-r border-[#1a1a1a] text-[#2a2a2a] hover:text-white transition-colors shrink-0"
                    title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
                  >
                    {sidebarOpen
                      ? <PanelLeftClose className="w-4 h-4" />
                      : <PanelLeftOpen  className="w-4 h-4" />
                    }
                  </button>

                  {/* Tabs */}
                  <div className="flex flex-1 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
                    {TABS.map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => handleTabChange(tab.id)}
                        className={`flex items-center gap-2 px-4 h-full font-mono text-[10px] uppercase tracking-widest whitespace-nowrap transition-all duration-200 border-b-2 shrink-0 ${
                          activeTab === tab.id
                            ? "border-[#D4FF26] text-white"
                            : "border-transparent text-[#333] hover:text-[#666]"
                        }`}
                      >
                        {tab.icon}
                        <span className="hidden sm:inline">{tab.label}</span>
                      </button>
                    ))}
                  </div>

                  {/* Quick-open links for preview tabs */}
                  {(activeTab === "compare" || activeTab === "preview") && (
                    <div className="flex items-center gap-1 px-3 border-l border-[#1a1a1a] shrink-0">
                      <a
                        href={originalHtmlUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-[9px] text-[#333] hover:text-[#D4FF26] flex items-center gap-1 px-2 py-1 border border-[#1a1a1a] hover:border-[#D4FF26]/30 transition-colors"
                        title="Open original in new tab"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span className="hidden lg:inline">Original</span>
                      </a>
                      <a
                        href={variantHtmlUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-[9px] text-[#D4FF26]/60 hover:text-[#D4FF26] flex items-center gap-1 px-2 py-1 border border-[#D4FF26]/20 hover:border-[#D4FF26]/50 transition-colors"
                        title="Open optimized in new tab"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span className="hidden lg:inline">Optimized</span>
                      </a>
                    </div>
                  )}
                </div>

                {/* ── Tab content ─────────────────────────────────────────── */}
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="flex-1 overflow-hidden"
                    style={activeTabMeta.fullbleed ? { height: fullbleedH } : { overflowY: "auto" }}
                  >
                    {activeTab === "compare" && (
                      <BeforeAfterSlider
                        originalScreenshotUrl={originalSsUrl}
                        modifiedScreenshotUrl={modifiedSsUrl}
                        fillParent
                      />
                    )}
                    {activeTab === "preview" && (
                      <PagePreview
                        originalHtmlUrl={originalHtmlUrl}
                        modifiedHtmlUrl={variantHtmlUrl}
                      />
                    )}
                    {activeTab === "scorecard" && (
                      <div className="p-6">
                        <CROScorecard
                          croFindings={finalResult.cro_findings}
                          scoreBefore={finalResult.cro_score_before}
                          scoreAfter={finalResult.cro_score_after}
                          liftRange={finalResult.predicted_lift_range}
                        />
                      </div>
                    )}
                    {activeTab === "explanations" && (
                      <div className="p-6">
                        <ExplanationPanel explanations={finalResult.explanations} />
                      </div>
                    )}
                    {activeTab === "diff" && (
                      <div className="p-6">
                        <PatchDiffViewer patchSpec={finalResult.patch_spec} />
                      </div>
                    )}
                    {activeTab === "qa" && (
                      <div className="p-6">
                        <QAReportPanel qaReport={finalResult.qa_report} />
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
