import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
const root = new URL('../styles/', import.meta.url);
const source = JSON.parse(await readFile(new URL('hig-source.json', root), 'utf8')) as { files: Record<string, string> };
for (const [name, expected] of Object.entries(source.files)) {
 const actual = createHash('sha256').update(await readFile(new URL(name, root))).digest('hex');
 if (actual !== expected) throw new Error(`${name} differs from pinned HIG distribution; review upstream upgrade and provenance`);
}
console.log('Pinned HIG CSS distribution hashes OK');
