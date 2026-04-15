"use client";

import { useState } from "react";
import { ReactCompareSlider } from "react-compare-slider";

interface BeforeAfterSliderProps {
  originalScreenshotUrl: string;
  modifiedScreenshotUrl: string;
  originalHtmlUrl?: string;
  modifiedHtmlUrl?: string;
  fillParent?: boolean;
}

function DragHandle() {
  return (
    <div
      className="flex items-center h-full"
      style={{ pointerEvents: "none" }}
    >
      {/* Line */}
      <div className="absolute top-0 bottom-0 w-[2px] bg-[#D4FF26] shadow-[0_0_16px_rgba(212,255,38,0.5)]" />
      {/* Pill */}
      <div
        className="relative bg-[#D4FF26] text-black rounded-full shadow-xl flex items-center gap-2 px-3 py-1.5"
        style={{ pointerEvents: "all", cursor: "ew-resize" }}
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M6 1L2 5L6 9" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div className="w-[1px] h-3 bg-black/20" />
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M4 1L8 5L4 9" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
}

function ScreenshotFallback({
  originalHtmlUrl,
  modifiedHtmlUrl,
}: {
  originalHtmlUrl?: string;
  modifiedHtmlUrl?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 p-10 text-center">
      <div className="w-14 h-14 border border-[#222] flex items-center justify-center text-[#333] text-2xl">
        📸
      </div>
      <div>
        <h3 className="font-heading text-lg text-white/60 mb-2">Screenshots unavailable</h3>
        <p className="font-mono text-[11px] text-[#444] max-w-sm leading-relaxed">
          The compare slider requires full-page screenshots which may not be available
          for sites with anti-bot protection. Use the <strong className="text-[#D4FF26]">Preview</strong> tab
          for a live side-by-side comparison instead.
        </p>
      </div>
      {(originalHtmlUrl || modifiedHtmlUrl) && (
        <div className="flex gap-3 mt-2">
          {originalHtmlUrl && (
            <a
              href={originalHtmlUrl}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[11px] px-4 py-2 border border-[#333] text-[#888] hover:text-white hover:border-white/40 transition-all"
            >
              Open Original →
            </a>
          )}
          {modifiedHtmlUrl && (
            <a
              href={modifiedHtmlUrl}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[11px] px-4 py-2 border border-[#D4FF26]/40 text-[#D4FF26] hover:bg-[#D4FF26] hover:text-black transition-all"
            >
              Open Optimized →
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export function BeforeAfterSlider({
  originalScreenshotUrl,
  modifiedScreenshotUrl,
  originalHtmlUrl,
  modifiedHtmlUrl,
  fillParent,
}: BeforeAfterSliderProps) {
  const [imgError, setImgError] = useState(false);

  if (imgError) {
    return (
      <div className={`flex flex-col ${fillParent ? "h-full" : ""}`}>
        <ScreenshotFallback originalHtmlUrl={originalHtmlUrl} modifiedHtmlUrl={modifiedHtmlUrl} />
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${fillParent ? "h-full" : ""}`}>
      {/* Top label bar */}
      <div className="flex justify-between items-center px-4 py-2 border-b border-[#1a1a1a] bg-[#0a0a0a] shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#2a2a2a]" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#444]">Original</span>
        </div>
        <span className="font-mono text-[9px] text-[#2a2a2a]">← Drag to compare →</span>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-[#D4FF26]">Optimized</span>
          <span className="w-2 h-2 rounded-full bg-[#D4FF26]" />
        </div>
      </div>

      {/*
        Scrollable wrapper — the screenshots are full-page, potentially very tall.
        We show them at natural full-width (no cropping) in a vertically scrollable container.
        The ReactCompareSlider moves the divider horizontally; vertical scrolling is handled by the wrapper.
      */}
      <div
        className="flex-1 overflow-y-auto overflow-x-hidden"
        style={{ scrollbarWidth: "thin", scrollbarColor: "#2a2a2a #0a0a0a" }}
      >
        <ReactCompareSlider
          style={{ width: "100%", display: "block" }}
          handle={<DragHandle />}
          itemOne={
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={originalScreenshotUrl}
              alt="Original page"
              style={{ width: "100%", display: "block", verticalAlign: "top" }}
              draggable={false}
              onError={() => setImgError(true)}
            />
          }
          itemTwo={
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={modifiedScreenshotUrl}
              alt="Optimized page"
              style={{ width: "100%", display: "block", verticalAlign: "top" }}
              draggable={false}
              onError={() => setImgError(true)}
            />
          }
        />
      </div>
    </div>
  );
}
