// Keep docs on coordinated registry packages and reject copied HIG token/control CSS.
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';

const version = '0.1.0';
const docs = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
const lock = await readFile(new URL('../../../bun.lock', import.meta.url), 'utf8');
for (const name of ['@bloxwap/hig-tokens', '@bloxwap/hig-contracts', '@bloxwap/hig-react']) {
  assert.equal(docs.dependencies[name], version, `${name} must use the coordinated registry version`);
  // Exports maps hide package.json, so read the installed workspace dependency directly.
  const manifest = JSON.parse(await readFile(new URL(`../node_modules/${name}/package.json`, import.meta.url), 'utf8'));
  assert.equal(manifest.version, version, `${name} installed version differs from the docs manifest`);
  const entry = lock.split('\n').find(line => line.trimStart().startsWith(`"${name}": [`));
  assert(entry?.includes(`"${name}@${version}"`) && entry.includes('"sha512-'), `${name} needs a registry integrity entry in bun.lock`);
}
assert(!lock.includes('vendor/bloxwap-hig'), 'HIG runtime packages must resolve from the registry');

async function* sources(dir: URL): AsyncGenerator<URL> {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) yield* sources(new URL(`${entry.name}/`, dir));
    else if (/\.(css|tsx?)$/.test(entry.name)) yield new URL(entry.name, dir);
  }
}
for (const dir of ['app/', 'components/', 'lib/', 'styles/']) {
  for await (const file of sources(new URL(`../${dir}`, import.meta.url))) {
    const text = await readFile(file, 'utf8');
    // Palette/spacing tokens and the base control rule must come from the packages. Density variables such as
    // --hig-control are documented host settings (HIG itself sets them per [data-hig-density]) and stay allowed.
    if (/--hig-(?:background|surface|nested|text|muted|faint|border|action|onAction|focus|buy|sell|positive|negative|warning|info|space-[a-z]+)\s*:/.test(text) || /\.hig-button\s*\{/.test(text)) {
      throw new Error(`${file.pathname} redefines HIG tokens or control styles; import them from @bloxwap/hig-tokens/css and @bloxwap/hig-react/css`);
    }
  }
}
console.log(`HIG ${version} registry packages, lockfile integrity and source guard OK`);
