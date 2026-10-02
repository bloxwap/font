// Verifies the static export GitHub Pages will serve: required files, social cards, and base-path-safe links.
import { readFile, readdir, stat } from 'node:fs/promises';
import { join, extname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../out/', import.meta.url));
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? '';
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://bloxwap.github.io';
const failures: string[] = [];
const exists = async (path: string): Promise<boolean> => { try { return (await stat(path)).isFile(); } catch { return false; } };
async function walk(path: string): Promise<string[]> {
  const entries = await readdir(path, { withFileTypes: true });
  return (await Promise.all(entries.map(async (entry) => entry.isDirectory()
    ? walk(join(path, entry.name)) : [join(path, entry.name)]))).flat();
}

for (const required of [
  'index.html', '404.html', 'docs/index.html', 'search.json', 'icon.svg', 'llms.txt', 'robots.txt', 'bloxwap-font.css', 'OFL.txt',
  'data/index.json', 'data/sans.json', 'data/sans.glyphs.json', 'data/mono.json', 'data/pixel.json',
  'sitemap.xml', 'og/home.png', '.nojekyll',
]) {
  if (!await exists(join(root, required))) failures.push(`Missing ${required}`);
}

// Every font the generated stylesheet points at must ship, or text silently falls back to system fonts.
const css = await readFile(join(root, 'bloxwap-font.css'), 'utf8').catch(() => '');
let fontFaces = 0;
for (const [, url] of css.matchAll(/url\("([^"?]+)(?:\?[^"]*)?"\)/g)) {
  fontFaces++;
  if (!await exists(join(root, decodeURIComponent(url!)))) failures.push(`bloxwap-font.css: missing ${url}`);
}
if (!fontFaces) failures.push('bloxwap-font.css declares no fonts');
// Web fonts listed in the data JSON must ship too (zips are GitHub Release assets, checked by the smoke test).
const dataFiles = (await readdir(join(root, 'data')).catch(() => [] as string[])).filter((name) => /^[\w-]+\.json$/.test(name) && !name.endsWith('.glyphs.json'));
for (const name of dataFiles) {
  const data = JSON.parse(await readFile(join(root, 'data', name), 'utf8'));
  const paths: string[] = name === 'index.json' ? [] : (data.files?.web ?? []).map((file: { path: string }) => file.path);
  for (const path of paths.filter(Boolean)) {
    if (!await exists(join(root, path))) failures.push(`data/${name}: missing ${path}`);
  }
}

const files = (await walk(root)).filter((file) => extname(file) === '.html');
let socialCards = 0;
for (const file of files) {
  const html = await readFile(file, 'utf8');
  const name = relative(root, file).split(sep).join('/');
  if (name === 'index.html' || (name.startsWith('docs/') && name.endsWith('/index.html'))) {
    const meta = new Map([...html.matchAll(/<meta\b[^>]*>/g)].map(([tag]): [string | undefined, string | undefined] => {
      const attrs: Record<string, string> = Object.fromEntries([...tag.matchAll(/([\w:-]+)="([^"]*)"/g)].map(([, key, value]) => [key, value!.replaceAll('&amp;', '&')]));
      return [attrs.property ?? attrs.name, attrs.content];
    }));
    const route = name === 'index.html' ? '/' : `/${name.slice(0, -'index.html'.length)}`;
    const imagePath = route === '/' ? '/og/home.png' : route === '/docs/' ? '/og/docs/index.png' : `/og${route.slice(0, -1)}.png`;
    const absolute = (path: string): string => new URL(`${basePath}${path}`, siteUrl).href;
    for (const [key, expected] of Object.entries({
      'og:site_name': 'Bloxwap Font', 'og:url': absolute(route), 'og:image': absolute(imagePath),
      'og:image:width': '1200', 'og:image:height': '630', 'twitter:card': 'summary_large_image',
    })) {
      if (meta.get(key) !== expected) failures.push(`${name}: expected ${key} = ${expected}, got ${meta.get(key)}`);
    }
    try {
      const png = await readFile(join(root, imagePath));
      if (png.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a' || png.readUInt32BE(16) !== 1200 || png.readUInt32BE(20) !== 630) {
        failures.push(`${name}: ${imagePath} must be a 1200×630 PNG`);
      }
    } catch { failures.push(`${name}: missing social card ${imagePath}`); }
    socialCards++;
  }
  // Every root-relative asset or link must carry the base path, or it 404s on GitHub Pages.
  if (basePath) {
    for (const [, url] of html.matchAll(/(?:href|src)="(\/[^"]*)"/g)) {
      if (!url.startsWith(`${basePath}/`) && url !== basePath) failures.push(`${name}: ${url} is missing base path ${basePath}`);
    }
  }
}

if (failures.length) {
  console.error(`Static export check failed:\n  ${[...new Set(failures)].slice(0, 50).join('\n  ')}`);
  process.exit(1);
}
console.log(`Static export OK: ${files.length} HTML files, ${socialCards} social cards, ${fontFaces} @font-face rules${basePath ? `, base path ${basePath}` : ''}.`);
