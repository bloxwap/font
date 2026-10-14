import { webkit } from '../apps/docs/node_modules/@playwright/test/index.mjs';
const browser = await webkit.launch();
const page = await browser.newPage({viewport:{width:320,height:900},reducedMotion:'reduce'});
for (const font of ['Georgia','serif','Liberation Serif','Times New Roman','DejaVu Serif']) {
 await page.goto('http://127.0.0.1:43914/font/');
 await page.addStyleTag({content:`* { line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important;font-family:'${font}',serif !important;} p {margin-bottom:2em !important;}`});
 console.log(font, await page.evaluate(()=>({width:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('body *')].filter(e=>{const b=e.getBoundingClientRect();let p=e.parentElement;while(p){if(['hidden','clip','auto','scroll'].includes(getComputedStyle(p).overflowX))return false;p=p.parentElement;} return b.width>0 && b.right>322 && getComputedStyle(e).position!=='fixed';}).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent?.slice(0,55),right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width,overflow:getComputedStyle(e).overflowX})).slice(0,40)})));
}
await browser.close();
