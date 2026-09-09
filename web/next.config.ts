import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  turbopack: {
    // Pin the workspace root to this directory -- a package-lock.json
    // outside the git repo (unrelated to this project) would otherwise
    // make Turbopack guess the wrong root.
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
