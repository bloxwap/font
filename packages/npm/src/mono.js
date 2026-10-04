import localFont from 'next/font/local';
// The companion scripts (Arabic, Hebrew, Armenian, Georgian, CJK) as one fallback family with unicode-range.
import '../mono-scripts.css';
// The italic face: the same family, not preloaded, so it downloads only when a page renders italic text.
import './mono-italic.js';

/**
 * Bloxwap Mono for Next.js: variable weight 100–900 with italics; `variable` sets --font-bloxwap-mono.
 * Next.js preloads the normal face; the italic loads only when a page renders italic text.
 */
export const BloxwapMono = localFont({
  src: [{ path: '../fonts/BloxwapMono/BloxwapMono-Variable.woff2', weight: '100 900', style: 'normal' }],
  variable: '--font-bloxwap-mono',
  display: 'swap',
  adjustFontFallback: false,
  fallback: ['Bloxwap Mono Scripts', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
});
