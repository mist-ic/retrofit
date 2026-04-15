import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RetroFit | Intelligence",
  description: "Differential CRO Personalization Architecture",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col selection:bg-white selection:text-black">
        {children}
      </body>
    </html>
  );
}
