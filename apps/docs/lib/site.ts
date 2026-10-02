import { FONT_VERSION } from './font-version';

export const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? '';
export const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://bloxwap.github.io';
export const repository = 'https://github.com/bloxwap/font';
export const productName = 'Bloxwap Font';

/** For fetches and plain asset URLs. Next Link already applies basePath. */
export function assetUrl(path: string): string { return `${basePath}${path}`; }

/**
 * A file under public/ by its data-JSON path (e.g. "fonts/BloxwapSans/variable/BloxwapSans[wght].woff2"):
 * base path, percent-encoded brackets, and the font cache-busting version.
 */
export function fileUrl(path: string, { version = true } = {}): string {
  const encoded = path.split('/').map(encodeURIComponent).join('/');
  return `${basePath}/${encoded}${version ? `?v=${FONT_VERSION}` : ''}`;
}

/** Absolute URL of a public file on the deployed site (for copy-paste snippets). */
export function publicUrl(path: string): string {
  const encoded = path.split('/').map(encodeURIComponent).join('/');
  return `${siteUrl}${basePath || '/font'}/${encoded}`;
}

/**
 * A download zip by its data-JSON path (e.g. "downloads/BloxwapSans.zip"). The zips are GitHub Release assets, not
 * committed files: `bun run fonts:build` writes them to apps/docs/public/downloads (ignored), and they are uploaded to
 * the release with `bun run fonts:release`. `latest/download` always resolves to the newest release.
 */
export function downloadUrl(path: string): string {
  return `${repository}/releases/latest/download/${encodeURIComponent(path.split('/').pop()!)}`;
}

export const stylesheetHref = `${basePath}/bloxwap-font.css?v=${FONT_VERSION}`;
