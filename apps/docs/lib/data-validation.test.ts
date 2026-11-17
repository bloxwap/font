import { FONT_VERSION } from './font-version';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateData } from './data-validation';
test('rejects malformed, misidentified and invalid Unicode glyph payloads', () => {
  for (const data of [{assetVersion:FONT_VERSION,id:'sans',glyphs:{}}, {assetVersion:FONT_VERSION,id:'mono',glyphs:[]}, {assetVersion:FONT_VERSION,id:'sans',glyphs:[{n:'bad',c:'Letters',s:'Latin',a:500,u:0xd800}]}]) {
    assert.throws(() => validateData('/data/sans.glyphs.json', data));
  }
  assert.deepEqual(validateData('/data/sans.glyphs.json', {assetVersion:FONT_VERSION,id:'sans',glyphs:[]}), {assetVersion:FONT_VERSION,id:'sans',glyphs:[]});
});
