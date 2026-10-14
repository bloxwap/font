import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const root = new URL('../', import.meta.url);
const manifest = JSON.parse(await readFile(new URL('manifest.json',root)));
const pkg = JSON.parse(await readFile(new URL('package.json',root)));
test('manifest describes every built font and exact bytes', async () => {
 assert.equal(manifest.version,pkg.version);
 const listed = new Set(manifest.faces.map(f=>f.path));
 assert.equal(listed.size,manifest.faces.length);
 let count=0;
 for (const dir of ['fonts','native']) for (const family of await readdir(new URL(`${dir}/`,root))) {
  for (const file of await readdir(new URL(`${dir}/${family}/`,root))) if (/\.(ttf|woff2)$/.test(file)) {
   assert.ok(listed.has(`${dir}/${family}/${file}`)); count++;
  }
 }
 assert.equal(count,manifest.faces.length);
 for (const face of manifest.faces) {
  const bytes=await readFile(new URL(face.path,root));
  assert.equal(bytes.length,face.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'),face.sha256);
  assert.equal(face.packageVersion,pkg.version);
  assert.ok(face.scripts.length);
 }
});
test('CSS exports resolve real files and all manifest web faces',async()=>{
 const referenced = new Set();
 for(const entry of await readdir(new URL('css/',root))) {
  const url=new URL(`css/${entry}`,root);
  const css=await readFile(url,'utf8');
  assert.ok(css.includes('@font-face'));
  const role=entry.split('-')[0].replace('.css','');
  assert.ok(css.includes(`Bloxwap ${role[0].toUpperCase()+role.slice(1)}`));
  for(const match of css.matchAll(/url\("([^"]+)"\)/g)) {
   assert.ok((await stat(new URL(match[1],url))).isFile());
   referenced.add(match[1].replace('../',''));
  }
 }
 assert.deepEqual([...referenced].sort(),manifest.faces.filter(f=>f.format==='woff2').map(f=>f.path).sort());
 assert.equal(pkg.exports['./css/*'],'./css/*.css');
 const core=await readFile(new URL('css/sans-core.css',root),'utf8');
 assert.ok(!core.includes('Arabic'));
 const arabic=await readFile(new URL('css/sans-arabic.css',root),'utf8');
 assert.ok(!arabic.includes('BloxwapSans/'));
});
test('native Metro entries have exact stable registration keys',async()=>{
 for(const family of await readdir(new URL('native/',root))) {
  const js=await readFile(new URL(`native/${family}/index.js`,root),'utf8');
  const entries=[...js.matchAll(/"([^"]+)": require\("\.\/([^"]+)"\)/g)];
  const faces=manifest.faces.filter(f=>f.path.startsWith(`native/${family}/`));
  assert.equal(entries.length,faces.length);
  for(const [_,name,file] of entries) assert.ok(faces.some(f=>f.registrationName===name && f.path.endsWith('/'+file)));
 }
});
