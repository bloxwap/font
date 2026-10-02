import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { glyphKey, glyphLabel, glyphText, glyphVariants } from './glyph-text';
import type { Glyph } from './types';

const base: Glyph = { n: 'a', u: 0x61, c: 'Lowercase', s: 'Latin', a: 600 };

test('encoded characters keep their Unicode code point and readable identity', () => {
  const greek = { ...base, n: 'alpha', u: 0x3b1, d: 'Greek small letter alpha' };
  assert.equal(glyphText(greek), 'α');
  assert.equal(glyphLabel(greek), 'Greek small letter alpha, U+03B1');
});

test('alternates and ligatures copy source text without compatibility substitutions', () => {
  assert.equal(glyphText({ ...base, n: 'a.ss01', u: null, t: 'a', f: 'ss01' }), 'a');
  assert.equal(glyphText({ ...base, n: 'f_i', u: null, t: 'fi', f: 'liga' }), 'fi');
  assert.equal(glyphText({ ...base, n: 'hyphen_greater.code', u: null, t: '->', f: 'calt' }), '->');
  assert.equal(glyphText({ ...base, n: 'eacute', u: null, t: 'e\u0301' }), 'e\u0301');
});

test('invisible and supplementary-plane characters are intact; unreachable glyphs have no source', () => {
  assert.equal(glyphText({ ...base, u: 0x20 }), ' ');
  assert.equal(glyphText({ ...base, u: 0x1f600 }), '😀');
  assert.equal(glyphText({ ...base, n: '.notdef', u: null }), null);
});

test('shared outlines retain separate Unicode identities and selection keys', () => {
  const variants = glyphVariants([{ ...base, n: 'mu', u: 0xb5, d: 'Micro sign', alt: [0x3bc],
    v: [{ u: 0x3bc, d: 'Greek small letter mu', c: 'Lowercase', s: 'Greek' }] }]);
  assert.equal(variants.length, 2);
  assert.equal(glyphText(variants[0]!), 'µ');
  assert.equal(glyphText(variants[1]!), 'μ');
  assert.equal(glyphLabel(variants[1]!), 'Greek small letter mu, U+03BC');
  assert.notEqual(glyphKey(variants[0]!), glyphKey(variants[1]!));
});
