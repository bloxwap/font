#!/usr/bin/env bash
# Full build: skeletons -> UFO -> variable + static fonts -> web formats -> dist + website data.
# Run from anywhere; paths are relative to packages/font.  Usually: bun run fonts:build [family ...]
#   tools/build_all.sh               all families
#   tools/build_all.sh sans mono     selected families
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
export PYTHONPATH="$PWD/tools${PYTHONPATH:+:$PYTHONPATH}"
# Same commit, same bytes. fontTools timestampNow() reads SOURCE_DATE_EPOCH.
if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
  SOURCE_DATE_EPOCH=$("$PY" -c 'from toolchain import ensure_source_date_epoch; print(ensure_source_date_epoch())')
  export SOURCE_DATE_EPOCH
fi
echo "SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-unset}"
if [ -z "${JOBS+x}" ]; then
  if [ "$(uname -s)" = Darwin ]; then JOBS=$(sysctl -n hw.ncpu)
  elif command -v nproc >/dev/null 2>&1; then JOBS=$(nproc)
  else JOBS=$($PY -c 'import os; print(os.cpu_count() or 1)'); fi
fi
case "$JOBS" in ''|*[!0-9]*|0) echo "JOBS must be a positive integer" >&2; exit 1;; esac
export JOBS
if [ $# -eq 0 ]; then
  FAMS=()
  while IFS= read -r fam; do FAMS+=("$fam"); done < <("$PY" -c 'import sys; sys.path.insert(0, "tools"); from bwfont.families import FAMILIES; print("\n".join(FAMILIES))')
else FAMS=("$@"); fi

echo "==> checking skeletons"
$PY tools/check_cusps.py | tail -1
$PY tools/check_glyphs.py --pack core,arabic,hebrew,armenian,georgian | grep -v robust_union | tail -1

echo "==> generating and compiling (JOBS=$JOBS): ${FAMS[*]}"
$PY tools/build_pool.py "${FAMS[@]}"

echo "==> post-processing, web formats, dist, site"
$PY tools/postprocess.py "${FAMS[@]}"
