// Assembles the npm package from the website's committed web fonts (apps/docs/public), which
// `bun run fonts:build` produces. Run by `npm pack` / `npm publish` (prepack); output is gitignored.
//
//   fonts/<PS>/<PS>[-Italic]-Variable.woff2   every family's variable WOFF2 (the files the website serves)
//   bloxwap-font.css          the website stylesheet: one family name per style, companions via unicode-range
//   sans-scripts.css          "Bloxwap Sans Scripts": the Sans companions, used as next/font fallback (src/sans.js)
//   mono-scripts.css          "Bloxwap Mono Scripts": the same for Mono (src/mono.js)
//   LICENSE                   SIL Open Font License 1.1
import { cp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const pkg = fileURLToPath(new URL('..', import.meta.url));
const repo = join(pkg, '../..');
const pub = join(repo, 'apps/docs/public');

// Bundlers resolve url() and next/font paths literally, so the package drops the axis brackets from file names:
// BloxwapSans[wght].woff2 -> BloxwapSans-Variable.woff2, BloxwapPixel-Italic[ROND,wght].woff2 -> BloxwapPixel-Italic-Variable.woff2.
const packaged = (file) => file.replace(/\[[A-Za-z,]+\](?=\.)/, '-Variable');
await rm(join(pkg, 'fonts'), { recursive: true, force: true });
for (const family of await readdir(join(pub, 'fonts'))) {
  await mkdir(join(pkg, 'fonts', family), { recursive: true });
  const variable = join(pub, 'fonts', family, 'variable');
  for (const entry of await readdir(variable, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.endsWith('.woff2')) {
      await cp(join(variable, entry.name), join(pkg, 'fonts', family, packaged(entry.name)));
    } else if (entry.name === 'subsets' && entry.isDirectory()) {
      for (const file of await readdir(join(variable, 'subsets'))) {
        if (file.endsWith('.woff2')) await cp(join(variable, 'subsets', file), join(pkg, 'fonts', family, packaged(file)));
      }
    }
  }
  await cp(join(repo, 'LICENSE'), join(pkg, 'fonts', family, 'LICENSE'));
}

const header = (title) => `/*\n * ${title}\n * @bloxwap/font — https://bloxwap.github.io/font/ — SIL Open Font License 1.1. © 2026 Bloxwap, Inc.\n */\n`;
// Package-relative URLs: no cache-busting query (the npm version does that) and no variable/ folder.
const site = (await readFile(join(pub, 'bloxwap-font.css'), 'utf8'))
  .replace(/url\("fonts\/([^/]+)\/variable\/(?:subsets\/)?([^"?]+)(?:\?[^"]*)?"\)/g, (_, family, file) => `url("./fonts/${family}/${packaged(decodeURIComponent(file))}")`);
const faces = site.match(/@font-face \{[^}]*\}/g) ?? [];
if (faces.length < 3) throw new Error(`expected @font-face rules in bloxwap-font.css, found ${faces.length}`);
await writeFile(join(pkg, 'bloxwap-font.css'), site.replace(/^\/\*[\s\S]*?\*\/\n/, header('Every Bloxwap Font family. Companion scripts load only when a page uses them (unicode-range).')));

for (const [style, ps] of [['Sans', 'BloxwapSans'], ['Mono', 'BloxwapMono']]) {
  // The companion faces of "Bloxwap <style>" (their file isn't the core font), renamed so next/font can list them as a fallback.
  const companions = faces.filter((f) => f.includes(`font-family: "Bloxwap ${style}";`) && !f.includes(`url("./fonts/${ps}/`))
    .map((f) => f.replace(`font-family: "Bloxwap ${style}";`, `font-family: "Bloxwap ${style} Scripts";`));
  if (!companions.length) throw new Error(`no ${style} companion faces found`);
  await writeFile(join(pkg, `${style.toLowerCase()}-scripts.css`), header(`"Bloxwap ${style} Scripts": Arabic, Hebrew, Armenian, Georgian and CJK companions for Bloxwap ${style}, each downloaded only when a page uses its script.`) + companions.join('\n') + '\n');
}

await cp(join(repo, 'LICENSE'), join(pkg, 'LICENSE'));
console.log(`@bloxwap/font: ${faces.length} @font-face rules, ${(await readdir(join(pkg, 'fonts'))).length} families`);

// Explicit CSS entries retain existing Unicode ranges, including locale-sensitive CJK ordering.
await rm(join(pkg, 'css'), { recursive: true, force: true });
await mkdir(join(pkg, 'css'), { recursive: true });
const groups = new Map();
for (const face of faces) {
  const family = /font-family: "([^"]+)"/.exec(face)[1];
  const ps = /url\("\.\/fonts\/([^/]+)\//.exec(face)[1];
  const role = family.includes('Mono') ? 'mono' : family.includes('Pixel') ? 'pixel' : 'sans';
  const suffix = ps.replace(/^Bloxwap(?:Sans|Mono|Pixel)/, '');
  const script = ({Arabic:'arabic', Hebrew:'hebrew', Armenian:'armenian', Georgian:'georgian', JP:'jp', KR:'kr', SC:'sc'})[suffix] ?? 'core';
  // Named companion aliases belong only to their script entry.
  for (const key of [role, `${role}-${script}`]) {
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(face.replaceAll('"./fonts/', '"../fonts/'));
  }
}
for (const [key, rules] of groups) await writeFile(join(pkg, 'css', `${key}.css`), header(key) + rules.join('\n') + '\n');
// Remove the old web-package layout; opt-in packages retain their hash-checked TTF cache.

// Complete core entry points preserve the original self-hosting option and keep
// every manifest web face addressable through a CSS export.
for (const role of ['sans', 'mono', 'pixel']) {
  const complete = groups.get(`${role}-core`).filter((face) => face.includes('.latin.woff2'))
    .map((face) => face.replace('.latin.woff2', '.woff2').replace(/\n  unicode-range: [^;]+;/, ''));
  await writeFile(join(pkg, 'css', `${role}-full.css`), header(`${role}: complete core fonts`) + complete.join('\n') + '\n');
}
await rm(join(pkg, 'native'), {recursive:true, force:true});
const { execFileSync } = await import('node:child_process');
execFileSync(process.env.FONT_PYTHON ?? 'python3', [join(pkg, 'scripts/faces.py')], {stdio:'inherit'});
