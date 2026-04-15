import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8080";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        // All /api/* paths proxy to FastAPI (includes /api/runs, /api/preview, /api/screenshots)
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        // Shortcut: /preview/* → /api/preview/* (for iframe src convenience)
        source: "/preview/:path*",
        destination: `${BACKEND_URL}/api/preview/:path*`,
      },
      {
        // Shortcut: /screenshots/* → /api/screenshots/* (for img src convenience)
        source: "/screenshots/:path*",
        destination: `${BACKEND_URL}/api/screenshots/:path*`,
      },
    ];
  },
};

export default nextConfig;
