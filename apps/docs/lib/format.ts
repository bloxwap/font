export function fmtBytes(n: number | null | undefined): string {
  if (n == null) return '';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
export const fmtNum = (n: number): string => Number(n).toLocaleString('en-US');
export const hex = (u: number): string => `U+${u.toString(16).toUpperCase().padStart(4, '0')}`;
export const plural = (n: number, one: string, many = `${one}s`): string => `${fmtNum(n)} ${n === 1 ? one : many}`;
