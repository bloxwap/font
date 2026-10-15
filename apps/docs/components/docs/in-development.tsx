import { Callout } from '@bloxwap/hig-react/status';

/**
 * The HIG warning callout for a family whose fonts are not built yet. Presentational only (no
 * font-data reads), so the unit test renders exactly what the family pages render.
 * announce={false}: this is static page content, not a live status change.
 */
export function InDevelopmentCallout({ name, packs }: { name: string; packs?: string }) {
  return <div className="bw-callout not-prose" role="note">
    <Callout severity="warning" announce={false} title={`${name} is being drawn.`} action={<span className="wip-badge">In development</span>}>
      <p>Its fonts are not part of this release yet{packs ? ` (planned coverage: ${packs})` : ''}. This page fills in automatically from the font data once it is built.</p>
    </Callout>
  </div>;
}
