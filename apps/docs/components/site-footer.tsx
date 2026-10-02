import { assetUrl } from '@/lib/site';

/** Link columns mirror the bloxwap.com footer (as on bloxwap.github.io), so every Bloxwap site points at the same places. */
const COLUMNS: [string, [string, string][]][] = [
  ['Product', [['Home', 'https://bloxwap.com'], ['Web', 'https://bloxwap.app'], ['Pro', 'https://bloxwap.pro'], ['App', 'https://bloxwap.com/#app']]],
  ['Social', [['X', 'https://x.com/bloxwap'], ['Telegram', 'https://t.me/bloxwap'], ['Discord', 'https://discord.com/invite/cEfkcg6JHT'], ['Reddit', 'https://www.reddit.com/r/Bloxwap/']]],
  ['Open source', [['Chart SDK', 'https://bloxwap.github.io/chart/'], ['Hyperliquid SDK', 'https://bloxwap.github.io/hyperliquid/'], ['SFX', 'https://bloxwap.github.io/sfx/'], ['GitHub', 'https://github.com/bloxwap']]],
];

/** The Bloxwap site footer: brand, three link columns, and the legal row. */
export function SiteFooter() {
  return <footer className="site-footer">
    <div className="footer-grid">
      <div className="footer-brand">
        <a className="footer-lockup" href="https://bloxwap.github.io/" aria-label="Bloxwap on GitHub">
          {/* Supplied Bloxwap artwork (brand lockups); the marks are never redrawn. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={assetUrl('/logos/bloxwap-lockup.svg')} alt="" width={151} height={36} />
        </a>
        <p>The easiest way to trade.</p>
      </div>
      {COLUMNS.map(([title, links]) => <nav className="footer-col" key={title} aria-label={title}>
        <h2>{title}</h2>
        {links.map(([label, href]) => <a href={href} key={label}>{label}</a>)}
      </nav>)}
    </div>
    <div className="footer-base">
      <span>© {new Date().getFullYear()} Bloxwap, Inc. · Fonts licensed under the <a href={assetUrl('/docs/license/')}>SIL Open Font License 1.1</a></span>
      <nav className="footer-legal" aria-label="Legal">
        <a href="https://bloxwap.com/docs/terms">Terms</a>
        <span aria-hidden="true">•</span>
        <a href="https://bloxwap.github.io/privacy/">Privacy</a>
        <span aria-hidden="true">•</span>
        <a href={assetUrl('/llms.txt')}>llms.txt</a>
      </nav>
    </div>
  </footer>;
}
