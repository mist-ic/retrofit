'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { AdUploadStep } from '@/components/wizard/AdUploadStep';
import { UrlInputStep } from '@/components/wizard/UrlInputStep';
import { createRun } from '@/lib/api';
import { Zap, Shield, BarChart3, Wand2 } from 'lucide-react';

type AdInput = { file: File | null; url: string };

const FEATURES = [
  { icon: Zap, text: 'Real-time 6-agent pipeline with live status' },
  { icon: BarChart3, text: '7-criterion CRO audit with scored breakdown' },
  { icon: Shield, text: 'Hallucination detection — every change is grounded' },
  { icon: Wand2, text: 'Surgical HTML patches, never full-page rewrites' },
];

export default function HomePage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [adInput, setAdInput] = useState<AdInput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleAdComplete = (input: AdInput) => {
    setAdInput(input);
    setStep(2);
  };

  const handleSubmit = async (landingPageUrl: string) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('landing_page_url', landingPageUrl);
      if (adInput?.file) formData.append('ad_image', adInput.file);
      if (adInput?.url) formData.append('ad_image_url', adInput.url);

      const { run_id } = await createRun(formData);
      router.push(`/run/${run_id}`);
    } catch (e) {
      console.error(e);
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold text-white">RetroFit</span>
        </div>
      </header>

      <div className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">

          {/* Left — hero copy */}
          <div className="space-y-8 lg:pt-6">
            <div className="space-y-4">
              <div className="badge badge-cyan w-fit">6-agent AI pipeline</div>
              <h1 className="text-4xl lg:text-5xl font-bold leading-tight tracking-tight">
                Make your landing page{' '}
                <span className="gradient-text">match the ad</span>
              </h1>
              <p className="text-lg text-slate-400 leading-relaxed">
                Feeds an ad screenshot and a landing page URL into AI agents that rewrite
                the hero section to close the message gap and improve conversion rate.
              </p>
            </div>

            <ul className="space-y-3">
              {FEATURES.map(({ icon: Icon, text }) => (
                <li key={text} className="flex items-center gap-3 text-sm text-slate-300">
                  <div className="w-7 h-7 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center flex-shrink-0">
                    <Icon className="w-3.5 h-3.5 text-cyan-400" />
                  </div>
                  {text}
                </li>
              ))}
            </ul>

            {/* Step indicators */}
            <div className="flex items-center gap-3">
              {[1, 2].map((s) => (
                <div key={s} className="flex items-center gap-2">
                  <div className={`w-6 h-6 rounded-full text-xs flex items-center justify-center font-semibold transition-all ${
                    step >= s ? 'bg-cyan-500 text-white' : 'bg-[var(--bg-elevated)] text-slate-500 border border-[var(--border)]'
                  }`}>
                    {s}
                  </div>
                  <span className={`text-xs ${step >= s ? 'text-slate-300' : 'text-slate-600'}`}>
                    {s === 1 ? 'Ad creative' : 'Landing page'}
                  </span>
                  {s < 2 && <span className="text-slate-700 text-xs">→</span>}
                </div>
              ))}
            </div>
          </div>

          {/* Right — wizard card */}
          <div className="glass glass-elevated rounded-2xl p-6 lg:p-8">
            <AnimatePresence mode="wait">
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <AdUploadStep onComplete={handleAdComplete} />
                </motion.div>
              )}
              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <UrlInputStep
                    onBack={() => setStep(1)}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

        </div>
      </div>
    </main>
  );
}
