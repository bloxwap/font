# Validation commands and limits

Local Linux validation uses the committed lockfile, Python 3.13 / fonttools 4.66.1,
Next 16.3.6 and Playwright 1.63.0's matching browser binaries.

| Gate | Command | Result/evidence |
| --- | --- | --- |
| Dependencies | `bun install --frozen-lockfile` | Pass; frozen-install.txt |
| Assets/build | `FONT_PYTHON=.../.venv/bin/python node packages/npm/scripts/build.mjs` | Pass; 240 built faces; native-build.txt |
| Built files | `FONT_PYTHON=.../.venv/bin/python bun run test` | 3 Node tests + binary metadata/coverage checks across 240 faces pass; package-test.txt |
| Package | `npm pack --ignore-scripts --json` after verified build | 330 entries; packed-summary.json; CI uploads candidate |
| Lint | `bun run lint` | Pass; lint-final.txt |
| Typecheck | `NEXT_PUBLIC_BASE_PATH=/font bun run typecheck` | Pass; typecheck-final.txt |
| Static docs | `NEXT_PUBLIC_BASE_PATH=/font bun run docs:build` | Pass; 27 HTML files / 24 social cards / 52 font rules; docs-build-final.txt |
| Glyph semantics | `bun test apps/docs/lib/glyph-text.test.ts` | 4 pass; glyph-test.txt |
| Next consumer | `cd apps/next-fixture && bun run check && bun run build && node check-export.mjs` | Pass; Next/manifest/native-map types; two primary normal preloads; next-*.txt |
| Browsers | `DOCS_URL=... PLAYWRIGHT_BROWSERS_PATH=... bunx playwright test ...` | 57/57 pass in one complete run; browser-final-all.txt |

The final complete suite passed **57/57** without retries in Chromium, Firefox and WebKit;
see browser-final-all.txt. It includes the Arabic/Hebrew/Armenian/Georgian specimens
and downloads. FontFace family comparisons normalize quoted serialization.
The watchlist table is a keyboard-focusable HIG scroll region: this fixes a 7px
WebKit/DejaVu Serif overflow at 320px without hiding content or weakening reflow checks.
reflow-fixed.txt records five replacement font checks, all with a 320px page width.
The final hydration gate is covered by 30/30 affected browser checks (browser-hydration.txt), including a held glyph request that verifies disabled search before readiness and retained Unicode queries afterwards. Current Playwright config and CI run that suite on Chromium and WebKit.

No native app was built or run. No physical iOS/Android, iOS hardware, Dynamic Type,
VoiceOver/TalkBack or platform font-substitution/clipping observation is represented by
these binary, typecheck or browser tests. HIG consumers own native runtime integration
and device evidence. No font glyph sources or committed font binaries were changed.
