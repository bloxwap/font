import { hex } from '@/lib/format';
import type { Glyph } from '@/lib/types';

/** Keep the source characters intact: features change rendering, never clipboard text. */
export function glyphText(glyph: Glyph): string | null {
  return glyph.u != null ? String.fromCodePoint(glyph.u) : glyph.t || null;
}

/** Shared outlines can represent different characters; give each scalar its own selection. */
export function glyphVariants(glyphs: Glyph[]): Glyph[] {
  return glyphs.flatMap((glyph) => [glyph, ...(glyph.v ?? (glyph.alt ?? []).map((u) => ({ u, d: undefined })))
    .map((variant) => ({ ...glyph, ...variant, alt: undefined, v: undefined }))]);
}

export function glyphKey(glyph: Glyph): string {
  return `${glyph.n}:${glyph.u ?? 'unencoded'}`;
}

export function glyphLabel(glyph: Glyph): string {
  const name = glyph.d ?? glyph.n;
  return glyph.u != null ? `${name}, ${hex(glyph.u)}`
    : glyph.f ? `${name}, ${glyph.c === 'Ligatures' ? 'ligature' : 'alternate'} via ${glyph.f}` : name;
}
