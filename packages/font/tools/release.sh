#!/usr/bin/env bash
# Publish the download zips as GitHub Release assets. `bun run fonts:build` writes them to
# apps/docs/public/downloads/ (ignored by git); the website links to releases/latest/download/<name>.zip.
#   tools/release.sh            tag v<@bloxwap/font version> (packages/npm/package.json), e.g. v0.1.0
#   tools/release.sh v0.1.1     explicit tag
# One version everywhere: the GitHub Release tag follows the npm package, and publishing the release
# triggers .github/workflows/publish_npm.yml for that version.
# Creates the release if it doesn't exist, otherwise replaces its zips.  Needs the GitHub CLI (gh auth login).
set -euo pipefail
cd "$(dirname "$0")/../../.."
TAG=${1:-v$(node -p "require('./packages/npm/package.json').version")}
shopt -s nullglob
ZIPS=(apps/docs/public/downloads/*.zip)
[ ${#ZIPS[@]} -gt 0 ] || { echo "no zips in apps/docs/public/downloads — run bun run fonts:build first"; exit 1; }
if gh release view "$TAG" >/dev/null 2>&1; then
  gh release upload "$TAG" "${ZIPS[@]}" --clobber
else
  gh release create "$TAG" "${ZIPS[@]}" --title "Bloxwap Font $TAG" \
    --notes "Desktop and web fonts for every Bloxwap Font family (OTF, TTF, WOFF2, WOFF and variable), under the SIL Open Font License 1.1. \`Bloxwap-Fonts.zip\` holds Sans, Mono and Pixel; each script companion has its own zip. Specimens and docs: https://bloxwap.github.io/font/"
fi
echo "released ${#ZIPS[@]} zips as $TAG"
