'use client';

import { useEffect, useState } from 'react';
import { assetUrl } from './site';
import type { FamilyData, Glyph, Languages } from './types';

const cache = new Map<string, Promise<unknown>>();

function load<T>(path: string): Promise<T | null> {
  if (!cache.has(path)) {
    cache.set(path, fetch(assetUrl(path), { cache: 'no-cache' })
      .then((response) => (response.ok ? response.json() : null))
      .catch(() => null));
  }
  return cache.get(path) as Promise<T | null>;
}

export const loadFamily = (id: string) => load<FamilyData>(`/data/${id}.json`);
/** Every language across the collection (public/data/languages.json). */
export const loadLanguages = () => load<Languages>('/data/languages.json');
export const loadGlyphs = (id: string) => load<{ id: string; glyphs: Glyph[] }>(`/data/${id}.glyphs.json`).then((d) => d?.glyphs ?? null);

/** Fetch-on-demand JSON with a loading state: undefined while loading, null when missing. */
export function useAsync<T>(loader: () => Promise<T | null>, key: string): T | null | undefined {
  const [state, setState] = useState<{ key: string; value: T | null } | null>(null);
  useEffect(() => {
    let live = true;
    loader().then((value) => { if (live) setState({ key, value }); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state?.key === key ? state.value : undefined;
}

/** Hand text to the type tester: on the home page directly, elsewhere by navigating to it. */
export interface TesterRequest { family?: string; text?: string; lang?: string; feature?: string }
export const TESTER_EVENT = 'bw-tester';

export function sendToTester(request: TesterRequest): void {
  if (document.getElementById('tester')) {
    window.dispatchEvent(new CustomEvent<TesterRequest>(TESTER_EVENT, { detail: request }));
    return;
  }
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(request)) if (value) params.set(key, value);
  window.location.href = `${assetUrl('/')}?${params}#tester`;
}
