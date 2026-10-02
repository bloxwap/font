import { fmtNum } from './format';
import type { FamilyMeta } from './types';

/** "11,172 Hangul syllables"-style numbers, for scripts Hyperglot can't summarise as languages. */
export function coverageHighlights(meta: Pick<FamilyMeta, 'coverage'>): { value: string; label: string }[] {
  const out: { value: string; label: string }[] = [];
  const block = (name: string) => meta.coverage.blocks.find((b) => b.name === name)?.count ?? 0;
  const script = (name: string) => meta.coverage.scripts.find((s) => s.script === name)?.count ?? 0;
  if (block('Hangul Syllables')) out.push({ value: fmtNum(block('Hangul Syllables')), label: 'Hangul syllables' });
  if (script('Han')) out.push({ value: fmtNum(script('Han')), label: 'hanzi' });
  if (script('Arabic')) out.push({ value: fmtNum(script('Arabic')), label: 'Arabic characters' });
  for (const name of ['Hebrew', 'Armenian', 'Georgian']) {
    if (script(name)) out.push({ value: fmtNum(script(name)), label: `${name} characters` });
  }
  for (const s of meta.coverage.scripts) {
    if (['Hangul', 'Han', 'Arabic', 'Hebrew', 'Armenian', 'Georgian', 'Common'].includes(s.script)) continue;
    out.push({ value: fmtNum(s.count), label: `${s.script} characters` });
  }
  return out;
}
