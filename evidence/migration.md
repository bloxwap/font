# Font contribution to HIG #7 and #34

Baseline font source: `269a0af` (latest default branch at start; no open font PRs).
HIG source: `1a776b9326c6ba03702894943b3edbfd178c4b40`, 0.1.0 candidate.
Font distribution: 0.1.3 candidate; no npm publication, tag or release.
Owner: font maintainers. Exception review: 2026-11-13.

## Presentation migration

The SDK-docs kit explicitly permits retaining Fumadocs conventions and a host-equivalent shell. This pilot keeps Fumadocs routing, navigation/mobile drawer, static Orama search, code/copy conventions and all distinctive font components. It imports the approved plain CSS distribution (HIG tokens and control styles), pinned with source hashes and the MIT license. A build check prevents hand-edited vendor drift. Local names now alias HIG semantic variables; shared button presentation comes from `.hig-button`. The old 80-line palette file and duplicate base button interaction declarations are removed. Fumadocs and SDK-specific axis/glyph/feature control layout remain intentional host adapters, not a forked HIG component library. Glyph search/category/script controls stay disabled while loading, preventing server-rendered input from accepting queries before hydration. No feedback backend is introduced; reduced motion and quiet status messages remain intact.

Rollback is a revert of this owning PR to baseline `269a0af` and its lockfile. The final migration removes the old copies after validation; there is no permanent duplicate CSS or dual-shell runtime flag. The kit's temporary pilot flag is replaced by this reviewed commit rollback. Upstream HIG packages are unpublished candidates, so package-registry imports would not be reproducible; the approved plain CSS route is used instead. Existing base path `/font`, static export, metadata/social cards, search index, docs deep links and SDK API examples remain supported. The installation page links the new cross-platform recipe and explicitly distinguishes published 0.1.2 from candidate additions.

## Equivalent measured pages

`capture.mjs` captures the home and installation page at 1280×900 and the home at 390×900 against the local production `/font` export with Chrome on Linux. Screenshots and raw resource metrics are adjacent to this report. Both baseline and final export are rebuilt from their locked sources; a two-second settling period includes route prefetches consistently. Bytes are decoded browser resource bodies, not compressed transfer sizes or npm package size. Home deliberately demonstrates the entire script catalog; its budget is not a minimal product UI budget.

| Page | CSS before → after | Font before → after | JS before → after |
| --- | --- | --- | --- |
| Home desktop | 190,005 → 193,351 | 11,567,128 → 11,567,128 | 1,718,785 → 1,719,166 |
| Installation desktop | 190,005 → 193,351 | 592,796 → 592,796 | 1,190,836 → 1,191,217 |
| Home mobile | 190,005 → 193,351 | 11,567,128 → 11,567,128 | 1,626,782 → 1,627,170 |

CSS increases by 3,346 decoded bytes from shared HIG styles. Runtime dependency count remains eight; ESLint/config/parser dependencies are development-only. TypeScript is pinned to 6.0.3 because the ESLint parser rejects the previous TypeScript 7 dependency. No runtime dependency removal is claimed. Font binaries and catalog data are unchanged. Selective font CSS entries allow consumers to avoid catalog-wide loading; the manifest reports the exact bytes for each chosen face. Retained swap/fallback loading is not certified as zero CLS.

## Asset and recipe evidence

The candidate contains 240 faces (24 variable WOFF2 plus 216 static TTF), totaling 276,286,760 font bytes. The packed artifact has 330 entries, 276,772,438 unpacked bytes and 117,382,906 compressed bytes; these are whole-catalog install costs, not automatic web/native runtime downloads.

The package builder copies the original variable WOFF2 bytes, emits family/script CSS with retained Unicode ranges and decodes the existing static WOFF2s into TTFs at the nine named weight tiers. Pixel ROND is fixed at 50. The existing named static sources carry approximate OS/2 weights (e.g. 608 for SemiBold); native registration metadata is normalized to the named tier (600) and sourceWeight is retained. Outlines, cmap, metrics and hinting remain unchanged, verified against the committed source tables. Each static face's unique embedded family/full/PostScript/typographic family name matches its Metro registration key. TTF output is generated rather than added as per-consumer binary copies. The typed manifest includes actual scripts, internal font version, package version, hashes, byte sizes and static/variable source hashes and axis provenance. Package tests open the built binaries and verify names, weights/styles, Unicode cmap, shaping script/feature tags, tabular digits, unchanged glyph/metric/hinting tables, source bytes, CSS paths and complete inventory. Per-family Metro maps have typed stable keys but bundle all their weights. Direct native/assets/* entries let consumers bundle only chosen faces. Assets must be registered before rendering.

The Next consumer fixture builds the package's existing Sans/Mono loaders in Next 16.3.6 and checks that only two primary normal faces are preloaded. Its typecheck also consumes the new manifest and native-map declarations. Browser checks cover font loading, the type tester/axes, glyph browsing/Unicode/ligature transfers, search/static paths, clipboard/install keyboard actions, mobile navigation, mixed-script text, replacement fonts, 320/640/1280 reflow and 200% root text. Existing Arabic/Hebrew/Armenian/Georgian script specimens remain part of the suite; physical-device behavior is not browser evidence.

## Remaining issue-level work

**HIG #7:** font-side assets/manifest, selective CSS, Next and native recipes are supplied. HIG consumers must integrate the candidate manifest and weight-to-family selection (the current native provider accepts only one fontFamily string), pin/release the approved artifact through the owning release process, and validate approved type roles and locale/loading budgets in their fixtures/products. Actual NativeWind rem-root mapping requires the product monorepo audit. No RN/Expo native app, physical iOS/Android, Dynamic Type, VoiceOver/TalkBack or native clipping rendering was run on this Linux VM; these checks require the owning host/device environment. Linux metadata assertions prove embedded names, not absence of runtime platform substitution.

**HIG #34:** this evidence and owning PR cover only the Font row. Hyperliquid, Chart, SFX and Haptic rows require their own linked owning PRs/build/demo evidence; this report makes no claim about their status. Upstream HIG owners must update `planning/adoption.json` with this PR/version/rollback and retain the candidate-vs-published distinction. Font's documented exceptions are the approved pinned CSS distribution, retained Fumadocs/demo adapters and commit rollback in place of a permanent pilot flag. Neither cross-repository issue is closed by this font contribution alone.
