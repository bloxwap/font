import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const root = new URL('../', import.meta.url);
const nativeRoot = new URL('../native/', root);
const manifest = JSON.parse(await readFile(new URL('manifest.json',root)));
const pkg = JSON.parse(await readFile(new URL('package.json',root)));
const nativePackages = await Promise.all((await readdir(nativeRoot)).map(async dir => ({
 root: new URL(`${dir}/`,nativeRoot),
 pkg: JSON.parse(await readFile(new URL(`${dir}/package.json`,nativeRoot))),
})));
const nativeFamilies = p => Object.keys(p.pkg.exports).filter(key => key !== './assets/*').map(key => key.slice(2));
const assetURL = face => {
 if(face.format === 'woff2') return new URL(face.path,root);
 const p=nativePackages.find(p=>p.pkg.name===face.package);
 assert.ok(p,face.path);
 assert.ok(face.path.startsWith(`${face.package}/assets/`));
 return new URL(face.path.slice(`${face.package}/assets/`.length),p.root);
};
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
 for(const p of nativePackages) for(const family of nativeFamilies(p)) {
  for(const file of await readdir(new URL(`${family}/`,p.root))) if(file.endsWith('.ttf')) {
   assert.ok(listed.has(`${p.pkg.name}/assets/${family}/${file}`)); count++;
  }
 }
 assert.equal(count,manifest.faces.length);
 for (const face of manifest.faces) {
  const bytes=await readFile(assetURL(face));
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
test('native packages have matching versions, licenses and stable Metro registration keys',async()=>{
 assert.equal(nativePackages.length,8);
 const license=await readFile(new URL('../../LICENSE',root),'utf8');
 for(const p of nativePackages) {
  assert.equal(p.pkg.version,pkg.version,p.pkg.name);
  assert.equal(p.pkg.license,'OFL-1.1');
  assert.equal(p.pkg.publishConfig.access,'public');
  assert.equal(await readFile(new URL('LICENSE',p.root),'utf8'),license);
  assert.ok(p.pkg.files.includes('LICENSE'));
  assert.equal(p.pkg.exports['./assets/*'],'./*');
  for(const family of nativeFamilies(p)) {
   assert.deepEqual(p.pkg.exports[`./${family}`],{types:`./${family}/index.d.ts`,default:`./${family}/index.js`});
   const js=await readFile(new URL(`${family}/index.js`,p.root),'utf8');
   const types=await readFile(new URL(`${family}/index.d.ts`,p.root),'utf8');
   const entries=[...js.matchAll(/"([^"]+)": require\("\.\/([^"]+)"\)/g)];
   const faces=manifest.faces.filter(f=>f.path.startsWith(`${p.pkg.name}/assets/${family}/`));
   assert.ok(faces.length>0);
   assert.equal(entries.length,faces.length);
   for(const [_,name,file] of entries) {
    assert.ok(faces.some(f=>f.registrationName===name && f.path.endsWith('/'+file)));
    assert.ok(types.includes(`readonly "${name}": number;`));
   }
  }
 }
});
test('web npm distribution stays under 20 MB and contains no native assets',async()=>{
 const {stdout}=await promisify(execFile)('npm',['pack','--dry-run','--json','--ignore-scripts'],{cwd:root,maxBuffer:10*1024*1024});
 const [pack]=JSON.parse(stdout);
 assert.ok(pack.unpackedSize<=20_000_000,`unpacked size ${pack.unpackedSize} exceeds 20 MB`);
 assert.ok(!pack.files.some(f=>f.path.startsWith('native/') || f.path.endsWith('.ttf')));
 assert.ok(!Object.keys(pkg.exports).some(key=>key.startsWith('./native/')));
 assert.ok(pack.files.some(f=>f.path==='LICENSE'));
 assert.equal(pkg.license,'OFL-1.1');
});
