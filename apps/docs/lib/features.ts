/** Descriptions and preview samples for OpenType features (the tags come from each font's GSUB/GPOS). */

/** Features browsers apply by default; toggling one of these turns it OFF. */
export const DEFAULT_ON = new Set(['liga', 'calt', 'kern', 'clig', 'locl', 'ccmp', 'mark', 'mkmk', 'rlig', 'init', 'medi', 'fina', 'isol', 'curs']);

const ORDER = ['ss', 'cv', 'liga', 'calt', 'dlig', 'tnum', 'pnum', 'lnum', 'onum', 'zero', 'frac', 'numr', 'dnom', 'sups', 'subs', 'sinf', 'ordn', 'case', 'smcp', 'c2sc', 'salt', 'kern'];
export function featureRank(tag: string): number {
  const i = ORDER.findIndex((prefix) => tag.startsWith(prefix));
  return i < 0 ? 99 : i;
}

export const FEATURE_INFO: Record<string, { description: string; sample?: string }> = {
  liga: { description: 'Standard ligatures, on by default.', sample: 'fi fl ff' },
  calt: { description: 'Contextual alternates. In Bloxwap Mono these are the code ligatures; they keep every glyph on the 600-unit grid.', sample: '=> != >= <= -> :: |>' },
  dlig: { description: 'Discretionary ligatures: arrows typed as ASCII become real arrows.', sample: '-> <- => <->' },
  kern: { description: 'Kerning, on by default. Turn it off to see the raw spacing.', sample: 'AV To Wa Ty' },
  tnum: { description: 'Tabular figures: every digit has the same width so columns of numbers line up. The default figures are already tabular.', sample: '1,111.11 0,000.00' },
  pnum: { description: 'Proportional figures: digits take their natural width, for figures in running text.', sample: '1,111.11 0,000.00' },
  zero: { description: 'Slashed zero, to tell 0 from O at a glance.', sample: '0O 2026 0x00' },
  case: { description: 'Case-sensitive forms: punctuation moves up to sit with capitals.', sample: '(HELLO) [A-Z] {@} ¡¿' },
  frac: { description: 'Fractions: numerator, fraction slash, denominator.', sample: '1/2 3/4 5/8' },
  sups: { description: 'Superscript figures.', sample: 'x2 E=mc2' },
  subs: { description: 'Subscript figures.', sample: 'H2O CO2' },
  sinf: { description: 'Scientific inferiors, for chemical formulas.', sample: 'H2O C6H12O6' },
  numr: { description: 'Numerators (figures raised to fraction height).', sample: '0123456789' },
  dnom: { description: 'Denominators (figures lowered to fraction height).', sample: '0123456789' },
  ordn: { description: 'Ordinals: superior letters after figures.', sample: '1a 2o No' },
  smcp: { description: 'Small capitals from lowercase letters.', sample: 'Small caps' },
  c2sc: { description: 'Capitals to small capitals, for acronyms in text.', sample: 'NASA and USB' },
  salt: { description: 'Stylistic alternates.' },
  locl: { description: 'Localized forms, chosen by the lang attribute (Romanian, Catalan, Serbian, Bulgarian, Macedonian).' },
  ccmp: { description: 'Glyph composition and decomposition (accents), always on.' },
  mark: { description: 'Mark positioning: places accents on base letters.' },
  mkmk: { description: 'Mark-to-mark positioning: stacks accents.' },
  init: { description: 'Arabic initial forms (applied automatically by joining).' },
  medi: { description: 'Arabic medial forms (applied automatically by joining).' },
  fina: { description: 'Arabic final forms (applied automatically by joining).' },
  isol: { description: 'Arabic isolated forms (applied automatically by joining).' },
  rlig: { description: 'Required ligatures (such as Arabic lam-alef), always on.' },
  ljmo: { description: 'Hangul leading jamo forms.' },
  vjmo: { description: 'Hangul vowel jamo forms.' },
  tjmo: { description: 'Hangul trailing jamo forms.' },
  fwid: { description: 'Full-width forms.' },
  hwid: { description: 'Half-width forms.' },
  palt: { description: 'Proportional alternate widths for CJK punctuation.' },
  halt: { description: 'Alternate half widths for CJK punctuation.' },
  vert: { description: 'Vertical alternates for vertical text.' },
};

/** label = the stylistic set's own name (from the font, or tools/bwfont/features.py SS_NAMES). */
export function featureDescription(tag: string, name: string, chars: string, label?: string | null): string {
  if (FEATURE_INFO[tag]) return FEATURE_INFO[tag].description;
  if (/^(ss|cv)\d\d$/.test(tag)) {
    // The label (e.g. "Single-storey a") is shown as the title, so describe the set and what it touches.
    return chars ? `${name}: changes ${[...chars].slice(0, 12).join(' ')}.` : `${name}.`;
  }
  return name;
}

/** Text that shows a feature's effect: curated samples first, then the characters it changes. */
export function featureSample(tag: string, chars: string, sequences: string[]): string {
  const curated = FEATURE_INFO[tag]?.sample;
  if (curated) return curated;
  if (/^(ss|cv)\d\d$/.test(tag) && chars) return [...chars].slice(0, 14).join(' ');
  if (sequences.length) return sequences.slice(0, 6).join(' ');
  if (chars) return [...chars].slice(0, 14).join('');
  return '';
}

