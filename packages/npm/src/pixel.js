import localFont from 'next/font/local';
// The italic face: the same family, not preloaded, so it downloads only when a page renders italic text.
import './pixel-italic.js';

/**
 * Bloxwap Pixel for Next.js: variable weight 100–900 and roundness (set `font-variation-settings: "ROND" 0–100`),
 * with italics; `variable` sets --font-bloxwap-pixel. Next.js preloads the normal face; the italic loads only when a
 * page renders italic text.
 */
export const BloxwapPixel = localFont({
  // No `style` on this src: with a single file next/font copies its style onto className and .style, and a
  // `font-style: normal` there would cancel inherited italics (<em><code className>) and fall back to the normal face.
  src: [{ path: '../fonts/BloxwapPixel/BloxwapPixel-Variable.woff2', weight: '100 900' }],
  variable: '--font-bloxwap-pixel',
  display: 'swap',
  adjustFontFallback: false,
  fallback: ['ui-monospace', 'monospace'],
});
