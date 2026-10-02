'use client';

import { useEffect, useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { copyText } from './toast';

/** A quiet icon button that copies `text`, with a check mark and a screen-reader status (as in the sfx and chart docs). */
export function CopyTextButton({ text, label = 'Copy', ariaLabel }: { text: string | (() => string); label?: string; ariaLabel?: string }) {
  const [state, setState] = useState<'idle' | 'ok' | 'failed'>('idle');
  useEffect(() => {
    if (state === 'idle') return;
    const timer = window.setTimeout(() => setState('idle'), state === 'ok' ? 2000 : 5000);
    return () => window.clearTimeout(timer);
  }, [state]);
  const name = ariaLabel ?? label;
  return <>
    <button type="button" className="btn btn--ghost btn--icon copy-btn" data-state={state} aria-label={name} title={state === 'ok' ? 'Copied!' : name}
      onClick={async () => setState(await copyText(typeof text === 'function' ? text() : text) ? 'ok' : 'failed')}>
      {state === 'ok' ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
    </button>
    <span role="status" className="sr-only">
      {state === 'ok' ? 'Copied to clipboard.' : state === 'failed' ? 'Could not copy. Select the code to copy it manually.' : ''}
    </span>
  </>;
}
