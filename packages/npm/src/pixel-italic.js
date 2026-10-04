import localFont from 'next/font/local';

// The italic face of Bloxwap Pixel, imported for its side effect by ./pixel.js. It is a separate next/font call so that it
// can opt out of preloading: `preload` applies to every file in a call, and a page that never renders italic text
// would otherwise download the italic as well. Without a preload, the browser fetches this face only when text uses it.
//
// From Next.js 15, next/font/local names the family after the const the call is assigned to (Next 13.2-14 hashed it
// per call, hence the `next >=15` peer range), so this const must stay `BloxwapPixel`:
// that adds the italic to the same family as the normal face in ./pixel.js, and <em> gets the real italic, not a
// synthesized slant.
const BloxwapPixel = localFont({
  src: [{ path: '../fonts/BloxwapPixel/BloxwapPixel-Italic-Variable.woff2', weight: '100 900', style: 'italic' }],
  display: 'swap',
  preload: false,
  // Like ./pixel.js, no metric-adjusted fallback face.
  adjustFontFallback: false,
});

export default BloxwapPixel;
