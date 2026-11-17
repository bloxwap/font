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

// Download URLs must identify the same immutable release as the source lock.
const lock = JSON.parse(await (await import('node:fs/promises')).readFile(new URL('../../../packages/npm/static-sources.json', import.meta.url), 'utf8'));
const { RELEASE_TAG } = await import('../lib/release-version');
if (Object.values(lock.families).some((entry) => (entry as { tag: string }).tag !== RELEASE_TAG)) {
  throw new Error('Download release and static source pins differ; update lib/release-version.ts');
}

// A stale version constant must never bless a mixture of old metadata and new fonts.
const { createHash } = await import('node:crypto');
const { readdir, readFile } = await import('node:fs/promises');
const { FONT_VERSION } = await import('../lib/font-version');
async function fontPaths(directory: string): Promise<string[]> {
  const entries = await readdir(pub + directory, { withFileTypes: true });
  const paths: string[] = [];
  for (const entry of entries) {
    const path = `${directory}/${entry.name}`;
    if (entry.isDirectory()) paths.push(...await fontPaths(path));
    else if (path.endsWith('.woff2')) paths.push(path);
  }
  return paths;
}
const hash = createHash('sha1');
for (const path of (await fontPaths('fonts')).sort()) {
  hash.update(path);
  hash.update(await readFile(pub + path));
}
if (hash.digest('hex').slice(0, 10) !== FONT_VERSION) {
  throw new Error('Hosted fonts changed without regenerating the stylesheet and metadata');
}
