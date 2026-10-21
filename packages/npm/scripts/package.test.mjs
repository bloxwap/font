import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const root = new URL('../', import.meta.url);
const nativeRoot = new URL('native/', root);
const manifest = JSON.parse(await readFile(new URL('manifest.json',root)));
const staticSources = JSON.parse(await readFile(new URL('static-sources.json',root)));
const pkg = JSON.parse(await readFile(new URL('package.json',root)));
const nativeFamilies = (await readdir(nativeRoot, {withFileTypes:true}))
 .filter(entry=>entry.isDirectory()).map(entry=>entry.name);
const assetURL = face => new URL(face.path,root);
test('manifest describes every built font and exact bytes', async () => {
 assert.equal(manifest.version,pkg.version);
 const listed = new Set(manifest.faces.map(f=>f.path));
 assert.equal(listed.size,manifest.faces.length);
 let count=0;
 for (const family of await readdir(new URL('fonts/',root))) {
  for (const file of await readdir(new URL(`fonts/${family}/`,root))) if (file.endsWith('.woff2')) {
   assert.ok(listed.has(`fonts/${family}/${file}`)); count++;
  }
 }
 for(const family of nativeFamilies) {
  for(const file of await readdir(new URL(`${family}/`,nativeRoot))) if(file.endsWith('.ttf')) {
   assert.ok(listed.has(`native/${family}/${file}`)); count++;
  }
 }
 assert.equal(count,manifest.faces.length);
 for (const face of manifest.faces) {
  const bytes=await readFile(assetURL(face));
  assert.equal(bytes.length,face.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'),face.sha256);
  assert.equal(face.packageVersion,pkg.version);
  assert.ok(face.scripts.length);
  if (face.format === 'ttf') {
   const family = face.path.split('/').at(-2);
   const source = staticSources.families[family];
   const file = source.files.find(file => `${source.asset}:${file.path}@${source.tag}` === face.source);
   assert.ok(file, face.source);
   assert.equal(face.sourceSha256, file.sha256);
  }
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
test('native family maps have exact registration keys and isolated CommonJS scope',async()=>{
 assert.equal(nativeFamilies.length,17);
 assert.deepEqual(pkg.exports['./native/*'],{types:'./native/*/index.d.ts',default:'./native/*/index.js'});
 assert.equal(pkg.exports['./native/assets/*'],'./native/*');
 assert.deepEqual(JSON.parse(await readFile(new URL('package.json',nativeRoot))),{type:'commonjs'});
 for(const family of nativeFamilies) {
  const js=await readFile(new URL(`${family}/index.js`,nativeRoot),'utf8');
  const types=await readFile(new URL(`${family}/index.d.ts`,nativeRoot),'utf8');
  const entries=[...js.matchAll(/"([^"\n]+)": require\("\.\/([^"\n]+)"\)/g)];
  const faces=manifest.faces.filter(f=>f.path.startsWith(`native/${family}/`));
  assert.ok(faces.length>0);
  assert.equal(entries.length,faces.length);
  for(const [_,name,file] of entries) {
   assert.ok(faces.some(f=>f.registrationName===name && f.path.endsWith('/'+file)));
   assert.ok(types.includes(`readonly "${name}": number;`));
  }
 }
});
test('single npm distribution contains the complete catalog with selective asset exports',async()=>{
 const {stdout}=await promisify(execFile)('npm',['pack','--dry-run','--json','--ignore-scripts'],{cwd:root,maxBuffer:10*1024*1024});
 const [pack]=JSON.parse(stdout);
 assert.ok(pack.unpackedSize<=300_000_000,`unpacked size ${pack.unpackedSize} exceeds 300 MB`);
 const packedFonts=pack.files.filter(f=>/\.(ttf|woff2)$/.test(f.path));
 assert.deepEqual(packedFonts.map(f=>f.path).sort(),manifest.faces.map(f=>f.path).sort());
 assert.equal(packedFonts.filter(f=>f.path.endsWith('.ttf')).length,216);
 assert.ok(pack.files.some(f=>f.path==='native/package.json'));
 assert.ok(pack.files.some(f=>f.path==='LICENSE'));
 assert.equal(pkg.license,'OFL-1.1');
 assert.equal(pkg.name,'@bloxwap/font');
});
test('direct native imports resolve only the selected font asset',async()=>{
 const {createRequire}=await import('node:module');
 const {runInNewContext}=await import('node:vm');
 const require=createRequire(new URL('package.json',root));
 for(const face of manifest.faces.filter(f=>f.format==='ttf')) {
  const subpath=`@bloxwap/font/native/assets/${face.path.slice('native/'.length)}`;
  assert.equal(require.resolve(subpath),new URL(face.path,root).pathname);
  assert.equal(face.package,'@bloxwap/font');
 }
 const imported=[];
 const module={exports:{}};
 const source=await readFile(new URL('native/BloxwapSans/index.js',root),'utf8');
 runInNewContext(source,{module,require:path=>{imported.push(path); return imported.length;}});
 assert.equal(imported.length,18);
 assert.ok(imported.every(path=>path.startsWith('./BloxwapSans-') && path.endsWith('.ttf')));
 assert.equal(typeof module.exports['BloxwapSans-SemiBold'],'number');
});

test('core CSS uses script subsets while next/font retains complete sources',async()=>{
 for (const role of ['sans','mono','pixel']) {
  const css=await readFile(new URL(`css/${role}-core.css`,root),'utf8');
  assert.equal((css.match(/@font-face/g)??[]).length,8);
  assert.equal((css.match(/unicode-range:/g)??[]).length,8);
  for(const subset of ['latin','greek','cyrillic','other']) {
   assert.equal((css.match(new RegExp(`\\.${subset}\\.woff2`,'g'))??[]).length,2);
  }
  const js=await readFile(new URL(`src/${role}.js`,root),'utf8');
  assert.ok(js.includes('-Variable.woff2'));
  assert.ok(!js.includes('-Variable.latin.woff2'));
 }
 const latin=manifest.faces.find(f=>f.path==='fonts/BloxwapSans/BloxwapSans-Variable.latin.woff2');
 const full=manifest.faces.find(f=>f.path==='fonts/BloxwapSans/BloxwapSans-Variable.woff2');
 assert.ok(latin.bytes>0 && latin.bytes<full.bytes);
 const css=await readFile(new URL('bloxwap-font.css',root));
 const {gzipSync}=await import('node:zlib');
 assert.ok(gzipSync(css).length<10_000);
 assert.equal(pkg.license,'OFL-1.1');
 assert.equal(await readFile(new URL('LICENSE',root),'utf8'),await readFile(new URL('../../LICENSE',root),'utf8'));
});
