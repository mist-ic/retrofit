'use client';

import { ExplanationItem } from '@/lib/types';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ExplanationPanelProps {
  explanations: ExplanationItem[];
}

const PRINCIPLE_LABELS: Record<string, string> = {
  message_match: '🎯 Message Match',
  hero_clarity: '✨ Hero Clarity',
  cta_visibility: '⚡ CTA Visibility',
  social_proof: '⭐ Social Proof',
  urgency_scarcity: '⏰ Urgency',
  trust_signals: '🛡️ Trust',
  mobile_readiness: '📱 Mobile',
};

export function ExplanationPanel({ explanations }: ExplanationPanelProps) {
  if (!explanations.length) {
    return <p className="text-sm text-slate-500 py-8 text-center">No explanation data available.</p>;
  }

  return (
    <div className="space-y-4">
      {explanations.map((item, i) => (
        <motion.div
          key={item.change_id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="glass rounded-xl p-4 space-y-3"
        >
          {/* Selector */}
          <div className="flex items-center gap-2">
            <code className="text-xs text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded font-mono">
              {item.element_selector}
            </code>
            <span className={cn(
              'text-xs px-2 py-0.5 rounded-full font-medium',
              item.change_type === 'copy' ? 'badge-cyan' : item.change_type === 'style' ? 'badge-purple' : 'badge-amber'
            )}>
              {item.change_type}
            </span>
          </div>

          {/* Before/after text */}
          {(item.original_text || item.new_text) && (
            <div className="grid grid-cols-2 gap-3">
              {item.original_text && (
                <div className="space-y-1">
                  <span className="text-xs font-medium text-red-400 uppercase tracking-wider">Before</span>
                  <p className="text-sm text-slate-400 line-through leading-snug">{item.original_text}</p>
                </div>
              )}
              {item.new_text && (
                <div className="space-y-1">
                  <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">After</span>
                  <p className="text-sm text-white font-medium leading-snug">{item.new_text}</p>
                </div>
              )}
            </div>
          )}

          {/* Rationale */}
          <p className="text-sm text-slate-300 leading-relaxed">{item.rationale}</p>

          {/* CRO principle tags */}
          <div className="flex flex-wrap gap-1.5">
            {item.cro_principles.map((p) => (
              <span key={p} className="badge badge-cyan text-xs">
                {PRINCIPLE_LABELS[p] || p}
              </span>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
