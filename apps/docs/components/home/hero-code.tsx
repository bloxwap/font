import type { ReactNode } from 'react';
import { CopyTextButton } from '@/components/ui/copy-text-button';

const FILE = 'app/layout.tsx';

/** The Next.js quick start shown in the hero (the @bloxwap/font package API: one export per family). */
const SNIPPET = `import { BloxwapSans } from '@bloxwap/font/sans';
import { BloxwapMono } from '@bloxwap/font/mono';

// Two variable fonts: weights 100–900, italics, and
// Arabic, Hebrew, Armenian, Georgian and CJK built in.
const fonts = \`\${BloxwapSans.variable} \${BloxwapMono.variable}\`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={fonts}>
      <body className={BloxwapSans.className}>{children}</body>
    </html>
  );
}

// In CSS: font-family: var(--font-bloxwap-mono);`;

const KEYWORDS = new Set(['import', 'from', 'export', 'default', 'function', 'const', 'return']);
// Comments, strings and template literals, identifiers, then any single other character.
const TOKEN = /(\/\/[^\n]*)|('[^'\n]*'|"[^"\n]*"|`[^`]*`)|([A-Za-z_$][\w$]*)|([\s\S])/g;

/** A tiny highlighter for this one snippet, in the Bloxwap code palette (keyword, string, type). */
function highlight(code: string): ReactNode[] {
  const out: ReactNode[] = [];
  let plain = '';
  const flush = () => { if (plain !== '') out.push(plain); plain = ''; };
  for (const [, comment, string, word, other] of code.matchAll(TOKEN)) {
    const cls = comment ? 'syntax-muted' : string ? 'syntax-string' : word && KEYWORDS.has(word) ? 'syntax-keyword'
      : word && /^[A-Z]/.test(word) ? 'syntax-type' : null;
    const text = comment ?? string ?? word ?? other ?? '';
    if (cls === null) plain += text;
    else { flush(); out.push(<span key={out.length} className={cls}>{text}</span>); }
  }
  flush();
  return out;
}

/** The hero's code window: a Next.js layout using @bloxwap/font, with a copy button. */
export function HeroCode() {
  return <figure className="code-window" aria-label="Using @bloxwap/font in a Next.js layout">
    <figcaption className="code-toolbar">
      <span className="window-dots" aria-hidden="true"><i /><i /><i /></span>
      <span>{FILE}</span>
      <span className="code-actions"><span className="code-language">TSX</span><CopyTextButton text={`${SNIPPET}\n`} ariaLabel="Copy code" /></span>
    </figcaption>
    <pre><code>{highlight(SNIPPET)}</code></pre>
    <p className="code-status"><span aria-hidden="true" /> Bloxwap Sans and Mono on every page, in every script</p>
  </figure>;
}
