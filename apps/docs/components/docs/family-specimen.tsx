'use client';

import { useState } from 'react';
import { Range, Switch } from '@/components/ui/controls';
import { fontStack, instanceName } from '@/lib/families';
import type { Axis, Instance } from '@/lib/types';

/** Editable specimen with one slider per axis (wght as font-weight, others via font-variation-settings). */
export function FamilySpecimenClient({ name, style, axes, hasItalic, instances, text, small }: {
  name: string; style: string; axes: Axis[]; hasItalic: boolean; instances: Instance[]; text: string; small?: string;
}) {
  const [values, setValues] = useState<Record<string, number>>(() => Object.fromEntries(axes.map((a) => [a.tag, a.default])));
  const [italic, setItalic] = useState(false);
  const wght = values.wght ?? 400;
  const other = axes.filter((a) => a.tag !== 'wght').map((a) => `"${a.tag}" ${values[a.tag]}`).join(', ');
  const css = { fontFamily: fontStack(name, style), fontWeight: wght, fontStyle: italic ? 'italic' : 'normal', fontVariationSettings: other || 'normal' };
  const language = name.endsWith('Arabic') ? 'ar' : name.endsWith('Hebrew') ? 'he'
    : name.endsWith('Armenian') ? 'hy' : name.endsWith('Georgian') ? 'ka' : undefined;
  return <figure className="bw-specimen not-prose" aria-label={`${name} specimen`}>
    <div className="bw-specimen-text" style={css} lang={language} dir="auto" contentEditable suppressContentEditableWarning spellCheck={false} role="textbox" aria-label={`${name} specimen text, editable`}>{text}</div>
    {small && <div className="bw-specimen-text bw-specimen-text--small" style={css} lang={language} dir="auto">{small}</div>}
    <figcaption className="bw-specimen-controls">
      {axes.map((a) => <Range key={a.tag} label={<>{a.name} <code>{a.tag}</code></>} min={a.min} max={a.max} value={values[a.tag] ?? a.default}
        note={a.tag === 'wght' ? instanceName(instances, values.wght ?? 400) : undefined}
        onChange={(v) => setValues((s) => ({ ...s, [a.tag]: v }))} />)}
      {hasItalic && <Switch label="Italic" checked={italic} onChange={setItalic} />}
    </figcaption>
  </figure>;
}
