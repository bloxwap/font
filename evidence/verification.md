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
| Browsers | `DOCS_URL=... PLAYWRIGHT_BROWSERS_PATH=... bunx playwright test ...` | 57 distinct checks validated in three engines; broad run plus targeted reruns below |

The broad 45-case run passed 43 immediately, one WebKit Unicode-name check on retry,
and failed Firefox's existing family-name assertion because Firefox retains CSS quotes.
The assertion now normalizes quotes. A clean targeted run of deployed.spec.ts and
scripts.spec.ts passed 15/15 (including the fixed Firefox check and all 12 script cases).
The independent Unicode-name recheck passed 3/3 without retries. The accompanying
browser-targeted.txt and unicode-recheck.txt record those final reruns. The CI job runs
all 57 cases together against the final export and remains the merge gate.

Earlier attempts with system Chrome had browser startup/teardown timeouts, and a
shared local preview port collided with another server. Those attempts are not counted
as certification. Final checks use matching Playwright browsers and dedicated port 43914.
Before/after screenshots use system Chrome on Linux and are visual/byte comparisons.

No native app was built or run. No physical iOS/Android, iOS hardware, Dynamic Type,
VoiceOver/TalkBack or platform font-substitution/clipping observation is represented by
these binary, typecheck or browser tests. HIG consumers own native runtime integration
and device evidence. No font glyph sources or committed font binaries were changed.
