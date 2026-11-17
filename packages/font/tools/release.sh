#!/usr/bin/env bash
# Publish the download zips as GitHub Release assets. `bun run fonts:build` writes them to
# apps/docs/public/downloads/ (ignored by git); the website links to releases/latest/download/<name>.zip.
#   tools/release.sh            tag v<@bloxwap/font version> (packages/npm/package.json), e.g. v0.1.0
#   tools/release.sh v0.1.1     explicit tag
# One version everywhere: the GitHub Release tag follows the npm package, and publishing the release
# triggers .github/workflows/publish_npm.yml for that version.
# Creates a new immutable release from committed artifacts.  Needs the GitHub CLI (gh auth login).
set -euo pipefail
cd "$(dirname "$0")/../../.."
TAG=${1:-v$(node -p "require('./packages/npm/package.json').version")}
shopt -s nullglob
ZIPS=(apps/docs/public/downloads/*.zip)
[ ${#ZIPS[@]} -gt 0 ] || { echo "no zips in apps/docs/public/downloads — run bun run fonts:build first"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo 'Commit generated fonts and the source lock before releasing'; exit 1; }
[ "$TAG" = "v$(node -p "require('./packages/npm/package.json').version")" ] || { echo 'Release tag must match package version'; exit 1; }
if gh release view "$TAG" >/dev/null 2>&1; then
  echo 'Published releases are immutable; create a new version'; exit 1
fi
# Verify that regenerating the lock reproduces the committed inventory.
"${FONT_PYTHON:-packages/font/.venv/bin/python}" packages/npm/scripts/static_sources.py lock --tag "$TAG"
git diff --exit-code -- packages/npm/static-sources.json || { git restore -- packages/npm/static-sources.json; echo 'ZIPs differ from the committed lock'; exit 1; }
if git rev-parse "$TAG" >/dev/null 2>&1 && [ "$(git rev-list -n 1 "$TAG")" != "$(git rev-parse HEAD)" ]; then
  echo 'Tag does not point to the current commit'; exit 1
fi

gh release create "$TAG" "${ZIPS[@]}" --target "$(git rev-parse HEAD)" --title "Bloxwap Font $TAG" \
    --notes "Desktop and web fonts for every Bloxwap Font family (OTF, TTF, WOFF2, WOFF and variable), under the SIL Open Font License 1.1. \`Bloxwap-Fonts.zip\` holds Sans, Mono and Pixel; each script companion has its own zip. Specimens and docs: https://bloxwap.github.io/font/"
echo "released ${#ZIPS[@]} zips as $TAG"
