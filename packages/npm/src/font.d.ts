/** What `next/font` returns for a font with a CSS variable. */
export interface BloxwapFont {
  /** Applies the font family: add to an element's className. */
  className: string;
  /** Defines the CSS variable (e.g. --font-bloxwap-sans): add to <html> or <body> className. */
  variable: string;
  style: { fontFamily: string; fontWeight?: number; fontStyle?: string };
}
