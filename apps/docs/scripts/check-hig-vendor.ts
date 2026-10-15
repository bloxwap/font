// Guards the HIG consumption path: the vendored candidate tarballs match their recorded provenance, the installed
// packages are those tarballs, and no hand-copied HIG token/control CSS has crept back into the docs sources.
import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';

const vendor = new URL('../../../vendor/bloxwap-hig/', import.meta.url);
const provenance = JSON.parse(await readFile(new URL('provenance.json', vendor), 'utf8')) as { artifactVersion: string; sourceCommit: string; files: Record<string, string> };
for (const [file, expected] of Object.entries(provenance.files)) {
  const actual = createHash('sha256').update(await readFile(new URL(file, vendor))).digest('hex');
  if (actual !== expected) throw new Error(`vendor/bloxwap-hig/${file} does not match provenance.json; re-pack from bloxwap/hig ${provenance.sourceCommit}`);
}

for (const name of ['@bloxwap/hig-tokens', '@bloxwap/hig-contracts', '@bloxwap/hig-react']) {
  // The packages' exports maps hide package.json, so read the installed copy through node_modules.
  const manifest = JSON.parse(await readFile(new URL(`../node_modules/${name}/package.json`, import.meta.url), 'utf8')) as { version: string };
  if (manifest.version !== provenance.artifactVersion) throw new Error(`${name} ${manifest.version} is installed; expected ${provenance.artifactVersion}`);
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
    // Palette/spacing tokens and the base control rule must come from the packages. Density variables such as
    // --hig-control are documented host settings (HIG itself sets them per [data-hig-density]) and stay allowed.
    if (/--hig-(?:background|surface|nested|text|muted|faint|border|action|onAction|focus|buy|sell|positive|negative|warning|info|space-[a-z]+)\s*:/.test(text) || /\.hig-button\s*\{/.test(text)) {
      throw new Error(`${file.pathname} redefines HIG tokens or control styles; import them from @bloxwap/hig-tokens/css and @bloxwap/hig-react/css`);
    }
  }
}
console.log(`HIG ${provenance.artifactVersion} vendored tarballs, installed packages and source guard OK`);
