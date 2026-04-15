"use client";

import { useState } from "react";

interface PagePreviewProps {
  originalHtmlUrl: string;
  modifiedHtmlUrl: string;
}

type Pane = "original" | "split" | "optimized";

const PANES: { id: Pane; label: string }[] = [
  { id: "original",  label: "Original"  },
  { id: "split",     label: "Split"     },
  { id: "optimized", label: "Optimized" },
];

function IframePane({
  src,
  label,
  accent,
}: {
  src: string;
  label: string;
  accent?: boolean;
}) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden min-w-0">
      {/* Pane header */}
      <div
        className="flex items-center px-4 h-8 shrink-0 border-b"
        style={{
          borderColor: accent ? "rgba(212,255,38,0.2)" : "#1a1a1a",
          backgroundColor: accent ? "rgba(212,255,38,0.04)" : "#0a0a0a",
        }}
      >
        <span
          className="font-mono text-[9px] uppercase tracking-widest"
          style={{ color: accent ? "#D4FF26" : "#333" }}
        >
          {label}
        </span>
      </div>

      {/* The iframe — width is 100% of pane, height fills remaining space */}
      <iframe
        src={src}
        title={label}
        className="flex-1 border-none block w-full bg-white"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        loading="lazy"
        style={{
          // Force the iframe to pretend it's a full desktop viewport
          minWidth: "100%",
        }}
      />
    </div>
  );
}

export function PagePreview({ originalHtmlUrl, modifiedHtmlUrl }: PagePreviewProps) {
  const [active, setActive] = useState<Pane>("split");

  return (
    <div className="flex flex-col h-full">
      {/* Mode selector bar */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[#1a1a1a] bg-[#0a0a0a] shrink-0">
        {PANES.map((p) => (
          <button
            key={p.id}
            onClick={() => setActive(p.id)}
            className={`font-mono text-[9px] uppercase tracking-widest px-3 py-1 transition-all duration-200 ${
              active === p.id
                ? "bg-[#D4FF26] text-black font-bold"
                : "text-[#333] border border-[#1a1a1a] hover:text-white hover:border-[#333]"
            }`}
          >
            {p.label}
          </button>
        ))}

        {/* Tip */}
        <span className="ml-auto font-mono text-[9px] text-[#222]">
          JS/CSS from the original site is sandboxed
        </span>
      </div>

      {/* Iframe(s) — fill all remaining height */}
      <div className="flex flex-1 overflow-hidden">
        {(active === "original" || active === "split") && (
          <IframePane src={originalHtmlUrl} label="Original" />
        )}

        {active === "split" && (
          <div className="w-[1px] bg-[#1a1a1a] shrink-0" />
        )}

        {(active === "optimized" || active === "split") && (
          <IframePane src={modifiedHtmlUrl} label="Optimized" accent />
        )}
      </div>
    </div>
  );
}
