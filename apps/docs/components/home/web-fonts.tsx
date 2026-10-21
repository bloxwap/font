'use client';

import { useState } from 'react';
import { Spinner } from '@bloxwap/hig-react/status';
import { loadFamily, useAsync } from '@/lib/client-data';
import { fmtBytes } from '@/lib/format';
import { downloadUrl, fileUrl } from '@/lib/site';

/** The file list stays out of the initial HTML and Flight payload until expanded. */
export function WebFonts({ id, count }: { id: string; count: number }) {
  const [opened, setOpened] = useState(false);
  const data = useAsync(() => opened ? loadFamily(id) : Promise.resolve(null), opened ? id : '');
  return <details onToggle={(event) => { if (event.currentTarget.open) setOpened(true); }}>
    <summary>Variable web fonts ({count} WOFF2)</summary>
    {opened && (data === undefined ? <Spinner label="Loading web fonts" />
      : data ? <><ul>{data.files.web.map((w) => <li key={w.path}><a href={fileUrl(w.path)}>{w.name}</a> <span className="l-iso">{fmtBytes(w.bytes)}</span></li>)}</ul>{data.files.zip && <p><a href={downloadUrl(data.files.zip.path)}>Static web fonts in the family zip</a></p>}</>
        : <p role="status">Web font data isn’t available yet.</p>)}
  </details>;
}
