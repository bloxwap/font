'use client';

import { useEffect, useState } from 'react';

const EVENT = 'bw-toast';

/** Show a short status message in the page's <Toaster /> (announced politely to screen readers). */
export function toast(message: string): void {
  window.dispatchEvent(new CustomEvent<string>(EVENT, { detail: message }));
}

export function Toaster() {
  const [message, setMessage] = useState('');
  const [show, setShow] = useState(false);
  useEffect(() => {
    let timer = 0;
    const onToast = (event: Event) => {
      setMessage((event as CustomEvent<string>).detail);
      setShow(true);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setShow(false), 1800);
    };
    window.addEventListener(EVENT, onToast);
    return () => { window.removeEventListener(EVENT, onToast); window.clearTimeout(timer); };
  }, []);
  return <div className="toast" role="status" aria-live="polite" data-show={show}>{message}</div>;
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch { ok = false; }
    area.remove();
    return ok;
  }
}
