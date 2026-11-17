// tsrs and typescript must agree across every app. A silent mismatch means CI
// (tsrs) and next build (typescript) check different languages.
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const pins = new Map();
for (const app of readdirSync('apps')) {
  const path = join('apps', app, 'package.json');
  const pkg = JSON.parse(readFileSync(path, 'utf8'));
  const deps = { ...pkg.dependencies, ...pkg.devDependencies };
  for (const name of ['tsrs', 'typescript']) {
    if (!deps[name]) continue;
    if (!pins.has(name)) pins.set(name, new Map());
    const versions = pins.get(name);
    if (!versions.has(deps[name])) versions.set(deps[name], []);
    versions.get(deps[name]).push(path);
  }
}
let failed = false;
for (const [name, versions] of pins) {
  if (versions.size !== 1) {
    failed = true;
    console.error(`${name} versions differ:`);
    for (const [version, files] of versions) console.error(`  ${version}: ${files.join(', ')}`);
  }
}
if (failed) process.exit(1);
console.log(`typecheck pins agree: ${[...pins].map(([name, versions]) => `${name}@${[...versions.keys()][0]}`).join(', ')}`);
