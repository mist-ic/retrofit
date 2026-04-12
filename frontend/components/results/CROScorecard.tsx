'use client';

import { CROFindings, CriterionScore } from '@/lib/types';
import { cn, formatScore, scoreBg, scoreColor } from '@/lib/utils';
import { motion } from 'framer-motion';

interface CROScorecardProps {
  findings: CROFindings;
  scoreBefore: number;
  scoreAfter: number;
  liftRange: string;
}

export function CROScorecard({ findings, scoreBefore, scoreAfter, liftRange }: CROScorecardProps) {
  const delta = scoreAfter - scoreBefore;

  return (
    <div className="space-y-6">
      {/* Score summary */}
      <div className="grid grid-cols-3 gap-4">
        <ScoreCard label="Before" score={scoreBefore} />
        <ScoreCard label="After" score={scoreAfter} highlight />
        <div className="glass rounded-xl p-4 flex flex-col items-center justify-center gap-1">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Est. Lift</span>
          <span className="text-2xl font-bold text-purple-400">+{liftRange}</span>
          <span className="text-xs text-slate-500">CVR improvement</span>
        </div>
      </div>

      {/* Summary */}
      <div className="glass rounded-xl p-4">
        <p className="text-sm text-slate-300">{findings.summary}</p>
      </div>

      {/* Criteria table */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Criteria Breakdown</h3>
        {findings.criteria.map((c) => (
          <CriterionRow key={c.criterion_id} criterion={c} />
        ))}
      </div>
    </div>
  );
}

function ScoreCard({ label, score, highlight }: { label: string; score: number; highlight?: boolean }) {
  return (
    <div className={cn('glass rounded-xl p-4 flex flex-col items-center gap-1', highlight && 'border-cyan-500/20')}>
      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
      <span className={cn('text-3xl font-bold tabular-nums', scoreColor(score))}>
        {formatScore(score)}
      </span>
      <span className="text-xs text-slate-500">/ 100</span>
    </div>
  );
}

function CriterionRow({ criterion }: { criterion: CriterionScore }) {
  return (
    <div className="glass rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-200">{criterion.label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">weight {(criterion.weight * 100).toFixed(0)}%</span>
          <span className={cn('text-sm font-bold tabular-nums', scoreColor(criterion.score))}>
            {formatScore(criterion.score)}
          </span>
        </div>
      </div>
      <div className="h-1.5 w-full rounded-full bg-[var(--bg-elevated)] overflow-hidden">
        <motion.div
          className={cn('h-full rounded-full', scoreBg(criterion.score))}
          initial={{ width: 0 }}
          animate={{ width: `${criterion.score}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      <p className="text-xs text-slate-400">{criterion.rationale}</p>
    </div>
  );
}
