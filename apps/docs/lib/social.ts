import type { Metadata } from 'next';
import { basePath, siteUrl } from './site';

export const socialImageSize = { width: 1200, height: 630 };
export const homeSocial = {
  title: 'Bloxwap Font',
  description: 'Rounded typefaces for interfaces, code and screens — Sans, Mono and Pixel, with Arabic, Armenian, Georgian, Hebrew, Japanese, Korean and Chinese companions. Free and open source under the SIL OFL 1.1.',
};

/** Explicit PNG paths work on GitHub Pages without a running image service. */
export function socialImageSegments(slugs?: string[]): string[] {
  if (!slugs) return ['home.png'];
  return ['docs', ...slugs.slice(0, -1), `${slugs.at(-1) ?? 'index'}.png`];
}

export function socialImagePath(slugs?: string[]): string {
  return `/og/${socialImageSegments(slugs).join('/')}`;
}

export function socialMetadata({ title, description, path, imagePath }: {
  title: string;
  description: string;
  path: string;
  imagePath: string;
}): Pick<Metadata, 'openGraph' | 'twitter' | 'alternates'> {
  const absolute = (pathname: string) => new URL(`${basePath}${pathname}`, siteUrl).href;
  const image = { url: absolute(imagePath), ...socialImageSize, alt: `Bloxwap Font — ${title}` };
  const socialTitle = title === 'Bloxwap Font' ? 'Bloxwap Font — Sans, Mono & Pixel typefaces' : `${title} · Bloxwap Font`;
  return {
    alternates: { canonical: absolute(path) },
    openGraph: {
      type: 'website', locale: 'en_US', siteName: 'Bloxwap Font',
      title: socialTitle, description, url: absolute(path),
      images: [{ ...image, type: 'image/png' }],
    },
    twitter: { card: 'summary_large_image', site: '@bloxwap', title: socialTitle, description, images: [image] },
  };
}
