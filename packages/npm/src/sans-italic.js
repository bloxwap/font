import localFont from 'next/font/local';

// The italic face of Bloxwap Sans, imported for its side effect by ./sans.js. It is a separate next/font call so that it
// can opt out of preloading: `preload` applies to every file in a call, and a page that never renders italic text
// would otherwise download the italic as well. Without a preload, the browser fetches this face only when text uses it.
//
// next/font/local names the family after the const the call is assigned to, so this const must stay `BloxwapSans`:
// that adds the italic to the same family as the normal face in ./sans.js, and <em> gets the real italic, not a
// synthesized slant.
const BloxwapSans = localFont({
  src: [{ path: '../fonts/BloxwapSans/BloxwapSans-Italic-Variable.woff2', weight: '100 900', style: 'italic' }],
  display: 'swap',
  preload: false,
  // Like ./sans.js, no metric-adjusted fallback face.
  adjustFontFallback: false,
});

export default BloxwapSans;
