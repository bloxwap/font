import { test, expect } from '@playwright/test';

const live = process.env.DOCS_URL;
test.skip(!live, 'Set DOCS_URL to verify a served site');

const scripts = [
  { id: 'arabic', name: 'Arabic', sample: 'السَّلَامُ', lang: 'ar', italic: false },
  { id: 'armenian', name: 'Armenian', sample: 'Հայաստան', lang: 'hy', italic: true },
  { id: 'georgian', name: 'Georgian', sample: 'ქართული ᲥᲐᲠᲗᲣᲚᲘ', lang: 'ka', italic: true },
  { id: 'hebrew', name: 'Hebrew', sample: 'שָׁלוֹם עוֹלָם', lang: 'he', italic: false },
];

for (const script of scripts) {
  test(`${script.name}: real fonts, specimens and downloads`, async ({ page, request }) => {
    await page.goto(new URL(`docs/families/sans-${script.id}/`, live!).href);
    await expect(page.locator('.bw-callout-wip')).toHaveCount(0);
    const sans = page.getByRole('textbox', { name: `Bloxwap Sans ${script.name} specimen text, editable` });
    await expect(sans).toBeVisible();
    // Hebrew and Arabic specimens infer direction from their editable content.
    if (script.id === 'hebrew') {
      await expect(sans).toHaveAttribute('lang', script.lang);
      await expect(sans).toHaveAttribute('dir', 'auto');
      await expect(sans).toHaveCSS('direction', 'rtl');
    }
    for (const style of ['Sans', 'Mono']) {
      const family = `Bloxwap ${style} ${script.name}`;
      const loaded = await page.evaluate(async ({ family, sample }) => {
        const faces = await document.fonts.load(`400 32px "${family}"`, sample);
        const italics = await document.fonts.load(`italic 400 32px "Bloxwap ${family.includes('Mono') ? 'Mono' : 'Sans'}"`, sample);
        return { faces: faces.map((f) => ({ family: f.family.replaceAll('"', ''), status: f.status })),
          italics: italics.map((f) => f.status) };
      }, { family, sample: script.sample });
      expect(loaded.faces).toContainEqual({ family, status: 'loaded' });
      expect(loaded.italics.length).toBeGreaterThan(0);
      expect(loaded.italics.every((s) => s === 'loaded')).toBe(true);
      const data = await request.get(new URL(`data/${style.toLowerCase()}-${script.id}.json`, live!).href);
      expect(data.ok()).toBe(true);
      expect((await data.json()).hasItalic).toBe(script.italic);
      const zip = await request.get(`https://github.com/bloxwap/font/releases/latest/download/Bloxwap${style}${script.name}.zip`);
      expect(zip.ok()).toBe(true);
      expect((await zip.body()).subarray(0, 2).toString()).toBe('PK');
    }
    if (script.id !== 'arabic') {
      await expect(page.getByRole('textbox', { name: `Bloxwap Mono ${script.name} specimen text, editable` })).toBeVisible();
    }
    if (script.italic) {
      await page.locator('.bw-specimen').first().locator('label.switch').click();
      await expect(sans).toHaveCSS('font-style', 'italic');
    }
    if (process.env.SCRIPT_SCREENSHOTS) {
      await page.screenshot({ path: `${process.env.SCRIPT_SCREENSHOTS}/${script.id}-page.png`, fullPage: true });
    }
  });
}
