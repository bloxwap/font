# CI runners

GitHub Actions jobs run on self-hosted Apple Silicon Mac minis, except the `publish` job in `.github/workflows/publish_npm.yml`:

```yaml
runs-on: [self-hosted, macOS, ARM64]
```

Mac mini jobs do not call `apt`, `sudo`, or `playwright install --with-deps`. System tools must already be on the machine. Workflow scripts are BSD/`bash` 3.2 portable and write scratch files under `$RUNNER_TEMP`.

## npm trusted publishing exception

[npm trusted publishing and provenance require GitHub-hosted runners](https://docs.npmjs.com/trusted-publishers/). Only `publish` in `publish_npm.yml` runs on GitHub-hosted `ubuntu-24.04`; all other jobs, including the existing security scan, stay on the minis. It builds locally on that runner with Node 24, npm 11.6.1, Python 3.13 and pinned pip dependencies, with no package-manager cache.

Configure the GitHub `npm-release` environment with required reviewers; the workflow references this environment, but required reviewers must be configured in repository settings. The job grants only `contents: read` and `id-token: write` and publishes with `--provenance`, including when token fallback is used.

Releases continue to work before npm configuration using the existing `NPM_TOKEN` secret as a transitional fallback, scoped to authentication, publish, and deprecation steps. On npmjs.com, configure the `@bloxwap/font` Trusted Publisher for organization `bloxwap`, repository `font`, workflow filename `publish_npm.yml`, and environment `npm-release`. Verify trusted publishing works, then delete `NPM_TOKEN` and its fallback bindings. Without a token, the authentication check accepts GitHub OIDC. `npm deprecate` cannot use OIDC, so deprecation emits a warning and is skipped when the token is absent.

## Runner labels

Register each Mac mini with the GitHub Actions runner application using all three labels:

| Label | Meaning |
| --- | --- |
| `self-hosted` | Not a GitHub-hosted VM |
| `macOS` | Darwin (required by Pages artifact packaging and Playwright's cache path) |
| `ARM64` | Apple Silicon |

## Prerequisites

Install these on the runner account **before** the machine picks up jobs. Homebrew is the expected installer; do not grant the runner passwordless `sudo` for CI.

### Operating system

- macOS on Apple Silicon
- Xcode Command Line Tools (`xcode-select --install`) for Playwright WebKit and any native Python wheel fallback

### Always on `PATH`

| Tool | Why |
| --- | --- |
| `bash` | Default `run:` shell (macOS 3.2 is enough) |
| `git` | `actions/checkout` |
| `curl` | Docs preview readiness check |
| `gh` | Path filter in Font delivery quality (`changes`) |
| `gtar` | `actions/upload-pages-artifact` on macOS (Homebrew `gnu-tar`; the action invokes `gtar`, not BSD `tar`) |
| `python3.13` | Font package generate and test on minis (`brew install python@3.13`) |

```sh
brew install gh gnu-tar python@3.13
# gtar must resolve as the binary name `gtar` (Homebrew ships it that way)
# python3.13 must be on PATH (Homebrew does this for python@3.13)
```

`actions/setup-python` is used only by the Ubuntu publish job. On the minis it is not used. On macOS it installs only to `/Users/runner/hostedtoolcache`, and creating `/Users/runner` needs `sudo`. Jobs use Homebrew Python 3.13 in a per-job venv (same version pin) and run `brew install python@3.13` when `python3.13` is missing.

### Installed by workflow actions (do not pre-provision unless you want faster cold starts)

| Tool | Action | Jobs |
| --- | --- | --- |
| Bun | `oven-sh/setup-bun@v2` | docs build/deploy, font quality, browser shards |
| Node.js 24 | `actions/setup-node@v7` | npm pack/test, next-fixture, publish |
| Playwright browsers | `bunx playwright install <browser>` (no OS-deps flag) | `docs-browser` matrix: Chromium, WebKit |

Playwright browsers live on the mini at `~/Library/Caches/ms-playwright`. That directory must be writable by the runner user. Do **not** save it with `actions/cache`: the folder is already shared on disk, and GitHub cache save of Chromium or WebKit stalls ~24 minutes for ~1.5 GB (same as hig / monorepo #4603). `bunx playwright install` uses the on-disk cache.

### Python packages (user-level, per job)

Jobs run `python -m pip install` without `sudo`:

- `fonttools[woff,unicode]==4.66.1`
- `brotli==1.2.1`

### Writable locations

- `$RUNNER_TEMP` — preview logs, path-filter file lists, Pages tarball, Python venv
- `$HOME/Library/Caches/ms-playwright` — Playwright browser cache (on-disk only; not `actions/cache`)
- Tool caches used by `setup-bun` and `setup-node` (local on the mini; jobs do not enable `cache: npm`)

### Network

The runner must reach GitHub (git, APIs, Actions artifacts/cache, Pages, OIDC), `registry.npmjs.org`, the Bun registry, PyPI, and Playwright's browser CDN.

### Permissions

- GitHub Pages deploy (`Documentation` / `deploy`): `pages: write` and `id-token: write`
- npm publish (`Publish to npm`): `contents: read`, `id-token: write`, and the `npm-release` environment

GitHub Pages uses OIDC on the self-hosted runners; npm uses the GitHub-hosted exception above. Keep the runner application updated.

## Jobs

| Workflow | Job | Notes |
| --- | --- | --- |
| Documentation | `build` | Lint/typecheck/build docs; uploads Pages artifact (`gtar`) on `main` / dispatch, not on PRs |
| Documentation | `deploy` | GitHub Pages, `main` only |
| Font delivery quality | `changes` | Path filter via `gh`; aggregator inputs |
| Font delivery quality | `assets` | Font package generate, tests, next-fixture, pack (no GitHub `font-build` cache) |
| Font delivery quality | `docs-build` | Lint, typecheck, docs build, unit tests |
| Font delivery quality | `docs-browser` | Matrix `chromium` / `webkit`, `--workers=1` |
| Font delivery quality | `docs` | Required-check aggregator; skip is success |
| Publish to npm | `publish` | GitHub-hosted `ubuntu-24.04`; `npm-release`; OIDC with transitional token fallback and provenance; release / workflow_dispatch |

A single Mac mini will serialize the browser matrix. That is expected. Playwright coverage is Chromium and WebKit.
