'use client';

import { useCallback, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Link, X, ImageIcon } from 'lucide-react';
import { useAdUpload, AdInputMode } from '@/hooks/useAdUpload';
import { cn } from '@/lib/utils';

interface AdUploadStepProps {
  onComplete: (state: { file: File | null; url: string }) => void;
}

export function AdUploadStep({ onComplete }: AdUploadStepProps) {
  const { state, setMode, onFileSelect, onUrlChange, clear, hasInput } = useAdUpload();
  const dropRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleContinue = () => {
    onComplete({ file: state.file, url: state.url });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-1">Upload your ad creative</h2>
        <p className="text-sm text-slate-400">
          Drop an image or paste a URL — this is what drove traffic to the landing page.
        </p>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-1 p-1 rounded-lg bg-[var(--bg-elevated)] w-fit">
        {(['file', 'url'] as AdInputMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              'px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-150',
              state.mode === m
                ? 'bg-[var(--bg-hover)] text-white'
                : 'text-slate-400 hover:text-white'
            )}
          >
            {m === 'file' ? 'Upload file' : 'Image URL'}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {state.mode === 'file' ? (
          <motion.div
            key="file"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            {!state.preview ? (
              <div
                ref={dropRef}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  'relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200 py-16',
                  dragging
                    ? 'border-cyan-400 bg-cyan-500/5'
                    : 'border-[var(--border-strong)] hover:border-cyan-500/50 hover:bg-[var(--bg-elevated)]'
                )}
              >
                <div className="w-12 h-12 rounded-full bg-[var(--bg-elevated)] flex items-center justify-center">
                  <Upload className="w-5 h-5 text-slate-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-300">Drop image here or click to browse</p>
                  <p className="text-xs text-slate-500 mt-1">PNG, JPG, WEBP — any ad screenshot</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
                />
              </div>
            ) : (
              <div className="relative rounded-xl overflow-hidden border border-[var(--border-strong)]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={state.preview} alt="Ad preview" className="w-full max-h-72 object-contain bg-[var(--bg-elevated)]" />
                <button
                  onClick={(e) => { e.stopPropagation(); clear(); }}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="url"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="space-y-3"
          >
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="url"
                  placeholder="https://cdn.example.com/ad-creative.png"
                  value={state.url}
                  onChange={(e) => onUrlChange(e.target.value)}
                  className="input pl-9"
                />
              </div>
              {state.url && (
                <button onClick={clear} className="btn-ghost px-3">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            {state.preview && (
              <div className="rounded-xl overflow-hidden border border-[var(--border)]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={state.preview} alt="Ad preview" className="w-full max-h-48 object-contain bg-[var(--bg-elevated)]" />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {state.error && (
        <p className="text-sm text-red-400">{state.error}</p>
      )}

      <div className="flex items-center justify-between pt-2">
        <p className="text-xs text-slate-500">
          No ad image? You can skip this — the pipeline will still run CRO analysis.
        </p>
        <button
          onClick={hasInput ? handleContinue : () => onComplete({ file: null, url: '' })}
          className="btn-primary"
        >
          {hasInput ? 'Continue →' : 'Skip →'}
        </button>
      </div>
    </div>
  );
}
