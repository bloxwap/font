import { createMDX } from 'fumadocs-mdx/next';
import type { NextConfig } from 'next';

const withMDX = createMDX();

const config: NextConfig = {
  output: 'export',
  trailingSlash: true,
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? '',
  images: { unoptimized: true },
  reactStrictMode: true,
  // Resolve dependencies from the workspace root (bun workspaces); the font build lives in
  // packages/font and writes its web fonts and data into public/.
  turbopack: { root: new URL('../..', import.meta.url).pathname },
};

export default withMDX(config);
