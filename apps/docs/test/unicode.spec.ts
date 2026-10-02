import { test, expect } from '@playwright/test';

const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify a served site');

test.beforeEach(async ({ page }) => {
  // Capture the app's clipboard payload without engine-specific permission prompts.
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: async (text: string) => {
        (window as typeof window & { copiedText: string }).copiedText = text;
      } },
    });
  });
});

const cases = [
  { title: 'encoded Greek alpha', family: 'Sans', query: 'U+03B1', source: 'α', tester: 'ααα Α',
    label: 'Greek small letter alpha, U+03B1', feature: null },
  { title: 'Greek mu sharing the micro-sign outline', family: 'Sans', query: 'U+03BC', source: 'μ', tester: 'μμμ Μ',
    label: 'Greek small letter mu, U+03BC', feature: null },
  { title: 'micro sign sharing the Greek-mu outline', family: 'Sans', query: 'U+00B5', source: 'µ', tester: 'µµµ Μ',
    label: 'Micro sign, U+00B5', feature: null },
  { title: 'stylistic alternate', family: 'Sans', query: 'a.ss01', source: 'a', tester: 'aaa A',
    label: 'Latin small letter a, alternate via ss01', feature: 'ss01' },
  { title: 'Mono arrow ligature', family: 'Mono', query: 'hyphen_greater.code', source: '->', tester: '->->->',
    label: 'Hyphen-minus, Greater-than sign, ligature via calt', feature: 'calt' },
];

for (const sample of cases) {
  test(`${sample.title}: copy and tester preserve source Unicode`, async ({ page }) => {
    await page.goto(live!);
    const glyphs = page.locator('#glyphs');
    const tester = page.locator('#tester');
    if (sample.feature === 'calt') {
      await tester.getByRole('radiogroup', { name: 'Tester typeface', exact: true })
        .getByRole('radio', { name: 'Mono', exact: true }).click();
      const calt = tester.getByRole('group', { name: 'OpenType features', exact: true })
        .getByRole('button', { name: /^calt\b/ });
      await expect(calt).toHaveAttribute('aria-pressed', 'true');
      await calt.click();
      await expect(calt).toHaveAttribute('aria-pressed', 'false');
      await expect(tester.locator('.t-text')).toHaveCSS('font-feature-settings', '"calt" 0');
    }
    await glyphs.getByRole('radiogroup', { name: 'Glyph browser typeface', exact: true })
      .getByRole('radio', { name: sample.family, exact: true }).click();
    await glyphs.getByRole('searchbox', { name: 'Search glyphs' }).fill(sample.query);
    const cell = glyphs.getByRole('option', { name: sample.label, exact: true });
    await expect(cell).toBeVisible();
    await cell.click();
    await expect.poll(() => page.evaluate(() => (window as typeof window & { copiedText: string }).copiedText))
      .toBe(sample.source);
    await page.evaluate(() => { (window as typeof window & { copiedText: string }).copiedText = ''; });
    await glyphs.getByRole('button', { name: 'Copy character', exact: true }).click();
    await expect.poll(() => page.evaluate(() => (window as typeof window & { copiedText: string }).copiedText))
      .toBe(sample.source);
    await glyphs.getByRole('button', { name: 'Use in tester', exact: true }).click();
    await expect(tester.locator('.t-text')).toHaveText(sample.tester);
    if (sample.feature) {
      await expect(tester.getByRole('group', { name: 'OpenType features', exact: true })
        .getByRole('button', { name: new RegExp(`^${sample.feature}\\b`) })).toHaveAttribute('aria-pressed', 'true');
      if (sample.feature === 'ss01') await expect(tester.locator('.t-text')).toHaveCSS('font-feature-settings', '"ss01"');
      if (sample.feature === 'calt') await expect(tester.locator('.t-text')).toHaveCSS('font-feature-settings', 'normal');
    }
  });
}

test('Unicode names are searchable and unreachable glyphs cannot be copied', async ({ page }) => {
  await page.goto(live!);
  const glyphs = page.locator('#glyphs');
  await glyphs.getByRole('searchbox', { name: 'Search glyphs' }).fill('Greek small letter alpha');
  await expect(glyphs.getByRole('option', { name: 'Greek small letter alpha, U+03B1', exact: true })).toBeVisible();
  await glyphs.getByRole('searchbox', { name: 'Search glyphs' }).fill('.notdef');
  await expect(glyphs.getByRole('listbox').getByRole('option')).toHaveCount(1);
  await expect(glyphs.getByRole('button', { name: 'Copy character', exact: true })).toBeDisabled();
  await expect(glyphs.getByRole('button', { name: 'Use in tester', exact: true })).toBeDisabled();
});

test('shared mu glyph offers separately named Unicode choices', async ({ page }) => {
  await page.goto(live!);
  const glyphs = page.locator('#glyphs');
  await glyphs.getByRole('searchbox', { name: 'Search glyphs' }).fill('mu');
  await expect(glyphs.getByRole('option', { name: 'Greek small letter mu, U+03BC', exact: true })).toBeVisible();
  await expect(glyphs.getByRole('option', { name: 'Micro sign, U+00B5', exact: true })).toBeVisible();
});
