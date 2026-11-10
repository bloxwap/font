#!/usr/bin/env bash
# Decide which required checks a path must run.
# Doc-only allow-list: evidence/**, bench/**, and Markdown outside apps/docs.
# Every other tracked file maps to assets, docs, toolchain, or more than one.
set -euo pipefail

classify() {
  local file=$1
  assets=false
  docs=false
  toolchain=false
  case "$file" in
    evidence/*|bench/*) return 0 ;;
    *.md)
      case "$file" in
        apps/docs/*) docs=true ;;
      esac
      return 0
      ;;
  esac
  case "$file" in
    apps/docs/*|scripts/*|bunfig.toml|.github/workflows/docs.yml|.github/workflows/font-quality.yml|package.json|bun.lock)
      docs=true
      ;;
  esac
  case "$file" in
    apps/next-fixture/*|packages/npm/*|LICENSE|apps/docs/public/*|packages/font/*|.github/scripts/*|.github/workflows/font-quality.yml|.github/workflows/publish_npm.yml|.github/workflows/static-sources.yml|package.json|bun.lock)
      assets=true
      ;;
  esac
  case "$file" in
    packages/font/*|.github/scripts/*|scripts/*|.github/workflows/font-quality.yml|package.json|bun.lock)
      toolchain=true
      ;;
  esac
  # Unknown paths still run the required docs gate instead of passing as a no-op.
  if [ "$assets" = false ] && [ "$docs" = false ] && [ "$toolchain" = false ]; then
    docs=true
  fi
}

coverage() {
  local root file failed=0
  root=$(git rev-parse --show-toplevel)
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    classify "$file"
    if [ "$assets" = false ] && [ "$docs" = false ] && [ "$toolchain" = false ]; then
      case "$file" in
        evidence/*|bench/*|*.md) ;;
        *)
          echo "uncovered: $file" >&2
          failed=1
          ;;
      esac
    fi
  done < <(git -C "$root" ls-files)
  if [ "$failed" -ne 0 ]; then
    echo "ci-paths: a tracked file is outside the allow-list and runs no check" >&2
    return 1
  fi
  echo "ci-paths: every tracked file is allow-listed or runs a check"
}

fold() {
  local file
  assets=false
  docs=false
  toolchain=false
  while IFS= read -r file || [ -n "$file" ]; do
    [ -z "$file" ] && continue
    classify "$file"
    [ "${file_assets:-false}" = true ] && assets=true
    # classify overwrites assets/docs/toolchain; OR them via locals
  done
}

# fold is implemented below by re-reading; the function above is replaced.
fold_files() {
  local file a=false d=false t=false
  while IFS= read -r file || [ -n "$file" ]; do
    [ -z "$file" ] && continue
    classify "$file"
    [ "$assets" = true ] && a=true
    [ "$docs" = true ] && d=true
    [ "$toolchain" = true ] && t=true
  done
  assets=$a
  docs=$d
  toolchain=$t
}

case "${1:-}" in
  classify)
    classify "$2"
    printf 'assets=%s\ndocs=%s\ntoolchain=%s\n' "$assets" "$docs" "$toolchain"
    ;;
  coverage)
    coverage
    ;;
  fold)
    fold_files
    printf 'assets=%s\ndocs=%s\ntoolchain=%s\n' "$assets" "$docs" "$toolchain"
    if [ -n "${GITHUB_OUTPUT:-}" ]; then
      printf 'assets=%s\ndocs=%s\ntoolchain=%s\n' "$assets" "$docs" "$toolchain" >> "$GITHUB_OUTPUT"
    fi
    ;;
  *)
    echo "usage: ci-paths.sh classify FILE | coverage | fold < files" >&2
    exit 2
    ;;
esac
