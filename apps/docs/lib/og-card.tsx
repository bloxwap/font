import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { ImageResponse } from 'next/og';
import { getTotals } from './font-data';
import { fmtNum } from './format';
import { socialImageSize } from './social';

// Modeled on GitHub's repository cards, in dark mode (as on the sfx docs): black canvas, title, muted
// description, the logo tile, a stats row, and the Bloxwap brand palette along the bottom. Set in
// Bloxwap Sans itself, read from the static TTFs in the distribution (apps/docs/assets/og, copied there by the font build).
const ink = '#f5f7fa';
const muted = '#a1a1a1';
const bar: [color: string, share: number][] = [['#00ff3f', 62], ['#35b5ff', 14], ['#b300ff', 10], ['#ff479c', 8], ['#fffb38', 6]];
const ttf = (style: string) => readFile(join(process.cwd(), 'assets', 'og', `BloxwapSans-${style}.ttf`));
const fonts = Promise.all([ttf('SemiBold'), ttf('Black')]);

const icons: Record<string, string[]> = {
  families: ['M4 7V4h16v3', 'M9 20h6', 'M12 4v16'],
  glyphs: ['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M14 14h7v7h-7z', 'M3 14h7v7H3z'],
  characters: ['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M14 14h7v7h-7z', 'M3 14h7v7H3z'],
  scripts: ['M4 7h16', 'M4 12h10', 'M4 17h13'],
  languages: ['M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z', 'M2 12h20', 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'],
  license: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'],
  docs: ['M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20'],
};

function Icon({ name }: { name: string }) {
  return <svg width={34} height={34} viewBox="0 0 24 24" fill="none" stroke={muted} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    {icons[name].map((d) => <path key={d} d={d} />)}
  </svg>;
}

function clamp(text: string, max: number): string {
  const points = [...text.trim()];
  return points.length > max ? `${points.slice(0, max - 1).join('')}…` : points.join('');
}

export async function renderSocialCard(options: {
  title: string;
  description: string;
  category: string;
  home?: boolean;
}): Promise<ImageResponse> {
  const [semibold, black] = await fonts;
  const totals = getTotals();
  const stats: [icon: string, value: string, label: string][] = [
    ['families', fmtNum(totals.families || 3), 'Families'],
    ['scripts', totals.scripts.length ? fmtNum(totals.scripts.length) : '—', 'Scripts'],
    ['characters', totals.characters ? fmtNum(totals.characters) : '—', 'Characters'],
    ['languages', totals.languages ? fmtNum(totals.languages) : '—', 'Languages'],
  ];
  const title = clamp(options.title, 60);
  const description = clamp(options.description, 150);
  const fontSize = options.home || title.length <= 20 ? 84 : title.length <= 34 ? 72 : 60;

  return new ImageResponse(
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', background: '#0a0a0a', color: ink, fontFamily: 'Bloxwap Sans' }}>
      <div style={{ display: 'flex', flex: 1, padding: '76px 80px 0' }}>
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, paddingRight: 64 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', fontSize, lineHeight: 1.08, letterSpacing: -2 }}>
            {options.home
              ? <><span style={{ fontWeight: 600, color: muted }}>bloxwap/</span><span style={{ fontWeight: 900 }}>font</span></>
              : <span style={{ fontWeight: 900 }}>{title}</span>}
          </div>
          <div style={{ display: 'flex', marginTop: 28, fontSize: 32, fontWeight: 600, lineHeight: 1.4, color: muted }}>{description}</div>
        </div>
        <svg width={200} height={200} viewBox="0 0 100 100">
          <rect width="100" height="100" rx="22.37" fill="#00ff3f" />
          <g fill="none" stroke="#0a0a0a" strokeWidth="16" strokeLinecap="round">
            <path d="M25 75L75 25" /><path d="M24 24L35 35" /><path d="M65 65L76 76" />
          </g>
        </svg>
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 56, padding: '0 80px 52px' }}>
        {options.home
          ? stats.map(([icon, value, label]) => <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 34, fontWeight: 600 }}><Icon name={icon} />{value}</div>
            <div style={{ display: 'flex', fontSize: 26, fontWeight: 600, color: muted }}>{label}</div>
          </div>)
          : <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 30, fontWeight: 600, color: muted }}>
            <Icon name="docs" /><span style={{ color: ink }}>bloxwap/font</span><span>·</span><span>{options.category}</span>
          </div>}
      </div>
      <div style={{ display: 'flex', height: 24 }}>
        {bar.map(([color, share]) => <div key={color} style={{ display: 'flex', flex: share, background: color }} />)}
      </div>
    </div>,
    {
      ...socialImageSize,
      fonts: [
        { name: 'Bloxwap Sans', data: semibold, weight: 600, style: 'normal' },
        { name: 'Bloxwap Sans', data: black, weight: 900, style: 'normal' },
      ],
    },
  );
}
