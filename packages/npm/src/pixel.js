import localFont from 'next/font/local';
// The italic face: the same family, not preloaded, so it downloads only when a page renders italic text.
import './pixel-italic.js';

/**
 * Bloxwap Pixel for Next.js: variable weight 100–900 and roundness (set `font-variation-settings: "ROND" 0–100`),
 * with italics; `variable` sets --font-bloxwap-pixel. Next.js preloads the normal face; the italic loads only when a
 * page renders italic text.
 */
export const BloxwapPixel = localFont({
  src: [{ path: '../fonts/BloxwapPixel/BloxwapPixel-Variable.woff2', weight: '100 900', style: 'normal' }],
  variable: '--font-bloxwap-pixel',
  display: 'swap',
  adjustFontFallback: false,
  fallback: ['ui-monospace', 'monospace'],
});
