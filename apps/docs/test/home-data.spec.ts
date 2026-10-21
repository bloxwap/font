import { test, expect } from '@playwright/test';

const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify a served site');

test('home payload stays below 250 KB and feature details load without resetting toggles', async ({ page, request }) => {
  const response = await request.get(live!);
  expect(Buffer.byteLength(await response.text())).toBeLessThan(250_000);
  const familyRequests: string[] = [];
  page.on('request', (request) => {
    if (/\/data\/[^/.]+\.json$/.test(request.url()) && !request.url().endsWith('/languages.json')) familyRequests.push(request.url());
  });
  let release!: () => void;
  const ready = new Promise<void>((resolve) => { release = resolve; });
  await page.route('**/data/sans.json', async (route) => { await ready; await route.continue(); });
  await page.goto(live!, { waitUntil: 'networkidle' });
  expect(familyRequests).toEqual([]);
  const zero = page.locator('#tester').getByRole('button', { name: /^zero\b/ });
  // Keyboard focus requests tooltip details, while the feature remains usable during the fetch.
  await zero.focus();
  await page.keyboard.press('Enter');
  await expect(zero).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#tester .css-code')).toContainText('"zero" 1');
  release();
  await expect(zero).toHaveAttribute('title', /Affects:/);
  await expect(zero).toHaveAttribute('aria-pressed', 'true');
  expect(familyRequests).toHaveLength(1);
});

test('expanding web fonts loads the complete file list once from public JSON', async ({ page, request }) => {
  const response = await request.get(new URL('data/sans.json', live!).href);
  const data = await response.json();
  let requests = 0;
  await page.route('**/data/sans.json', async (route) => { requests++; await route.continue(); });
  await page.goto(live!, { waitUntil: 'networkidle' });
  expect(requests).toBe(0);
  const details = page.locator('#download .dl-card').first().locator('details');
  await expect(details.locator('a')).toHaveCount(0);
  await details.locator('summary').click();
  await expect(details.locator('li a')).toHaveCount(data.files.web.length);
  for (const file of data.files.web) {
    const link = details.getByRole('link', { name: file.name, exact: true });
    await expect(link).toHaveAttribute('href', new RegExp(file.path.split('/').map(encodeURIComponent).join('/').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  await details.locator('summary').click();
  await details.locator('summary').click();
  await expect(details.locator('li a')).toHaveCount(data.files.web.length);
  expect(requests).toBe(1);
});

test('missing web-font JSON leaves the download card usable', async ({ page }) => {
  await page.route('**/data/sans.json', (route) => route.fulfill({ status: 404 }));
  await page.goto(live!);
  const card = page.locator('#download .dl-card').first();
  await card.locator('summary').click();
  await expect(card.getByRole('status')).toHaveText('Web font data isn’t available yet.');
  await expect(card.getByRole('link', { name: /Download Sans/ })).toBeVisible();
});
