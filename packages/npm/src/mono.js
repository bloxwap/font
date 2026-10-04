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
  // No `style` on this src: with a single file next/font copies its style onto className and .style, and a
  // `font-style: normal` there would cancel inherited italics (<em><code className>) and fall back to the normal face.
  src: [{ path: '../fonts/BloxwapMono/BloxwapMono-Variable.woff2', weight: '100 900' }],
  variable: '--font-bloxwap-mono',
  display: 'swap',
  adjustFontFallback: false,
  fallback: ['Bloxwap Mono Scripts', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
});
