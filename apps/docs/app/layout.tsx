import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { Provider } from '@/components/provider';
import { basePath, fileUrl, siteUrl, stylesheetHref } from '@/lib/site';
import { homeSocial, socialImagePath, socialMetadata } from '@/lib/social';
import './global.css';

export const metadata: Metadata = {
  metadataBase: new URL(`${siteUrl}${basePath}/`),
  title: { default: 'Bloxwap Font — Sans, Mono & Pixel typefaces', template: '%s · Bloxwap Font' },
  description: 'Bloxwap Font is a free, open-source type system from Bloxwap, Inc.: Bloxwap Sans, a rounded neo-grotesk with 9 weights and italics; Bloxwap Mono, with code ligatures; and Bloxwap Pixel, a variable pixel display face. SIL Open Font License 1.1.',
  icons: { icon: `${basePath}/icon.svg` },
  ...socialMetadata({ ...homeSocial, path: '/', imagePath: socialImagePath() }),
};

export const viewport: Viewport = {
  themeColor: '#0a0a0a',
  colorScheme: 'dark',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en" suppressHydrationWarning className="dark">
    <head>
      {/* The site is set in its own fonts: the same generated stylesheet users can link (see /docs/installation). */}
      <link rel="preload" href={fileUrl('fonts/BloxwapSans/variable/BloxwapSans[wght].woff2')} as="font" type="font/woff2" crossOrigin="" />
      <link rel="stylesheet" href={stylesheetHref} />
    </head>
    <body className="flex min-h-screen flex-col antialiased">
      <Provider>{children}</Provider>
    </body>
  </html>;
}
