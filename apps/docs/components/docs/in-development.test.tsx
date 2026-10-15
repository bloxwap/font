import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { renderToStaticMarkup } from 'react-dom/server';
import { InDevelopmentCallout } from './in-development';

// No family is in development today (all ten pages are built), so this is the fixture that runs
// the HIG Callout path InDevelopment uses, against the vendored @bloxwap/hig-react package.
const html = renderToStaticMarkup(<InDevelopmentCallout name="Bloxwap Sans Thai" packs="Thai + Lao" />);

test('renders a HIG warning callout inside a single static note', () => {
  assert.match(html, /^<div class="bw-callout not-prose" role="note"><section class="hig-surface" data-severity="warning">/);
  assert.equal(html.match(/role="/g)?.length, 1, 'announce={false} must not add a status/alert live region');
});

test('titles the family, keeps the in-development badge and planned coverage', () => {
  assert.match(html, /<strong>Bloxwap Sans Thai is being drawn\.<\/strong>/);
  assert.match(html, /<span class="wip-badge">In development<\/span>/);
  assert.match(html, /planned coverage: Thai \+ Lao/);
});

test('omits planned coverage when the catalog lists no packs', () => {
  assert.doesNotMatch(renderToStaticMarkup(<InDevelopmentCallout name="Bloxwap Sans" />), /planned coverage/);
});
