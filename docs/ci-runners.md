# CI runners

Every GitHub Actions job in this repository runs on self-hosted Apple Silicon Mac minis:

```yaml
runs-on: [self-hosted, macOS, ARM64]
```

Jobs do not call `apt`, `sudo`, or `playwright install --with-deps`. System tools must already be on the machine. Workflow scripts are BSD/`bash` 3.2 portable and write scratch files under `$RUNNER_TEMP`.

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

```sh
brew install gh gnu-tar
# gtar must resolve as the binary name `gtar` (Homebrew ships it that way)
```

### Installed by workflow actions (do not pre-provision unless you want faster cold starts)

| Tool | Action | Jobs |
| --- | --- | --- |
| Bun | `oven-sh/setup-bun@v2` | docs build/deploy, font quality, browser shards |
| Node.js 24 | `actions/setup-node@v7` | npm pack/test, next-fixture, publish |
| Python 3.13 | `actions/setup-python@v6` | font package generate, publish |
| Playwright browsers | `bunx playwright install <browser>` (no OS-deps flag) | `docs-browser` matrix: Chromium, Firefox, WebKit |

Playwright browsers are cached at `~/Library/Caches/ms-playwright`. That directory must be writable by the runner user.

### Python packages (user-level, per job)

Jobs run `python -m pip install` without `sudo`:

- `fonttools[woff,unicode]==4.66.1`
- `brotli==1.2.0`

### Writable locations

- `$RUNNER_TEMP` — preview logs, path-filter file lists, Pages tarball
- `$HOME/Library/Caches/ms-playwright` — Playwright browser cache
- Tool caches used by `setup-bun`, `setup-node`, and `setup-python`

### Network

The runner must reach GitHub (git, APIs, Actions artifacts/cache, Pages, OIDC), `registry.npmjs.org`, the Bun registry, PyPI, and Playwright's browser CDN.

### Permissions

- GitHub Pages deploy (`Documentation` / `deploy`): `pages: write` and `id-token: write`
- npm trusted publishing (`Publish to npm`): `id-token: write`

OIDC works on official GitHub Actions self-hosted runners. Keep the runner application updated.

## Jobs

| Workflow | Job | Notes |
| --- | --- | --- |
| Documentation | `build` | Lint/typecheck/build docs; uploads Pages artifact (`gtar`) |
| Documentation | `deploy` | GitHub Pages, `main` only |
| Font delivery quality | `changes` | Path filter via `gh`; aggregator inputs |
| Font delivery quality | `assets` | Font package generate, tests, next-fixture, pack |
| Font delivery quality | `docs-build` | Lint, typecheck, docs build, unit tests |
| Font delivery quality | `docs-browser` | Matrix `chromium` / `firefox` / `webkit`, `--workers=1` |
| Font delivery quality | `docs` | Required-check aggregator; skip is success |
| Publish to npm | `publish` | Release / workflow_dispatch |

A single Mac mini will serialize the browser matrix. That is expected; coverage is unchanged.
