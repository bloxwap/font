import { chromium } from '../apps/docs/node_modules/@playwright/test/index.mjs';
import { writeFile, stat, readdir, readFile } from 'node:fs/promises';
const phase = process.argv[2];
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
const page = await browser.newPage();
const measurements = {};
for (const [name, width, path] of [['home', 1280, ''], ['docs', 1280, 'docs/installation/'], ['mobile', 390, '']]) {
 await page.setViewportSize({width,height:900});
 await page.goto(`${process.env.CAPTURE_URL ?? 'http://127.0.0.1:43914/font/'}${path}`);
 await page.evaluate(() => document.fonts.ready);
 // Include route prefetches consistently in decoded resource measurements.
 await page.waitForTimeout(2000);
 await page.screenshot({path:`evidence/${phase}-${name}.png`});
 measurements[name] = await page.evaluate(() => ({cssBytes:performance.getEntriesByType('resource').filter(e=>e.name.includes('.css')).reduce((n,e)=>n+e.decodedBodySize,0),fontBytes:performance.getEntriesByType('resource').filter(e=>e.name.includes('.woff2')).reduce((n,e)=>n+e.decodedBodySize,0), runtimeBytes:performance.getEntriesByType('resource').filter(e=>e.name.includes('.js')).reduce((n,e)=>n+e.decodedBodySize,0)}));
}
await writeFile(`evidence/${phase}-metrics.json`, JSON.stringify(measurements,null,2)+'\n');
await browser.close();
