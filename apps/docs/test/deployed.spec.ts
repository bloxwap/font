import { test, expect } from '@playwright/test';
// DOCS_URL=http://localhost:3904/font/ (npm run preview) or the deployed https://bloxwap.github.io/font/
const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify a served site');

test('fonts, tester, glyph browser, languages, search and public resources', async ({ page, request }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(live!);

  // The site is set in its own fonts, loaded from the generated stylesheet.
  const fonts = await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(['Bloxwap Sans', 'Bloxwap Mono', 'Bloxwap Pixel'].map((family) => document.fonts.load(`400 16px "${family}"`)));
    return [...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family);
  });
  for (const family of ['Bloxwap Sans', 'Bloxwap Mono', 'Bloxwap Pixel']) expect(fonts).toContain(family);

  // Tester: toggle a feature and see it in the CSS readout; switch to Pixel and get the ROND axis.
  const tester = page.locator('#tester');
  await tester.getByRole('button', { name: /^zero/ }).click();
  await expect(tester.locator('.css-code')).toContainText('"zero" 1');
  await tester.getByRole('radio', { name: 'Pixel' }).click();
  await expect(tester.getByRole('slider', { name: /Roundness/ })).toBeVisible();
  await tester.getByRole('tab', { name: 'Waterfall' }).click();
  await expect(tester.locator('.wf-row')).toHaveCount(12);

  // Glyph browser: search by code point.
  const glyphs = page.locator('#glyphs');
  await glyphs.getByRole('searchbox').fill('U+00E9');
  await expect(glyphs.locator('.g-cell')).toHaveCount(1);
  await expect(glyphs.locator('.gi-meta h3')).toHaveText('eacute');

  // Languages: a card loads its sample into the tester.
  await page.locator('#languages .l-card').first().click();
  await expect(page.locator('.t-text')).toHaveAttribute('lang', /.+/);

  // Docs search uses the static index.
  await page.goto(new URL('docs/', live!).href);
  await page.getByRole('button', { name: /Search/ }).first().click();
  await page.getByRole('combobox').fill('unicode-range');
  await expect(page.getByRole('dialog')).toContainText(/script/i);

  for (const path of ['sitemap.xml', 'llms.txt', 'og/home.png', 'search.json', 'bloxwap-font.css', 'data/index.json', 'OFL.txt']) {
    const response = await request.get(new URL(path, live!).href);
    expect(response.ok(), path).toBe(true);
  }
  expect(errors).toEqual([]);
});
