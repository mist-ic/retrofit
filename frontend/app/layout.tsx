import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'RetroFit — AI Landing Page Personalization',
  description:
    'Feed an ad creative and a landing page URL into a 6-agent AI pipeline that rewrites the hero section to match the ad and improve conversion rate.',
  keywords: ['CRO', 'landing page', 'AI', 'personalization', 'conversion rate optimization'],
  openGraph: {
    title: 'RetroFit — AI Landing Page Personalization',
    description: 'AI agents that rewrite landing pages to match ad creatives.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="relative z-10 antialiased">{children}</body>
    </html>
  );
}
