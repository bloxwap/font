/** Client-safe family helpers shared by the home page and docs components. */

export const PRIMARY = ['sans', 'mono', 'pixel'] as const;

const FALLBACK: Record<string, string> = {
  sans: 'ui-rounded, system-ui, -apple-system, "Segoe UI", sans-serif',
  mono: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace',
  pixel: '"Bloxwap Mono", ui-monospace, monospace',
};

/** "Bloxwap Sans KR" -> "Sans KR". */
export function shortName(name: string): string { return name.replace(/^Bloxwap /, ''); }

/** The CSS family stack for a family: its own name, then the combined family of its style. */
export function fontStack(name: string, style: string): string {
  const base = style === 'mono' ? '"Bloxwap Mono"' : style === 'pixel' ? '"Bloxwap Pixel"' : '"Bloxwap Sans"';
  const own = `"${name}"`;
  return [own, own === base ? null : base, FALLBACK[style] ?? FALLBACK.sans].filter(Boolean).join(', ');
}

const DEFAULT_INSTANCES = [
  [100, 'Thin'], [200, 'ExtraLight'], [300, 'Light'], [400, 'Regular'], [500, 'Medium'],
  [600, 'SemiBold'], [700, 'Bold'], [800, 'ExtraBold'], [900, 'Black'],
] as const;

/** The named instance at a weight ("Regular" for 400), or ''. */
export function instanceName(instances: { name: string; coords: Record<string, number> }[] | undefined, weight: number): string {
  const list = instances?.length ? instances : DEFAULT_INSTANCES.map(([w, name]) => ({ name, coords: { wght: w } }));
  const hit = list.find((i) => i.coords.wght != null && Math.round(i.coords.wght) === Math.round(weight));
  return hit ? hit.name.replace(/ Italic$/, '') : '';
}

export function weightLadder(instances: { name: string; coords: Record<string, number> }[] | undefined): { name: string; weight: number }[] {
  const list = instances?.length ? instances : DEFAULT_INSTANCES.map(([w, name]) => ({ name, coords: { wght: w } }));
  return list.filter((i) => i.coords.wght != null).map((i) => ({ name: i.name, weight: Math.round(i.coords.wght) }));
}
