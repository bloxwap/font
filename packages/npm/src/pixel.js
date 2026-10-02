import localFont from 'next/font/local';

/**
 * Bloxwap Pixel for Next.js: variable weight 100–900 and roundness (set `font-variation-settings: "ROND" 0–100`),
 * with italics; `variable` sets --font-bloxwap-pixel.
 */
export const BloxwapPixel = localFont({
  src: [
    { path: '../fonts/BloxwapPixel/BloxwapPixel-Variable.woff2', weight: '100 900', style: 'normal' },
    { path: '../fonts/BloxwapPixel/BloxwapPixel-Italic-Variable.woff2', weight: '100 900', style: 'italic' },
  ],
  variable: '--font-bloxwap-pixel',
  display: 'swap',
  adjustFontFallback: false,
  fallback: ['ui-monospace', 'monospace'],
});
