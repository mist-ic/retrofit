"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { CROFindings, CriterionScore } from "@/lib/types";

interface CROScorecardProps {
  croFindings: CROFindings;
  scoreBefore: number;
  scoreAfter: number;
  liftRange: string;
}

const CRITERION_LABELS: Record<string, string> = {
  message_match: "Message Match",
  hero_clarity: "Hero Clarity",
  cta_visibility: "CTA Visibility",
  social_proof: "Social Proof",
  urgency_scarcity: "Urgency & Scarcity",
  trust_signals: "Trust Signals",
  mobile_readiness: "Mobile Readiness",
};

function ScoreGauge({ value, before }: { value: number; before: number }) {
  const radius = 52;
  const stroke = 6;
  const norm = radius - stroke / 2;
  const circ = 2 * Math.PI * norm;
  const afterDash = (value / 100) * circ;
  const beforeDash = (before / 100) * circ;
  const color = value >= 75 ? "#D4FF26" : value >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center w-32 h-32">
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90" fill="none">
        {/* Track */}
        <circle cx="60" cy="60" r={norm} stroke="#1a1a1a" strokeWidth={stroke} />
        {/* Before (dim) */}
        <motion.circle
          cx="60" cy="60" r={norm}
          stroke="#333333" strokeWidth={stroke}
          strokeDasharray={`${beforeDash} ${circ}`}
          strokeLinecap="round"
        />
        {/* After */}
        <motion.circle
          cx="60" cy="60" r={norm}
          stroke={color} strokeWidth={stroke}
          strokeDasharray={`${afterDash} ${circ}`}
          strokeLinecap="round"
          initial={{ strokeDasharray: `0 ${circ}` }}
          animate={{ strokeDasharray: `${afterDash} ${circ}` }}
          transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <motion.span
          className="font-heading text-3xl font-medium text-white"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {Math.round(value)}
        </motion.span>
        <span className="font-mono text-[9px] uppercase tracking-widest text-[#555]">/100</span>
      </div>
    </div>
  );
}

function CriterionBar({ criterion }: { criterion: CriterionScore }) {
  const label = CRITERION_LABELS[criterion.criterion_id] || criterion.label;
  const pct = criterion.score;
  const barColor = pct >= 75 ? "#D4FF26" : pct >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="group cursor-default">
      <div className="flex justify-between items-center mb-1">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[#777]">{label}</span>
        <span className="font-mono text-[10px]" style={{ color: barColor }}>{Math.round(pct)}</span>
      </div>
      <div className="h-1 bg-[#1a1a1a] w-full">
        <motion.div
          className="h-full"
          style={{ backgroundColor: barColor }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
        />
      </div>
      {/* Rationale tooltip on hover */}
      <AnimatePresence>
        <motion.p className="text-[10px] text-[#444] mt-1 leading-snug hidden group-hover:block">
          {criterion.rationale}
        </motion.p>
      </AnimatePresence>
    </div>
  );
}

export function CROScorecard({ croFindings, scoreBefore, scoreAfter, liftRange }: CROScorecardProps) {
  const delta = scoreAfter - scoreBefore;

  return (
    <div className="flex flex-col gap-8">
      {/* Score header */}
      <div className="flex flex-col sm:flex-row items-center gap-8 border border-[#222] bg-[#111111] p-6">
        <div className="flex flex-col items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">Before</span>
          <span className="font-heading text-4xl text-[#555]">{Math.round(scoreBefore)}</span>
        </div>

        <div className="flex flex-col items-center gap-1 flex-1">
          <ScoreGauge value={scoreAfter} before={scoreBefore} />
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">CRO Score After</span>
        </div>

        <div className="flex flex-col items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">Est. Lift</span>
          <span className="font-heading text-2xl text-[#D4FF26]">+{liftRange}</span>
          {delta > 0 && (
            <span className="font-mono text-[9px] text-[#555]">Δ +{delta.toFixed(0)} pts</span>
          )}
        </div>
      </div>

      {/* Criteria bars */}
      <div className="flex flex-col gap-4">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[#555] border-b border-[#1a1a1a] pb-2">
          Criterion Breakdown
        </span>
        {croFindings.criteria.map((c) => (
          <CriterionBar key={c.criterion_id} criterion={c} />
        ))}
      </div>

      {/* Top issues */}
      {croFindings.top_issues.length > 0 && (
        <div className="flex flex-col gap-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555] border-b border-[#1a1a1a] pb-2">
            Key Issues Found
          </span>
          {croFindings.top_issues.slice(0, 4).map((issue) => (
            <div
              key={issue.issue_id}
              className="border-l-2 pl-3 py-1"
              style={{ borderColor: issue.severity === "critical" ? "#ef4444" : issue.severity === "high" ? "#f59e0b" : "#555" }}
            >
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-mono text-[9px] uppercase" style={{ color: issue.severity === "critical" ? "#ef4444" : "#f59e0b" }}>
                  {issue.severity}
                </span>
                <span className="font-mono text-[9px] text-[#444]">{issue.criterion_id.replace(/_/g, " ")}</span>
              </div>
              <p className="font-body text-xs text-[#777]">{issue.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4">
        <p className="font-body text-sm text-[#666] leading-relaxed italic">{croFindings.summary}</p>
      </div>
    </div>
  );
}
