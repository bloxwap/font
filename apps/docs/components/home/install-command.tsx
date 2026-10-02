'use client';

import { useId, useState } from 'react';
import { CopyTextButton } from '@/components/ui/copy-text-button';

export const PACKAGE = '@bloxwap/font';

const managers = [
  { name: 'bun', command: `bun add ${PACKAGE}` },
  { name: 'npm', command: `npm install ${PACKAGE}` },
  { name: 'pnpm', command: `pnpm add ${PACKAGE}` },
  { name: 'yarn', command: `yarn add ${PACKAGE}` },
];

/** Package-manager tabs and a copyable install command (as on the sfx and chart landing pages). */
export function InstallCommand() {
  const id = useId();
  const [selected, setSelected] = useState(0);
  const { command } = managers[selected]!;

  return <div className="package-install">
    <div className="install-tabs" role="tablist" aria-label="Package manager">
      {managers.map(({ name }, index) => <button
        key={name}
        type="button"
        role="tab"
        id={`${id}-tab-${index}`}
        aria-controls={`${id}-command`}
        aria-selected={selected === index}
        tabIndex={selected === index ? 0 : -1}
        onClick={() => setSelected(index)}
        onKeyDown={(event) => {
          let next: number;
          if (event.key === 'ArrowRight') next = (index + 1) % managers.length;
          else if (event.key === 'ArrowLeft') next = (index + managers.length - 1) % managers.length;
          else if (event.key === 'Home') next = 0;
          else if (event.key === 'End') next = managers.length - 1;
          else return;
          event.preventDefault();
          setSelected(next);
          document.getElementById(`${id}-tab-${next}`)?.focus();
        }}
      >{name}</button>)}
    </div>
    <div className="install-command" role="tabpanel" id={`${id}-command`} aria-labelledby={`${id}-tab-${selected}`} tabIndex={0}>
      <span className="install-prompt" aria-hidden="true">$</span>
      <code>{command}</code>
      <CopyTextButton text={command} ariaLabel="Copy install command" />
    </div>
    <p className="install-platforms">Next.js · Vite · plain CSS · SIL OFL 1.1</p>
  </div>;
}
