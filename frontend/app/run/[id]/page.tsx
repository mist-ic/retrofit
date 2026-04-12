'use client';

import { use } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { usePipelineRun } from '@/hooks/usePipelineRun';
import { Navbar } from '@/components/layout/Navbar';
import { PipelineTimeline } from '@/components/pipeline/PipelineTimeline';
import { StreamingLog } from '@/components/pipeline/StreamingLog';
import { CROScorecard } from '@/components/results/CROScorecard';
import { ExplanationPanel } from '@/components/results/ExplanationPanel';
import { BeforeAfterSlider } from '@/components/results/BeforeAfterSlider';
import { PagePreview } from '@/components/results/PagePreview';
import { AuditReport } from '@/components/results/AuditReport';
import { getPreviewUrl } from '@/lib/api';
import { cn } from '@/lib/utils';

type Tab = 'comparison' | 'preview' | 'audit' | 'explanations' | 'scorecard';

const TABS: { id: Tab; label: string }[] = [
  { id: 'comparison', label: 'Before / After' },
  { id: 'scorecard', label: 'CRO Score' },
  { id: 'explanations', label: 'Changes' },
  { id: 'preview', label: 'Live Preview' },
  { id: 'audit', label: 'QA Report' },
];

export default function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: runId } = use(params);
  const { stages, result, liveMessages, isConnected, isDone, error } = usePipelineRun(runId);
  const [activeTab, setActiveTab] = useState<Tab>('comparison');

  const isRunning = !isDone;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 space-y-8">

        {/* ── Pipeline section ──────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left: timeline */}
          <div className="lg:col-span-1 space-y-4">
            <div className="glass rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-slate-300">Pipeline</h2>
                {isConnected && (
                  <span className="flex items-center gap-1.5 text-xs text-cyan-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    Running
                  </span>
                )}
                {isDone && !error && (
                  <span className="badge badge-emerald text-xs">Complete</span>
                )}
              </div>
              <PipelineTimeline stages={stages} />
            </div>
          </div>

          {/* Right: live log or result hero */}
          <div className="lg:col-span-2">
            <AnimatePresence mode="wait">
              {isRunning && (
                <motion.div
                  key="running"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="glass rounded-2xl p-5 space-y-4"
                >
                  <h2 className="text-sm font-semibold text-slate-300">Live Output</h2>
                  <StreamingLog events={liveMessages} />
                  <div className="flex items-center gap-3 pt-2">
                    <div className="flex-1 h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"
                        animate={{ x: ['-100%', '100%'] }}
                        transition={{ repeat: Infinity, duration: 1.8, ease: 'linear' }}
                        style={{ width: '40%' }}
                      />
                    </div>
                    <span className="text-xs text-slate-500">Analyzing...</span>
                  </div>
                </motion.div>
              )}

              {isDone && result && (
                <motion.div
                  key="result-hero"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass rounded-2xl p-6"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">Analysis complete</p>
                      <h2 className="text-2xl font-bold text-white">
                        CRO score{' '}
                        <span className="gradient-text">
                          {Math.round(result.cro_score_before)} → {Math.round(result.cro_score_after)}
                        </span>
                      </h2>
                      <p className="text-sm text-slate-400">{result.cro_findings.summary}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="badge badge-purple text-sm px-3 py-1">
                        Est. +{result.predicted_lift_range} CVR
                      </div>
                      <p className="text-xs text-slate-500 mt-2">
                        {result.patch_spec.operations.length} changes applied
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              {isDone && error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass rounded-2xl p-6 border border-red-500/20 bg-red-500/5"
                >
                  <h2 className="text-base font-semibold text-red-400 mb-2">Pipeline error</h2>
                  <p className="text-sm text-slate-400">{error}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

        </div>

        {/* ── Results tabs ──────────────────────────────────────────────────── */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Tab bar */}
            <div className="flex gap-1 p-1 rounded-xl bg-[var(--bg-surface)] border border-[var(--border)] w-fit">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                    activeTab === tab.id
                      ? 'bg-[var(--bg-hover)] text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                {activeTab === 'comparison' && (
                  <BeforeAfterSlider
                    originalUrl={result.original_screenshot_url}
                    modifiedUrl={result.modified_screenshot_url}
                  />
                )}

                {activeTab === 'scorecard' && (
                  <div className="glass rounded-2xl p-6">
                    <CROScorecard
                      findings={result.cro_findings}
                      scoreBefore={result.cro_score_before}
                      scoreAfter={result.cro_score_after}
                      liftRange={result.predicted_lift_range}
                    />
                  </div>
                )}

                {activeTab === 'explanations' && (
                  <ExplanationPanel explanations={result.explanations} />
                )}

                {activeTab === 'preview' && (
                  <PagePreview
                    originalUrl={getPreviewUrl(runId, 'original')}
                    modifiedUrl={getPreviewUrl(runId, 'variant')}
                  />
                )}

                {activeTab === 'audit' && (
                  <div className="glass rounded-2xl p-6">
                    <AuditReport report={result.qa_report} />
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </motion.div>
        )}

      </div>
    </div>
  );
}
