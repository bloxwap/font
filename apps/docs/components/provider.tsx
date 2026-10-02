'use client';

import { RootProvider } from 'fumadocs-ui/provider/next';
import type { ReactNode } from 'react';
import StaticSearch from './search';

/** Dark only, like the other Bloxwap sites, with the static Orama search index. */
export function Provider({ children }: { children: ReactNode }) {
  return <RootProvider theme={{ forcedTheme: 'dark' }} search={{ SearchDialog: StaticSearch }}>{children}</RootProvider>;
}
