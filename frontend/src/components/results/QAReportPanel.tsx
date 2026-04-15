"use client";

import { motion } from "framer-motion";
import type { QAReport } from "@/lib/types";
import { CheckCircle, XCircle, AlertTriangle, ShieldCheck } from "lucide-react";

interface QAReportPanelProps {
  qaReport: QAReport;
}

function CheckRow({ label, passed }: { label: string; passed: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[#111]">
      <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">{label}</span>
      {passed
        ? <CheckCircle className="w-4 h-4 text-[#D4FF26]" />
        : <XCircle className="w-4 h-4 text-red-500" />
      }
    </div>
  );
}

export function QAReportPanel({ qaReport }: QAReportPanelProps) {
  const passedAll = qaReport.passed;

  return (
    <div className="flex flex-col gap-6">
      {/* Overall status banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`border p-5 flex items-center gap-4 ${
          passedAll
            ? "border-[#D4FF26]/30 bg-[#D4FF26]/5"
            : "border-red-900/40 bg-red-950/20"
        }`}
      >
        {passedAll
          ? <ShieldCheck className="w-8 h-8 text-[#D4FF26] shrink-0" />
          : <AlertTriangle className="w-8 h-8 text-red-500 shrink-0" />
        }
        <div>
          <h3 className={`font-heading text-xl ${passedAll ? "text-[#D4FF26]" : "text-red-400"}`}>
            {passedAll ? "QA Passed" : "QA Passed with Warnings"}
          </h3>
          <p className="font-mono text-[10px] text-[#555] mt-0.5 uppercase tracking-widest">
            Variant: {qaReport.variant_id} · {qaReport.grounded_change_count} grounded changes
          </p>
        </div>
      </motion.div>

      {/* Checks grid */}
      <div className="border border-[#1a1a1a] p-4 flex flex-col">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[#555] mb-3">Validation Checks</span>
        <CheckRow label="Valid HTML structure" passed={qaReport.is_valid_html} />
        <CheckRow label="Key elements present" passed={qaReport.key_elements_present} />
        <CheckRow label="No hallucinations" passed={qaReport.hallucination_flags.length === 0} />
        <CheckRow label="Visual diff within threshold" passed={
          qaReport.visual_diff_score === null || qaReport.visual_diff_score < 0.5
        } />
      </div>

      {/* Visual diff score */}
      {qaReport.visual_diff_score !== null && (
        <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555] block mb-2">Visual Diff Score</span>
          <div className="flex items-center gap-4">
            <div className="flex-1 h-1.5 bg-[#1a1a1a]">
              <motion.div
                className="h-full"
                style={{ backgroundColor: qaReport.visual_diff_score < 0.3 ? "#D4FF26" : qaReport.visual_diff_score < 0.5 ? "#f59e0b" : "#ef4444" }}
                initial={{ width: 0 }}
                animate={{ width: `${qaReport.visual_diff_score * 100}%` }}
                transition={{ duration: 0.8 }}
              />
            </div>
            <span className="font-mono text-xs text-[#777] shrink-0">
              {(qaReport.visual_diff_score * 100).toFixed(1)}% pixel diff
            </span>
          </div>
          <p className="font-mono text-[9px] text-[#333] mt-1">Threshold: &lt;50% — changes should be surgical, not full redesigns</p>
        </div>
      )}

      {/* Structural issues */}
      {qaReport.structural_issues.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">Structural Issues</span>
          {qaReport.structural_issues.map((issue, i) => (
            <div
              key={i}
              className="border-l-2 pl-3 py-1"
              style={{ borderColor: issue.severity === "critical" ? "#ef4444" : "#f59e0b" }}
            >
              <div className="flex items-center gap-2">
                <span className="font-mono text-[9px] uppercase" style={{ color: issue.severity === "critical" ? "#ef4444" : "#f59e0b" }}>
                  {issue.severity}
                </span>
                <code className="font-mono text-[9px] text-[#444]">{issue.code}</code>
              </div>
              <p className="font-body text-xs text-[#666] mt-0.5">{issue.message}</p>
              {issue.selector && <code className="font-mono text-[9px] text-[#333]">{issue.selector}</code>}
            </div>
          ))}
        </div>
      )}

      {/* Hallucination flags */}
      {qaReport.hallucination_flags.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">Hallucination Flags</span>
          {qaReport.hallucination_flags.map((flag, i) => (
            <div key={i} className="border border-red-900/30 bg-red-950/10 p-3">
              <div className="flex items-center gap-2 mb-1">
                <XCircle className="w-3 h-3 text-red-500 shrink-0" />
                <code className="font-mono text-[9px] text-red-400">{flag.code}</code>
              </div>
              <p className="font-body text-xs text-[#666]">{flag.message}</p>
              <code className="font-mono text-[9px] text-red-600/70 mt-1 block">"{flag.offending_text}"</code>
            </div>
          ))}
        </div>
      )}

      {/* Failure reasons */}
      {qaReport.failure_reasons.length > 0 && (
        <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555] block mb-2">Failure Reasons</span>
          {qaReport.failure_reasons.map((reason, i) => (
            <p key={i} className="font-mono text-[10px] text-[#666] leading-relaxed py-0.5">{reason}</p>
          ))}
        </div>
      )}
    </div>
  );
}
