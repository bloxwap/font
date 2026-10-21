# Bloxwap font performance benchmark

The harness lives in `bench/` in this repository. It uses Python's standard library for orchestration and the repository's installed fontTools/fontmake/ttfautohint for font operations. It does not install dependencies, commit, push, or contact GitHub.

Run from the repository root with the font venv's Python:

```bash
# Existing assets only; disables npm prepack so this does not build anything.
packages/font/.venv/bin/python bench/bench.py assets

# Quick smoke test.
packages/font/.venv/bin/python bench/bench.py build --families pixel --runs 1

# Baseline: all requested families, sequentially; each run regenerates sources.
JOBS=6 packages/font/.venv/bin/python bench/bench.py build --families sans mono pixel --runs 3

# Adds exactly one unmodified build_all.sh sans invocation, including checks.
packages/font/.venv/bin/python bench/bench.py build --families sans --runs 3 --e2e

# Each run does a cold docs build (remove .next), then a warm build (keep .next),
# then npm assembly and npm pack (with the normal prepack lifecycle).
NEXT_PUBLIC_BASE_PATH=/font packages/font/.venv/bin/python bench/bench.py docs --runs 3

# Re-measure existing assets and export page weight after the docs build.
packages/font/.venv/bin/python bench/bench.py assets

# Run generate first, or use sources/instances from an earlier family build.
packages/font/.venv/bin/python bench/bench.py profile --family sans --stage generate
packages/font/.venv/bin/python bench/bench.py profile --family sans --stage variable
packages/font/.venv/bin/python bench/bench.py profile --family sans --stage static_ttf

# Merge saved JSON samples into bench/results/baseline.md (also writes report JSON).
packages/font/.venv/bin/python bench/bench.py report
```

`--repo`, `--results`, `--jobs` and `--restore` are global options: place them before the subcommand. Defaults are the repository root resolved from `bench.py`, `bench/results/`, `${JOBS:-6}`, and no restoration. Pass `--repo` to benchmark a different checkout or `--results` to choose a separate output directory. Runs must be positive integers. Results, timestamped command logs, raw `.prof` files, top 40 cumulative and self-time profile text, and the actual Sans Latin subset are written to `bench/results/` (gitignored). Failed stages also write JSON before exiting nonzero. Repeated runs produce per-run samples and medians. Report merges all result JSON, ignoring earlier reports and unrelated JSON without benchmark samples; move older samples elsewhere for a fresh baseline.

The `docs` command retains the native TTF cache for `npm_build` and `npm_pack`. To measure cold native generation separately, remove only the generated family directories, then time a build and its warm repeat:

```bash
rm -rf packages/npm/native/Bloxwap*
export FONT_PYTHON="$PWD/packages/font/.venv/bin/python"
time node packages/npm/scripts/build.mjs
time node packages/npm/scripts/build.mjs
```

Build regenerates `packages/font/sources`, `build`, `fonts`, and `apps/docs/public` (webfonts, downloads, CSS, site data), `apps/docs/lib/font-version.ts`, and possibly `apps/docs/assets/og`. It calls the existing generators without editing generator code or glyph definitions. Package/CSS/site stages run for the selected family after its compilation; package() also includes any other already built families. Static OTF and TTF are isolated into separate xargs stages with the same flags and concurrency as build_all.sh, which normally interleaves them per worker. Normal stage benchmarks omit the skeleton checks; `--e2e` runs the original script, including checks and its usual postprocess worker pool. Postprocessing is sequential and in-process for measurement, unlike that worker pool. Nested static TTF substage measurements overlap the parent; do not add both to get a build total. Remaining font load/fix work is included in the parent and `ttf_fix_save` tracks the TTF save. Autohint retains the existing best-effort fallback; inspect logs/output for skipped hinting.

Wall time uses `perf_counter`. CPU is delta self plus children user+system time; `children_cpu_seconds` separately gives total CPU consumed by reaped descendants (including the parallel static compilers). RSS fields are Linux KiB: `ru_maxrss` is a lifetime high-water mark, not a stage delta or summed concurrent memory. For an in-process stage, self RSS is relevant and child RSS may describe earlier commands. Per-file timings remain in raw JSON; summaries sum files within each run, then compute run median/min/max (RSS uses max). Profile static TTF launches one cProfile per xargs compiler and merges their stats. Profiles require generated inputs for variable/static stages and overwrite the corresponding compilation outputs.

`assets` measures `npm_unpacked_bytes` and `npm_file_count` for the single `@bloxwap/font` package, plus `npm_native_unpacked_bytes` and `npm_native_file_count` for its included native TTFs. All pack measurements use `--ignore-scripts`; assemble packages first with `FONT_PYTHON="$PWD/packages/font/.venv/bin/python" node packages/npm/scripts/build.mjs`.

Assets use shipped public fonts when no distribution fonts exist, report both trees separately, and never rebuild npm. A previously unassembled npm package can therefore have fewer files than a package built by `docs`. Table sizes are decoded, uncompressed SFNT lengths. The Google Fonts Latin subset preserves hinting, layout features `*`, and variations, and is saved in the results directory. Latin page bytes describe the shipped core Sans upright and italic Latin subset files referenced by the catalog CSS, falling back to full variable files when subsets are absent. The separate Google Fonts experiment does not represent the shipped Latin subset. Sizes are filesystem bytes, without HTTP overhead. CSS entries also report deterministic gzip sizes (level 9, mtime=0) and font-face counts.

The docs config uses `output: 'export'`, so page weight reads `apps/docs/out`. It reports all exported files plus index HTML and its unique local script/stylesheet/preload/prefetch references, stripping a `/font` basePath and query strings. Missing references are listed. Direct HTML references exclude lazy imports and non-preloaded fonts selected later through CSS; Latin font transfer is measured separately. It does not run a browser or estimate page-wide HTTP compression or Brotli transfer sizes. If docs have not been built, weight is explicitly unavailable.

For comparable runs, keep machine load, `JOBS`, Bun/font dependency versions, basePath, and existing other-family outputs consistent. JSON records versions, git SHA, CPU, RAM, CPU affinity, load average and the exact arguments. Warm docs builds retain `.next` from the immediately preceding cold build; other caches remain untouched.

Restoration is opt-in and destructive to existing tracked edits under these paths:

```bash
packages/font/.venv/bin/python bench/bench.py --restore build --families pixel --runs 1
```

In a finally block, this runs exactly `git -C "$REPO" checkout -- apps/docs/public apps/docs/lib packages`, followed by `git -C "$REPO" clean -fdx -- packages/font/build/`. Clean is limited to the font build directory. This is not a snapshot restore: it discards preexisting tracked edits in the checkout paths and leaves other untracked outputs (including fonts/sources, docs .next/out, and npm assembly) alone. The tracked checkout does not include `apps/docs/assets/og`. No automatic restoration happens without `--restore`.

## License

SIL Open Font License 1.1 (`OFL-1.1`). See [LICENSE](LICENSE).
