import localFont from 'next/font/local';
// The companion scripts (Arabic, Hebrew, Armenian, Georgian, CJK) as one fallback family with unicode-range.
import '../mono-scripts.css';

/** Bloxwap Mono for Next.js: variable weight 100–900 with italics; `variable` sets --font-bloxwap-mono. */
export const BloxwapMono = localFont({
  src: [
    { path: '../fonts/BloxwapMono/BloxwapMono-Variable.woff2', weight: '100 900', style: 'normal' },
    { path: '../fonts/BloxwapMono/BloxwapMono-Italic-Variable.woff2', weight: '100 900', style: 'italic' },
  ],
  variable: '--font-bloxwap-mono',
  display: 'swap',
  adjustFontFallback: false,
  fallback: ['Bloxwap Mono Scripts', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
});
