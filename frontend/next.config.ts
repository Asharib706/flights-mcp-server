import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Without this, Turbopack's automatic workspace-root inference walks up
  // past this directory and can latch onto an unrelated package.json/lockfile
  // that happens to live above the repo, breaking module resolution
  // (tailwindcss in particular) intermittently depending on its cache state.
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
