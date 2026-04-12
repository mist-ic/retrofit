'use client';

import Link from 'next/link';
import { Zap } from 'lucide-react';

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-base)]/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold tracking-tight text-white">RetroFit</span>
        </Link>

        <div className="flex items-center gap-4">
          <a
            href="https://github.com/mist-ic/retrofit"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            GitHub
          </a>
          <Link href="/" className="btn-primary text-xs px-3 py-1.5">
            New Analysis
          </Link>
        </div>
      </div>
    </nav>
  );
}
