"use client";

import { motion } from "framer-motion";
import type { StageId, StageState, StageStatus } from "@/lib/types";
import { STAGE_META } from "@/hooks/useSSE";
import { CheckCircle, Circle, AlertCircle, Loader2 } from "lucide-react";

interface PipelineTimelineProps {
  stages: Record<StageId, StageState>;
  stageOrder: StageId[];
}

const statusConfig: Record<StageStatus, {
  icon: (className: string) => React.ReactNode;
  dotClass: string;
  labelClass: string;
}> = {
  pending: {
    icon: (c) => <Circle className={c} />,
    dotClass: "border border-[#333333] bg-[#111111]",
    labelClass: "text-[#444444]",
  },
  running: {
    icon: (c) => <Loader2 className={`${c} animate-spin`} />,
    dotClass: "bg-[#D4FF26] shadow-[0_0_12px_rgba(212,255,38,0.7)]",
    labelClass: "text-white",
  },
  complete: {
    icon: (c) => <CheckCircle className={c} />,
    dotClass: "bg-[#D4FF26]",
    labelClass: "text-[#D4FF26]",
  },
  error: {
    icon: (c) => <AlertCircle className={c} />,
    dotClass: "bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]",
    labelClass: "text-red-400",
  },
};

function ElapsedTimer({ startedAt, completedAt }: { startedAt?: number; completedAt?: number }) {
  if (!startedAt) return null;
  const ms = (completedAt ?? Date.now()) - startedAt;
  const s = (ms / 1000).toFixed(1);
  return (
    <span className="font-mono text-[9px] text-[#555555]">{s}s</span>
  );
}

function StageRow({
  stage,
  isLast,
  index,
}: {
  stage: StageState;
  isLast: boolean;
  index: number;
}) {
  const meta = STAGE_META[stage.id];
  const cfg = statusConfig[stage.status];

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      className="flex gap-4 relative"
    >
      {/* Vertical connector line */}
      {!isLast && (
        <div
          className={`absolute left-[9px] top-[22px] bottom-0 w-[1px] transition-colors duration-700 ${
            stage.status === "complete" ? "bg-[#D4FF26]/40" : "bg-[#222222]"
          }`}
          style={{ height: "calc(100% + 16px)" }}
        />
      )}

      {/* Status dot */}
      <div className="relative mt-1 shrink-0">
        <motion.div
          className={`w-5 h-5 rounded-full flex items-center justify-center ${cfg.dotClass} transition-all duration-500`}
          animate={stage.status === "running" ? { scale: [1, 1.15, 1] } : {}}
          transition={{ repeat: Infinity, duration: 1.2 }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 pb-5 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className={`font-mono text-[11px] uppercase tracking-widest font-medium transition-colors duration-300 ${cfg.labelClass}`}>
            {meta.label}
          </span>
          <ElapsedTimer startedAt={stage.startedAt} completedAt={stage.completedAt} />
        </div>

        <p className="font-body text-[11px] text-[#555555] leading-snug">
          {stage.status === "pending" ? meta.description : stage.message || meta.description}
        </p>

        {/* Stage data badges (shown on complete) */}
        {stage.status === "complete" && stage.data && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-2 flex flex-wrap gap-2"
          >
            {Object.entries(stage.data).slice(0, 3).map(([k, v]) => {
              if (v === null || v === undefined || v === false) return null;
              return (
                <span key={k} className="font-mono text-[9px] bg-[#1a1a1a] border border-[#2a2a2a] px-2 py-0.5 text-[#777]">
                  {k.replace(/_/g, " ")}: {String(v)}
                </span>
              );
            })}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

export function PipelineTimeline({ stages, stageOrder }: PipelineTimelineProps) {
  return (
    <div className="py-4">
      {stageOrder.map((id, i) => (
        <StageRow
          key={id}
          stage={stages[id]}
          isLast={i === stageOrder.length - 1}
          index={i}
        />
      ))}
    </div>
  );
}
