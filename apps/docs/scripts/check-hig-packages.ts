// Keep docs on the published @bloxwap/hig package and reject copied HIG token/control CSS.
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';

const name = '@bloxwap/hig';
const version = '0.2.0';
const docs = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
const lock = await readFile(new URL('../../../bun.lock', import.meta.url), 'utf8');
const declared = [...Object.keys(docs.dependencies ?? {}), ...Object.keys(docs.devDependencies ?? {})].filter((dep) => dep.startsWith('@bloxwap/hig'));
assert.deepEqual(declared, [name], `docs must depend on ${name} only`);
assert.equal(docs.dependencies[name], version, `${name} must use the coordinated registry version`);
assert(!/@bloxwap\/hig-/.test(lock), 'bun.lock must not pin unpublished @bloxwap/hig-* 0.1 packages');
assert(!lock.includes('vendor/bloxwap-hig'), 'HIG runtime packages must resolve from the registry');

const entry = lock.split('\n').find((line) => line.trimStart().startsWith(`"${name}": [`));
assert(entry?.includes(`"${name}@${version}"`) && entry.includes('"sha512-') && !entry.includes('file:'), `${name} needs a registry integrity entry in bun.lock`);

const manifest = await installedManifest(name);
assert.equal(manifest.version, version, `${name} installed version differs from the docs manifest`);
assert.equal(manifest.name, name);

const nextConfig = await readFile(new URL('../next.config.ts', import.meta.url), 'utf8');
assert.match(nextConfig, /transpilePackages:\s*\[[^\]]*['"]@bloxwap\/hig['"]/);
assert.doesNotMatch(nextConfig, /@bloxwap\/hig-/);

async function installedManifest(pkg: string) {
  // Exports maps hide package.json. Isolated installs live in the workspace; a hoisted install lives at the root.
  for (const base of [new URL('../', import.meta.url), new URL('../../../', import.meta.url)]) {
    try {
      return JSON.parse(await readFile(new URL(`node_modules/${pkg}/package.json`, base), 'utf8'));
    } catch { /* try the next location */ }
  }
  throw new Error(`${pkg} is not installed; run bun install --frozen-lockfile`);
}

async function* sources(dir: URL): AsyncGenerator<URL> {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) yield* sources(new URL(`${entry.name}/`, dir));
    else if (/\.(css|tsx?)$/.test(entry.name)) yield new URL(entry.name, dir);
  }
}
for (const dir of ['app/', 'components/', 'lib/', 'styles/']) {
  for await (const file of sources(new URL(`../${dir}`, import.meta.url))) {
    const text = await readFile(file, 'utf8');
    if (/@bloxwap\/hig-/.test(text)) {
      throw new Error(`${file.pathname} still references an unpublished @bloxwap/hig-* package; import @bloxwap/hig subpaths`);
    }
    // Palette/spacing tokens and the base control rule must come from the package. Density variables such as
    // --hig-control are documented host settings (HIG itself sets them per [data-hig-density]) and stay allowed.
    if (/--hig-(?:background|surface|nested|text|muted|faint|border|action|onAction|focus|buy|sell|positive|negative|warning|info|space-[a-z]+)\s*:/.test(text) || /\.hig-button\s*\{/.test(text)) {
      throw new Error(`${file.pathname} redefines HIG tokens or control styles; import them from @bloxwap/hig/tokens/css and @bloxwap/hig/react/css`);
    }
  }
}
console.log(`HIG ${version} registry package, lockfile integrity and source guard OK`);
