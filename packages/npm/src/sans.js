import localFont from 'next/font/local';
// The companion scripts (Arabic, Hebrew, Armenian, Georgian, CJK) as one fallback family with unicode-range.
import '../sans-scripts.css';
// The italic face: the same family, not preloaded, so it downloads only when a page renders italic text.
import './sans-italic.js';

/**
 * Bloxwap Sans for Next.js: variable weight 100–900 with italics; `variable` sets --font-bloxwap-sans.
 * Next.js preloads the normal face; the italic loads only when a page renders italic text.
 */
export const BloxwapSans = localFont({
  src: [{ path: '../fonts/BloxwapSans/BloxwapSans-Variable.woff2', weight: '100 900', style: 'normal' }],
  variable: '--font-bloxwap-sans',
  display: 'swap',
  // A metric-adjusted Arial fallback would sit before the companions and draw Arabic and Hebrew in Arial.
  adjustFontFallback: false,
  fallback: ['Bloxwap Sans Scripts', 'ui-rounded', 'system-ui', 'sans-serif'],
});
