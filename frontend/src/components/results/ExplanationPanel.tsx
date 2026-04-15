"use client";

import { motion } from "framer-motion";
import type { ExplanationItem } from "@/lib/types";

interface ExplanationPanelProps {
  explanations: ExplanationItem[];
}

const CRO_PRINCIPLE_COLORS: Record<string, string> = {
  message_match:    "#D4FF26",
  hero_clarity:     "#60a5fa",
  cta_visibility:   "#f59e0b",
  social_proof:     "#a78bfa",
  urgency_scarcity: "#ef4444",
  trust_signals:    "#34d399",
  mobile_readiness: "#fb923c",
};

const CHANGE_TYPE_COLORS: Record<string, string> = {
  copy:      "#D4FF26",
  style:     "#60a5fa",
  structure: "#f59e0b",
};

function PrincipleBadge({ id }: { id: string }) {
  const color = CRO_PRINCIPLE_COLORS[id] || "#555";
  return (
    <span
      className="font-mono text-[8px] uppercase tracking-widest px-2 py-0.5 border"
      style={{ color, borderColor: `${color}40`, backgroundColor: `${color}10` }}
    >
      {id.replace(/_/g, " ")}
    </span>
  );
}

function ExplanationCard({ item, index }: { item: ExplanationItem; index: number }) {
  const typeColor = CHANGE_TYPE_COLORS[item.change_type] || "#555";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.3 }}
      className="border border-[#1a1a1a] bg-[#0d0d0d] p-5 flex flex-col gap-3"
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[8px] uppercase px-2 py-0.5 border" style={{ color: typeColor, borderColor: `${typeColor}40` }}>
            {item.change_type}
          </span>
          <code className="font-mono text-[9px] text-[#444] truncate max-w-[180px]">
            {item.element_selector}
          </code>
        </div>
        <span className="font-mono text-[9px] text-[#333]">#{item.change_id}</span>
      </div>

      {/* Copy diff */}
      {(item.original_text || item.new_text) && (
        <div className="flex flex-col gap-1">
          {item.original_text && (
            <div className="flex gap-2 items-start">
              <span className="font-mono text-[9px] text-red-500 w-3 shrink-0 mt-0.5">−</span>
              <span className="font-body text-xs text-[#555] line-through leading-snug">{item.original_text}</span>
            </div>
          )}
          {item.new_text && (
            <div className="flex gap-2 items-start">
              <span className="font-mono text-[9px] text-[#D4FF26] w-3 shrink-0 mt-0.5">+</span>
              <span className="font-body text-xs text-[#ccc] leading-snug">{item.new_text}</span>
            </div>
          )}
        </div>
      )}

      {/* Rationale */}
      <p className="font-body text-xs text-[#555] leading-relaxed">{item.rationale}</p>

      {/* CRO principle badges */}
      {item.cro_principles.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {item.cro_principles.map((p) => (
            <PrincipleBadge key={p} id={p} />
          ))}
        </div>
      )}
    </motion.div>
  );
}

export function ExplanationPanel({ explanations }: ExplanationPanelProps) {
  if (explanations.length === 0) {
    return (
      <div className="flex items-center justify-center h-40">
        <p className="font-mono text-[10px] text-[#444] uppercase tracking-widest">No explanations available</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">
          {explanations.length} Change{explanations.length !== 1 ? "s" : ""} Applied
        </span>
        <div className="flex gap-3">
          {Object.entries(CHANGE_TYPE_COLORS).map(([type, color]) => (
            <span key={type} className="font-mono text-[9px] uppercase flex items-center gap-1.5" style={{ color }}>
              <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ backgroundColor: color }} />
              {type}
            </span>
          ))}
        </div>
      </div>

      {explanations.map((item, i) => (
        <ExplanationCard key={item.change_id} item={item} index={i} />
      ))}
    </div>
  );
}
