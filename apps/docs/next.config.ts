import { createMDX } from 'fumadocs-mdx/next';
import type { NextConfig } from 'next';

const withMDX = createMDX();

const config: NextConfig = {
  output: 'export',
  trailingSlash: true,
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? '',
  images: { unoptimized: true },
  reactStrictMode: true,
  // Type checking runs before `next build` via scripts/typecheck.mjs (tsrs, with a tsc fallback on
  // platforms tsrs has no binary for), so Next's built-in TypeScript 6 pass is skipped.
  typescript: { ignoreBuildErrors: true },
  // Resolve dependencies from the workspace root (bun workspaces); the font build lives in
  // packages/font and writes its web fonts and data into public/.
  turbopack: { root: new URL('../..', import.meta.url).pathname },
};

export default withMDX(config);
