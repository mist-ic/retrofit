'use client';

interface PagePreviewProps {
  originalUrl: string;
  modifiedUrl: string;
}

export function PagePreview({ originalUrl, modifiedUrl }: PagePreviewProps) {
  return (
    <div className="grid grid-cols-2 gap-3 h-[600px]">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <span className="badge badge-red text-xs">Original</span>
        </div>
        <iframe
          src={originalUrl}
          className="flex-1 w-full rounded-xl border border-[var(--border)] bg-white"
          sandbox="allow-scripts allow-same-origin"
          title="Original landing page"
        />
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <span className="badge badge-emerald text-xs">Optimized</span>
        </div>
        <iframe
          src={modifiedUrl}
          className="flex-1 w-full rounded-xl border border-cyan-500/20 bg-white"
          sandbox="allow-scripts allow-same-origin"
          title="Optimized landing page"
        />
      </div>
    </div>
  );
}
