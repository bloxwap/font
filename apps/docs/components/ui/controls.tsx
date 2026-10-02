'use client';

import { useId, useRef, type CSSProperties, type KeyboardEvent, type ReactNode } from 'react';
import NumberFlow, { type Format } from '@number-flow/react';
import { QUICK_ROLL } from '@/lib/number-flow';

/**
 * A labeled range slider with the filled track (the --p custom property) and a live readout: the value rolls with
 * NumberFlow (`format` and `suffix` shape it), and `note` follows it as plain text (e.g. the instance name "Regular").
 */
export function Range({ label, value, min, max, step = 1, onChange, format, suffix, note, className }: {
  label: ReactNode; value: number; min: number; max: number; step?: number;
  onChange: (value: number) => void; format?: Format; suffix?: string; note?: ReactNode; className?: string;
}) {
  const id = useId();
  const p = `${((value - min) / (max - min || 1)) * 100}%`;
  return <div className={`ctl ${className ?? ''}`}>
    <span className="ctl-row"><label htmlFor={id}>{label}</label><output htmlFor={id}><NumberFlow value={value} locales="en-US" format={format} suffix={suffix} transformTiming={QUICK_ROLL} spinTiming={QUICK_ROLL} />{note ? <> {note}</> : null}</output></span>
    <input id={id} className="range" type="range" min={min} max={max} step={step} value={value}
      style={{ '--p': p } as CSSProperties} onChange={(e) => onChange(Number(e.target.value))} />
  </div>;
}

export function Switch({ label, checked, onChange, disabled, title }: {
  label: ReactNode; checked: boolean; onChange: (checked: boolean) => void; disabled?: boolean; title?: string;
}) {
  return <label className="switch" title={title}>
    <input type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
    <span className="switch-ui" aria-hidden="true" />
    <span className="switch-label">{label}</span>
  </label>;
}

export interface SegOption<T extends string> { value: T; label: ReactNode; ariaLabel?: string; title?: string }

/** Radio group (or tablist) of pill buttons with roving arrow-key navigation. */
export function Segmented<T extends string>({ label, options, value, onChange, small, role = 'radio', controls, className }: {
  label: string; options: SegOption<T>[]; value: T; onChange: (value: T) => void; small?: boolean;
  role?: 'radio' | 'tab'; controls?: (value: T) => string; className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const step = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const index = options.findIndex((o) => o.value === value);
    const next = options[(index + step + options.length) % options.length]!;
    onChange(next.value);
    requestAnimationFrame(() => ref.current?.querySelector<HTMLButtonElement>(`[data-value="${next.value}"]`)?.focus());
  }
  return <div ref={ref} className={`seg${small ? ' seg--sm' : ''} ${className ?? ''}`} role={role === 'tab' ? 'tablist' : 'radiogroup'} aria-label={label} onKeyDown={onKeyDown}>
    {options.map((o) => {
      const on = o.value === value;
      return <button key={o.value} type="button" data-value={o.value} role={role} tabIndex={on ? 0 : -1}
        aria-checked={role === 'radio' ? on : undefined} aria-selected={role === 'tab' ? on : undefined}
        aria-controls={controls?.(o.value)} aria-label={o.ariaLabel} title={o.title}
        onClick={() => onChange(o.value)}>{o.label}</button>;
    })}
  </div>;
}

export interface FamilyOption { id: string; name: string; style: string; companion: boolean }

/**
 * Sans / Mono / Pixel as a segmented control, plus a select for companion families when any are built.
 * `all` adds a leading option (value 'all') for views that can show the whole collection.
 */
export function FamilyPicker({ label, families, value, onChange, all }: {
  label: string; families: FamilyOption[]; value: string; onChange: (id: string) => void; all?: string;
}) {
  const primary = [...(all ? [{ id: 'all', name: all, style: 'sans', companion: false }] : []), ...families.filter((f) => !f.companion)];
  const companions = families.filter((f) => f.companion);
  const companionValue = companions.some((f) => f.id === value) ? value : '';
  return <div className="family-picker">
    <Segmented label={label} value={primary.some((f) => f.id === value) ? value : ('' as string)} onChange={onChange}
      options={primary.map((f) => ({ value: f.id, label: f.name.replace(/^Bloxwap /, '') }))} />
    {companions.length > 0 && <select aria-label={`${label}: companion families`} value={companionValue} onChange={(e) => e.target.value && onChange(e.target.value)}>
      <option value="">More scripts…</option>
      {companions.map((f) => <option key={f.id} value={f.id}>{f.name.replace(/^Bloxwap /, '')}</option>)}
    </select>}
  </div>;
}
