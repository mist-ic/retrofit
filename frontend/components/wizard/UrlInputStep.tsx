'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Globe, ArrowLeft, Zap } from 'lucide-react';

interface UrlInputStepProps {
  onBack: () => void;
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

const EXAMPLE_URLS = [
  'https://mamaearth.in/product/onion-hair-oil',
  'https://mokobara.com/collections/travel-bags',
  'https://damensch.com/pages/innerwear',
];

export function UrlInputStep({ onBack, onSubmit, isLoading }: UrlInputStepProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validate = (value: string): boolean => {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = () => {
    const trimmed = url.trim();
    if (!trimmed) { setError('Enter a landing page URL'); return; }
    if (!validate(trimmed)) { setError('Enter a valid URL starting with https://'); return; }
    setError('');
    onSubmit(trimmed);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-1">Enter the landing page URL</h2>
        <p className="text-sm text-slate-400">
          The page users land on after clicking the ad. Must be publicly accessible.
        </p>
      </div>

      <div className="space-y-2">
        <div className="relative">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="url"
            placeholder="https://example.com/summer-sale"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setError(''); }}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            className="input pl-9 pr-4 text-base"
            autoFocus
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>

      {/* Example URLs */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Try an example</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_URLS.map((ex) => (
            <button
              key={ex}
              onClick={() => { setUrl(ex); setError(''); }}
              className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border)] text-slate-400 hover:text-white hover:border-cyan-500/50 transition-all duration-150"
            >
              {new URL(ex).hostname}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between pt-2">
        <button onClick={onBack} className="btn-ghost">
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="btn-primary min-w-[140px]"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Starting...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Analyze
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
