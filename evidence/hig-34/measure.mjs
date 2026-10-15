// Measures the static export and presentation sources for the HIG #34 Font row.
// Usage (repo root): node evidence/hig-34/measure.mjs <before|after> [outDir]
import { readFileSync, readdirSync, statSync, existsSync, writeFileSync } from 'node:fs';
import { join, extname } from 'node:path';
import { gzipSync } from 'node:zlib';

const phase = process.argv[2];
const out = process.argv[3] ?? 'apps/docs/out';
if (!phase) throw new Error('phase required');
const walk = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]);
const files = walk(out);
const byExt = {};
for (const f of files) { const ext = extname(f) || '(none)'; byExt[ext] = (byExt[ext] ?? 0) + statSync(f).size; }
const css = files.filter((f) => f.endsWith('.css') && f.includes('/_next/')).map((f) => {
  const body = readFileSync(f);
  return { file: f.slice(out.length + 1), raw: body.length, gzip: gzipSync(body, { level: 9 }).length };
});
const docs = 'apps/docs';
const presentation = ['app/global.css', ...(existsSync(`${docs}/styles`) ? readdirSync(`${docs}/styles`).map((f) => `styles/${f}`) : [])];
const sources = presentation.map((f) => { const body = readFileSync(join(docs, f), 'utf8'); return { file: f, bytes: Buffer.byteLength(body), lines: body.split('\n').length }; });
const primitives = ['components/ui/controls.tsx', 'components/ui/copy-text-button.tsx', 'components/ui/toast.tsx', 'scripts/check-hig-source.ts', 'scripts/check-hig-vendor.ts']
  .filter((f) => existsSync(join(docs, f))).map((f) => ({ file: f, bytes: statSync(join(docs, f)).size }));
const pkg = JSON.parse(readFileSync(`${docs}/package.json`, 'utf8'));
const lock = readFileSync('bun.lock', 'utf8');
const lockPackages = (() => { const start = lock.indexOf('"packages": {'); return start < 0 ? 0 : (lock.slice(start).match(/^ {4}"[^"]+": \[/gm) ?? []).length; })();
const result = {
  phase,
  export: { files: files.length, bytes: files.reduce((n, f) => n + statSync(f).size, 0), bytesExcludingFonts: files.filter((f) => !/\.(woff2?|ttf)$/.test(f)).reduce((n, f) => n + statSync(f).size, 0), byExtension: byExt },
  generatedCss: { files: css, raw: css.reduce((n, c) => n + c.raw, 0), gzip: css.reduce((n, c) => n + c.gzip, 0) },
  presentationSources: { files: sources, bytes: sources.reduce((n, s) => n + s.bytes, 0), lines: sources.reduce((n, s) => n + s.lines, 0) },
  primitiveAndCheckFiles: primitives,
  dependencies: { runtime: Object.keys(pkg.dependencies).length, dev: Object.keys(pkg.devDependencies).length, runtimeHig: Object.keys(pkg.dependencies).filter((d) => d.startsWith('@bloxwap/hig-')), lockfilePackages: lockPackages },
};
writeFileSync(`evidence/hig-34/${phase}-measure.json`, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ phase, exportBytes: result.export.bytes, cssRaw: result.generatedCss.raw, cssGzip: result.generatedCss.gzip, sources: result.presentationSources, deps: result.dependencies }, null, 1));
