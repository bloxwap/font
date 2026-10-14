import { test, expect } from '@playwright/test';
const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify the production export');

test('HIG tokens, install keyboard/copy and variable axes survive migration', async ({ page }) => {
 await page.addInitScript(() => Object.defineProperty(navigator, 'clipboard', {
  value: { writeText: async (text: string) => { (window as typeof window & { copied: string }).copied = text; } },
 }));
 await page.goto(live!);
 expect(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--hig-space-lg').trim())).toBe('1rem');
 await expect(page.locator('.hero .hig-button').first()).toBeVisible();
 const tabs = page.getByRole('tablist', { name: 'Package manager' });
 await tabs.getByRole('tab', { name: 'bun', exact: true }).focus();
 await page.keyboard.press('ArrowRight');
 await expect(tabs.getByRole('tab', { name: 'npm', exact: true })).toBeFocused();
 await page.getByRole('button', { name: 'Copy install command', exact: true }).click();
 expect(await page.evaluate(() => (window as typeof window & { copied: string }).copied)).toBe('npm install @bloxwap/font');
 const tester = page.locator('#tester');
 await tester.getByRole('radio', { name: 'Pixel', exact: true }).click();
 const axis = tester.getByRole('slider', { name: /Roundness/ });
 await axis.focus();
 await axis.press('End');
 await expect(tester.locator('.css-code')).toContainText('100');
 const weight = tester.getByRole('slider', { name: 'Weight', exact: true });
 await weight.focus();
 await weight.press('End');
 await expect(tester.locator('.css-code')).toContainText('900');
 await tester.getByRole('radio', { name: 'Sans', exact: true }).click();
 await tester.getByRole('textbox').fill('A long translation — العربية שָׁלוֹם 日本語 한국어 中文');
 await expect(tester.getByRole('textbox')).toContainText('العربية');
 await page.goto(new URL('docs/cross-platform/', live!).href);
 await expect(page.getByRole('heading', { name: 'Cross-platform typography', exact: true })).toBeVisible();
 await expect(page.locator('body')).toContainText('BloxwapSans-RegularItalic');
});

test('mobile shell keeps navigation, search and deep links', async ({ page }) => {
 await page.setViewportSize({ width: 390, height: 844 });
 await page.goto(new URL('docs/cross-platform/', live!).href);
 const menu = page.getByRole('button', { name: /sidebar|menu/i }).first();
 await menu.click();
 await expect(page.getByRole('link', { name: 'Installation', exact: true }).first()).toBeVisible();
 await page.getByRole('link', { name: 'Installation', exact: true }).first().click();
 await expect(page).toHaveURL(/\/font\/docs\/installation/);
});
