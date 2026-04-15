import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // All /api/* paths proxy to FastAPI (includes /api/runs, /api/preview, /api/screenshots)
        source: "/api/:path*",
        destination: "http://127.0.0.1:8080/api/:path*",
      },
      {
        // Shortcut: /preview/* → /api/preview/* (for iframe src convenience)
        source: "/preview/:path*",
        destination: "http://127.0.0.1:8080/api/preview/:path*",
      },
      {
        // Shortcut: /screenshots/* → /api/screenshots/* (for img src convenience)
        source: "/screenshots/:path*",
        destination: "http://127.0.0.1:8080/api/screenshots/:path*",
      },
    ];
  },
};

export default nextConfig;
