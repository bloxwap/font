// Runs before dev/build: the site reads public/data/*.json and public/fonts at build time.
import { stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const pub = fileURLToPath(new URL('../public/', import.meta.url));
const missing: string[] = [];
for (const path of ['data/index.json', 'data/sans.json', 'data/sans.glyphs.json', 'bloxwap-font.css', 'fonts/BloxwapSans/variable']) {
  try { await stat(pub + path); } catch { missing.push(path); }
}
try { await stat(fileURLToPath(new URL('../lib/font-version.ts', import.meta.url))); } catch { missing.push('lib/font-version.ts'); }
if (missing.length) {
  console.error(`Missing generated font data: ${missing.join(', ')}.
From the repository root, build the fonts or refresh the website copies:
  bun run fonts:setup      # once: Python toolchain in packages/font/.venv
  bun run fonts:build      # build every family (writes apps/docs/public)
  bun run fonts:web        # re-package existing builds for the website
  bun run docs:data        # data only`);
  process.exit(1);
}
