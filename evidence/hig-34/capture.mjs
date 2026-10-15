// Captures equivalent production-export screenshots and decoded resource bytes (Chromium via Playwright).
// Usage (repo root, with `bun run docs:preview` serving /font on CAPTURE_URL): node evidence/hig-34/capture.mjs <before|after>
import { chromium } from '../../apps/docs/node_modules/@playwright/test/index.mjs';
import { writeFile } from 'node:fs/promises';

const phase = process.argv[2];
const base = process.env.CAPTURE_URL ?? 'http://127.0.0.1:4120/font/';
const viewports = { desktop: { width: 1280, height: 900 }, mobile: { width: 390, height: 844 } };
const pages = [['home', ''], ['installation', 'docs/installation/'], ['sans', 'docs/families/sans/'], ['character-set', 'docs/character-set/']];
const demos = [['tester', '#tester'], ['glyphs', '#glyphs']];
const browser = await chromium.launch();
const metrics = {};
for (const [vp, size] of Object.entries(viewports)) {
  const context = await browser.newContext({ viewport: size, deviceScaleFactor: 1, reducedMotion: 'reduce' });
  const page = await context.newPage();
  for (const [name, path] of pages) {
    await page.goto(base + path, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `evidence/hig-34/${phase}-${name}-${vp}.png` });
    metrics[`${name}-${vp}`] = await page.evaluate(() => {
      const r = performance.getEntriesByType('resource');
      const sum = (re) => r.filter((e) => re.test(e.name)).reduce((n, e) => n + e.decodedBodySize, 0);
      return { cssBytes: sum(/\.css(\?|$)/), fontBytes: sum(/\.woff2(\?|$)/), jsBytes: sum(/\.js(\?|$)/) };
    });
  }
  await page.goto(base, { waitUntil: 'networkidle' });
  for (const [name, selector] of demos) {
    const el = page.locator(selector);
    await el.scrollIntoViewIfNeeded();
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(1500);
    // Hide the sticky site header so it does not overlap a demo taller than the viewport.
    await el.screenshot({ path: `evidence/hig-34/${phase}-demo-${name}-${vp}.png`, style: '#nd-nav, #nd-subnav { visibility: hidden !important; }' });
  }
  await context.close();
}
await writeFile(`evidence/hig-34/${phase}-capture.json`, JSON.stringify(metrics, null, 2) + '\n');
await browser.close();
console.log(JSON.stringify(metrics));
