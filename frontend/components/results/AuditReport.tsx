'use client';

import { QAReport } from '@/lib/types';
import { cn, severityColor } from '@/lib/utils';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface AuditReportProps {
  report: QAReport;
}

export function AuditReport({ report }: AuditReportProps) {
  return (
    <div className="space-y-5">
      {/* Overall status banner */}
      <div className={cn(
        'flex items-center gap-3 rounded-xl px-4 py-3 border',
        report.passed
          ? 'bg-emerald-500/8 border-emerald-500/20'
          : 'bg-amber-500/8 border-amber-500/20'
      )}>
        {report.passed
          ? <CheckCircle className="w-5 h-5 text-emerald-400" />
          : <AlertTriangle className="w-5 h-5 text-amber-400" />}
        <div>
          <p className={cn('text-sm font-semibold', report.passed ? 'text-emerald-400' : 'text-amber-400')}>
            {report.passed ? 'QA Passed' : 'Completed with warnings'}
          </p>
          <p className="text-xs text-slate-400">
            {report.grounded_change_count} grounded changes applied
            {report.visual_diff_score != null && ` · ${(report.visual_diff_score * 100).toFixed(0)}% visual delta`}
          </p>
        </div>
      </div>

      {/* Check grid */}
      <div className="grid grid-cols-2 gap-3">
        <CheckRow label="Valid HTML" passed={report.is_valid_html} />
        <CheckRow label="Key elements present" passed={report.key_elements_present} />
        <CheckRow label="No hallucinations" passed={report.hallucination_flags.length === 0} />
        <CheckRow label="Visual integrity" passed={!report.visual_diff_score || report.visual_diff_score < 0.5} />
      </div>

      {/* Structural issues */}
      {report.structural_issues.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Structural Issues</h4>
          {report.structural_issues.map((issue, i) => (
            <div key={i} className={cn('text-xs px-3 py-2 rounded-lg border', severityColor(issue.severity))}>
              <span className="font-semibold">[{issue.severity.toUpperCase()}]</span> {issue.message}
            </div>
          ))}
        </div>
      )}

      {/* Hallucination flags */}
      {report.hallucination_flags.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hallucination Flags</h4>
          {report.hallucination_flags.map((flag, i) => (
            <div key={i} className="text-xs px-3 py-2 rounded-lg border bg-red-500/8 border-red-500/20 text-red-300">
              <span className="font-semibold">[{flag.code}]</span> {flag.message}
              <span className="block text-red-400/70 mt-0.5">"{flag.offending_text}"</span>
            </div>
          ))}
        </div>
      )}

      {/* Failure reasons */}
      {report.failure_reasons.length > 0 && (
        <div className="space-y-1">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Failure Reasons</h4>
          {report.failure_reasons.map((r, i) => (
            <p key={i} className="text-xs text-slate-400 bg-[var(--bg-elevated)] px-3 py-1.5 rounded-lg">{r}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function CheckRow({ label, passed }: { label: string; passed: boolean }) {
  return (
    <div className={cn(
      'flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm',
      passed
        ? 'border-emerald-500/15 bg-emerald-500/5 text-emerald-400'
        : 'border-red-500/15 bg-red-500/5 text-red-400'
    )}>
      {passed
        ? <CheckCircle className="w-4 h-4 flex-shrink-0" />
        : <XCircle className="w-4 h-4 flex-shrink-0" />}
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}
