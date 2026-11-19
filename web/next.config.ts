import type { NextConfig } from "next";

// Address of the FastAPI backend. The browser only talks to Next.js: requests to
// /api/... are forwarded (rewritten) to the backend, so there is one origin and no CORS.
const apiUrl = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  output: "standalone", // small self-contained server, used by the Docker image
  devIndicators: false, // hide the Next.js dev badge
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
