# Canonical Font ownership in the docs

Font owns the fonts that its documentation publishes. The root `hig-drift.json` uses the HIG scoped checker schema (`paths`, `canonical`, `obsoleteImports`, `exceptions`) and scans the tracked `apps/docs` tree. It names the 48 web-font binaries in `apps/docs/public/fonts` (including 24 core subsets) and the two OG TTFs in `apps/docs/assets/og` individually. These are Font's own distribution/preview assets, not copies from `@bloxwap/hig-native-fonts`.

The canonical list contains only those exact `.woff2`/`.ttf` paths. No directory, CSS file, component, HIG asset or vendored package is exempted. HIG still owns token definitions and control CSS; the documentation keeps its existing `@bloxwap/hig-*` imports. The existing owning vendor guard also checks archive hashes, installed versions and token/control redefinitions. There are no dated exceptions in this configuration.

When a Font build adds, renames or removes a published binary, update the individual canonical paths after checking the file's ownership. A newly tracked binary without a declaration fails drift. Adding CSS or components under the font directories does not make them canonical.

## Run the checks

The runtime packages stay on their existing checksummed candidate `7c67a07c`; their font APIs and appearance do not change. That older source predates HIG's scoped drift CLI, so this check independently pins the tooling to HIG `0e2394428a3971e677e0a97ef5259ac4ca1ec064`. This is a tooling checkout, not a runtime package refresh. Keep the tool ref in `.github/workflows/hig-drift.yml` and this guide together when upgrading it.

```sh
git clone --filter=blob:none --no-checkout https://github.com/bloxwap/hig.git .hig
git -C .hig fetch --depth=1 origin 0e2394428a3971e677e0a97ef5259ac4ca1ec064
git -C .hig sparse-checkout set --no-cone /scripts/drift.mjs
git -C .hig checkout --detach FETCH_HEAD
bun install --frozen-lockfile
node .hig/scripts/drift.mjs --root . --config hig-drift.json
bun run --cwd apps/docs scripts/check-hig-vendor.ts
```

The `.hig` checkout is ignored. The `HIG font ownership` workflow runs those same two guards on relevant pull requests and main changes, using the actual pinned HIG checker rather than a copy. It does not deploy or publish anything.

Validation and font/package identity evidence are recorded in `evidence/hig-canonical-ownership/`. Owner review and merging remain separate from automated results.
