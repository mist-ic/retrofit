'use client';

import { ReactCompareSlider, ReactCompareSliderImage } from 'react-compare-slider';

interface BeforeAfterSliderProps {
  originalUrl: string;
  modifiedUrl: string;
}

export function BeforeAfterSlider({ originalUrl, modifiedUrl }: BeforeAfterSliderProps) {
  return (
    <div className="rounded-xl overflow-hidden border border-[var(--border)]">
      <ReactCompareSlider
        itemOne={
          <div className="relative">
            <ReactCompareSliderImage src={originalUrl} alt="Original landing page" />
            <div className="absolute top-3 left-3 badge badge-red text-xs pointer-events-none">Original</div>
          </div>
        }
        itemTwo={
          <div className="relative">
            <ReactCompareSliderImage src={modifiedUrl} alt="Optimized landing page" />
            <div className="absolute top-3 right-3 badge badge-emerald text-xs pointer-events-none">Optimized</div>
          </div>
        }
        style={{ height: '560px' }}
      />
    </div>
  );
}
