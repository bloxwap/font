import { test, expect } from '@playwright/test';
// HIG #34: the docs consume the published @bloxwap/hig-* packages instead of copied CSS/primitives.
const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify the production export');

test('package CSS, HIG copy buttons and loading/empty states', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.addInitScript(() => Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: async (text: string) => { (window as typeof window & { copied: string }).copied = text; } },
  }));
  await page.goto(live!);

  // Token and control CSS come from the packages (the source-reconciliation roles only exist in the packaged tokens).
  const root = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    return { action: style.getPropertyValue('--hig-action').trim(), source: style.getPropertyValue('--hig-source-background').trim() };
  });
  expect(root.action).not.toBe('');
  expect(root.source).not.toBe('');
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#0a0a0a');

  // Copy controls are HIG ghost IconButtons with a full 48px target, keyboard operable, with a polite status.
  const copy = page.getByRole('button', { name: 'Copy install command', exact: true });
  await expect(copy).toHaveAttribute('data-intent', 'ghost');
  expect((await copy.boundingBox())!.height).toBeGreaterThanOrEqual(48);
  await copy.focus();
  await page.keyboard.press('Enter');
  expect(await page.evaluate(() => (window as typeof window & { copied: string }).copied)).toBe('bun add @bloxwap/font');
  await expect(page.locator('.package-install [role="status"]')).toHaveText('Copied to clipboard.');

  // Link-buttons share the HIG intents.
  await expect(page.locator('.hero a.hig-button[data-intent="primary"]').first()).toBeVisible();
  await expect(page.locator('.hero a.hig-button[data-intent="secondary"]')).toBeVisible();

  // Languages: the HIG EmptyState replaces the hand-built empty card.
  const languages = page.locator('#languages');
  await languages.getByRole('searchbox').fill('zzzz-no-such-language');
  await expect(languages.getByRole('heading', { name: 'No matches', exact: true })).toBeVisible();
  await expect(languages.locator('.hig-surface')).toContainText('Try another name or ISO 639-3 code.');

  // Glyph inspector actions are HIG secondary Buttons.
  const glyphs = page.locator('#glyphs');
  await expect(glyphs.getByRole('button', { name: 'Copy character', exact: true })).toHaveAttribute('data-intent', 'secondary');
  expect(errors).toEqual([]);
});

test('keyboard search opens the static index and deep-links under the base path', async ({ page }) => {
  await page.goto(new URL('docs/', live!).href, { waitUntil: 'networkidle' });
  // Fumadocs registers its ⌘K / Ctrl+K hotkey after hydration; retry until the dialog is open.
  await expect(async () => {
    await page.keyboard.press('ControlOrMeta+k');
    await expect(page.getByRole('combobox')).toBeVisible({ timeout: 1000 });
  }).toPass({ timeout: 15_000 });
  const input = page.getByRole('combobox');
  await expect(input).toBeFocused();
  await input.fill('variable');
  const dialog = page.getByRole('dialog');
  await expect(dialog.getByRole('option').first()).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/font\/docs\//);
});

for (const path of ['', 'docs/installation/', 'docs/character-set/']) {
  test(`390px mobile layout has no horizontal scroll: /${path}`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(new URL(path, live!).href);
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });
}
