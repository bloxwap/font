#!/usr/bin/env bash
# Full build: skeletons -> UFO -> variable + static fonts -> web formats -> dist + website data.
# Run from anywhere; paths are relative to packages/font.  Usually: bun run fonts:build [family ...]
#   tools/build_all.sh               all families
#   tools/build_all.sh sans mono     selected families
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
FONTMAKE=.venv/bin/fontmake
export PYTHONPATH="$PWD/tools${PYTHONPATH:+:$PYTHONPATH}"
if [ $# -eq 0 ]; then
  FAMS=()
  while IFS= read -r fam; do FAMS+=("$fam"); done < <("$PY" -c 'import sys; sys.path.insert(0, "tools"); from bwfont.families import FAMILIES; print("\n".join(FAMILIES))')
else FAMS=("$@"); fi

psname() { "$PY" -c "import sys; sys.path.insert(0, 'tools'); from bwfont.families import FAMILIES; print(FAMILIES['$1'].ps)"; }

echo "==> checking skeletons"
$PY tools/check_cusps.py | tail -1
$PY tools/check_glyphs.py --pack core,arabic,hebrew,armenian,georgian | grep -v robust_union | tail -1

echo "==> generating sources: ${FAMS[*]}"
$PY tools/generate.py "${FAMS[@]}"

FILTER="bwfont.ufo2ft_filters::RobustRemoveOverlapsFilter"
export FONTMAKE FILTER

compile_static() {   # $1 = instance ufo, $2 = family build dir
  $FONTMAKE -u "$1" -o otf --output-dir "$2/otf" --keep-overlaps --filter "$FILTER" >> "$2/static.log" 2>&1 &&
  $FONTMAKE -u "$1" -o ttf --output-dir "$2/ttf" --keep-overlaps --filter "$FILTER(pre=True)" >> "$2/static.log" 2>&1
}
export -f compile_static

compile_family() {
  local fam=$1; local ps; ps=$(psname "$1")
  local ds="sources/$fam/$ps.designspace"
  local out="build/$fam"
  rm -rf "$out"
  mkdir -p "$out"
  $FONTMAKE -m "$ds" -o variable --output-dir "$out/variable" > "$out/fontmake.log" 2>&1 \
    || { echo "!! variable build failed for $fam"; tail -30 "$out/fontmake.log"; return 1; }
  echo "    $fam: variable done"
  $PY tools/make_instances.py "$ds" "$out/instance_ufos" || return 1
  ls -d "$out"/instance_ufos/*.ufo | xargs -P "${JOBS:-6}" -I{} bash -c 'compile_static "$1" "$2"' _ {} "$out" \
    || { echo "!! static build failed for $fam"; tail -30 "$out/static.log"; return 1; }
  echo "    $fam: $(ls "$out/otf" | wc -l | tr -d ' ') otf, $(ls "$out/ttf" | wc -l | tr -d ' ') ttf"
}

echo "==> compiling (parallel)"
pids=()
for fam in "${FAMS[@]}"; do compile_family "$fam" & pids+=($!); done
fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
[ $fail -eq 0 ] || exit 1

echo "==> post-processing, web formats, dist, site"
$PY tools/postprocess.py "${FAMS[@]}"
