import { test, expect } from '@playwright/test';
const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL');

test('newer sample wins over delayed character set', async ({page}) => {
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/data/sans.glyphs.json', async route => { await gate; await route.continue(); });
  await page.goto(live!);
  const tester = page.locator('#tester');
  const zero = tester.getByRole('button', {name:/^zero\b/});
  await zero.click(); await expect(zero).toHaveAttribute('aria-pressed','true');
  const sample = tester.locator('select').filter({has:page.locator('option[value="charset"]')});
  await sample.selectOption('charset'); await sample.selectOption('numbers');
  const text = await tester.locator('.t-text').innerText();
  release();
  await expect(page.locator('#glyphs .g-cell').first()).toBeAttached();
  await expect(tester.locator('.t-text')).toHaveText(text, {useInnerText:true});
});

test('companion selection retains a primary keyboard stop and language stays visible', async ({page}) => {
  await page.goto(live!);
  const tester=page.locator('#tester');
  const zero=tester.getByRole('button',{name:/^zero\b/});await zero.click();await expect(zero).toHaveAttribute('aria-pressed','true');
  await tester.getByRole('combobox',{name:'Tester typeface: companion families'}).selectOption('sans-jp');
  await expect(tester.getByRole('radiogroup',{name:'Tester typeface',exact:true}).locator('[tabindex="0"]')).toHaveCount(1);
  await tester.getByRole('radio',{name:'Sans',exact:true}).click();
  await tester.locator('select').filter({has:page.locator('option[value="bg"]')}).selectOption('bg');
  await tester.getByRole('radio',{name:'Pixel',exact:true}).click();
  await expect(tester.locator('select').filter({has:page.locator('option[value="bg"]')})).toHaveValue('bg');
});
