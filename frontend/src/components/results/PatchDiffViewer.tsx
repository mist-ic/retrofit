"use client";

import { useState } from "react";
import type { PatchSpec, PatchOperation } from "@/lib/types";

interface PatchDiffViewerProps {
  patchSpec: PatchSpec;
}

const OP_COLORS: Record<string, string> = {
  replaceText:      "#D4FF26",
  replaceAttribute: "#60a5fa",
  addClass:         "#34d399",
  removeClass:      "#f87171",
  insertBefore:     "#a78bfa",
  insertAfter:      "#fb923c",
  replaceStyle:     "#f59e0b",
};

function OpCard({ op, index }: { op: PatchOperation; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const color = OP_COLORS[op.op] || "#555";

  const getDetails = (operation: PatchOperation): React.ReactNode => {
    switch (operation.op) {
      case "replaceText":
        return (
          <div className="flex flex-col gap-2 mt-2">
            {operation.original_text && (
              <div className="bg-red-950/30 border border-red-900/30 p-2 rounded">
                <span className="font-mono text-[9px] text-red-500 block mb-1">BEFORE</span>
                <span className="font-body text-xs text-[#888]">{operation.original_text}</span>
              </div>
            )}
            <div className="bg-[#1a2200]/60 border border-[#D4FF26]/20 p-2 rounded">
              <span className="font-mono text-[9px] text-[#D4FF26] block mb-1">AFTER</span>
              <span className="font-body text-xs text-white">{operation.new_text}</span>
            </div>
          </div>
        );
      case "replaceAttribute":
        return (
          <div className="mt-2 bg-[#0d0d0d] border border-[#1a1a1a] p-2">
            <code className="font-mono text-[10px] text-[#777]">{operation.attribute}</code>
            <span className="font-mono text-[10px] text-[#333] mx-2">→</span>
            <code className="font-mono text-[10px] text-[#60a5fa]">{operation.new_value}</code>
          </div>
        );
      case "replaceStyle":
        return (
          <div className="mt-2 bg-[#0d0d0d] border border-[#1a1a1a] p-2">
            <code className="font-mono text-[10px] text-[#f59e0b] break-all">{operation.css_text}</code>
          </div>
        );
      case "insertBefore":
      case "insertAfter":
        return (
          <div className="mt-2 bg-[#0d0d0d] border border-[#1a1a1a] p-2 overflow-x-auto">
            <code className="font-mono text-[10px] text-[#a78bfa] whitespace-pre-wrap break-all">{operation.html}</code>
          </div>
        );
      case "addClass":
        return (
          <div className="mt-2">
            <span className="font-mono text-[10px] text-[#34d399]">+ .{operation.class_name}</span>
          </div>
        );
      case "removeClass":
        return (
          <div className="mt-2">
            <span className="font-mono text-[10px] text-[#f87171]">- .{operation.class_name}</span>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="border border-[#1a1a1a] bg-[#0d0d0d]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-[#111] transition-colors"
      >
        <span className="font-mono text-[8px] uppercase tracking-widest shrink-0 w-5 text-[#333]">
          {String(index + 1).padStart(2, "0")}
        </span>
        <span
          className="font-mono text-[9px] uppercase tracking-widest shrink-0 px-2 py-0.5 border"
          style={{ color, borderColor: `${color}40`, backgroundColor: `${color}08` }}
        >
          {op.op}
        </span>
        <code className="font-mono text-[10px] text-[#555] flex-1 min-w-0 truncate">
          {op.selector}
        </code>
        <span className="font-mono text-[10px] text-[#333] shrink-0">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-[#111]">
          {getDetails(op)}
        </div>
      )}
    </div>
  );
}

export function PatchDiffViewer({ patchSpec }: PatchDiffViewerProps) {
  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex flex-col gap-0.5">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#555]">
            {patchSpec.operations.length} Operations Applied
          </span>
          <p className="font-body text-xs text-[#444]">{patchSpec.description}</p>
        </div>
        <code className="font-mono text-[9px] text-[#333] border border-[#1a1a1a] px-2 py-1">
          {patchSpec.variant_id}
        </code>
      </div>

      {/* Op type legend */}
      <div className="flex flex-wrap gap-2 mb-2">
        {Object.entries(OP_COLORS).map(([op, color]) => (
          <span key={op} className="font-mono text-[9px] flex items-center gap-1" style={{ color }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
            {op}
          </span>
        ))}
      </div>

      {/* Operations list */}
      <div className="flex flex-col divide-y divide-[#111]">
        {patchSpec.operations.map((op, i) => (
          <OpCard key={i} op={op} index={i} />
        ))}
      </div>
    </div>
  );
}
