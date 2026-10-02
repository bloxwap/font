import { test, expect, type Page } from '@playwright/test';

const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify a served site');
test.use({ reducedMotion: 'reduce' });

// SC 1.4.12 values from https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html.
const spacing = `* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; }
p { margin-bottom: 2em !important; }`;

async function expectReflow(page: Page) {
  const dimensions = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }));
  expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport + 2);
  // Preformatted code and the large price specimen have deliberate local scrolling.
  // Descriptive text, feature labels and actions must remain readable without clipping.
  const clipped = await page.locator('.btn, .seg button, .feat span, .l-sample, .hw-line, .lg-g, .ld-text, .wf-text, .bw-specimen-text, .gi-meta > p, .bw-coverage-row > span').evaluateAll((elements) =>
    elements.filter((element) => element.clientWidth > 0 && (
      element.scrollWidth > element.clientWidth + 2 || (
        ['hidden', 'clip'].includes(getComputedStyle(element).overflowY) && element.scrollHeight > element.clientHeight + 2
      )
    )).map((element) => `${element.className}: ${element.textContent?.slice(0, 80)}`),
  );
  expect(clipped).toEqual([]);
}

for (const width of [320, 640, 1280]) {
  test(`content reflows at ${width}px with user spacing and a replacement font`, async ({ page }) => {
    // 320 CSS px represents the reflow viewport of a 1280px browser at 400% zoom.
    // This checks layout; it does not exercise the browser's zoom controls.
    await page.setViewportSize({ width, height: 900 });
    await page.goto(live!);
    await page.addStyleTag({ content: `${spacing}\n* { font-family: Georgia, serif !important; }` });
    await expect(page.locator('#tester .feat').first()).toBeVisible();
    await expectReflow(page);
    for (const view of ['Waterfall', 'Weights']) {
      await page.locator('#tester').getByRole('tab', { name: view, exact: true }).click();
      await expectReflow(page);
    }
    for (const path of ['docs/usage/', 'docs/families/sans/']) {
      await page.goto(new URL(path, live!).href);
      await page.addStyleTag({ content: `${spacing}\n* { font-family: Georgia, serif !important; }` });
      await expectReflow(page);
    }
  });
}

test('text remains usable at 200% root font size', async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 900 });
  await page.goto(live!);
  await page.addStyleTag({ content: 'html { font-size: 200% !important; }' });
  await expectReflow(page);
});

test('symbol controls have meaningful names and work with the keyboard', async ({ page }) => {
  await page.goto(live!);
  const icons = page.locator('.home button, .home a, .home [role="radio"]');
  for (const control of await icons.all()) {
    if (await control.locator('svg').count()) {
      await expect(control).toHaveAccessibleName(/\p{L}/u);
      await expect(control.locator('svg').first()).toHaveAttribute('aria-hidden', 'true');
    }
  }
  const alignment = page.getByRole('radiogroup', { name: 'Alignment' });
  await alignment.getByRole('radio', { name: 'Align left', exact: true }).focus();
  await page.keyboard.press('ArrowRight');
  await expect(alignment.getByRole('radio', { name: 'Align center', exact: true })).toBeFocused();
  await expect(alignment.getByRole('radio', { name: 'Align center', exact: true })).toBeChecked();

  const price = page.getByLabel('Bitcoin price specimen, horizontally scrollable');
  await price.focus();
  await expect(price).toBeFocused();
});
