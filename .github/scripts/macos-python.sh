#!/bin/sh
# Homebrew Python 3.12 for self-hosted Mac minis.
# actions/setup-python hardcodes /Users/runner/hostedtoolcache on macOS; that
# path is not writable here (mkdir: /Users/runner: Permission denied).
set -eu
if [ -x /opt/homebrew/bin/brew ]; then
  echo /opt/homebrew/bin >> "$GITHUB_PATH"
  echo /opt/homebrew/sbin >> "$GITHUB_PATH"
  PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
elif [ -x /usr/local/bin/brew ]; then
  echo /usr/local/bin >> "$GITHUB_PATH"
  echo /usr/local/sbin >> "$GITHUB_PATH"
  PATH="/usr/local/bin:/usr/local/sbin:$PATH"
fi

py=""
if command -v python3.12 >/dev/null 2>&1; then
  py=$(command -v python3.12)
elif command -v python3 >/dev/null 2>&1; then
  ver=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  if [ "$ver" = "3.12" ]; then
    py=$(command -v python3)
  fi
fi

if [ -z "$py" ]; then
  # Homebrew bottles are fetched from ghcr.io, which this runner cannot resolve.
  # uv installs CPython 3.12 from the Astral/GitHub release instead.
  if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if [ -n "${GITHUB_PATH:-}" ]; then
      echo "$HOME/.local/bin" >> "$GITHUB_PATH"
    fi
  fi
  uv python install 3.12
  py=$(uv python find 3.12)
fi

if [ ! -x "$py" ]; then
  echo "Python 3.12 was not found after install at $py"
  exit 1
fi
"$py" --version
venv="$RUNNER_TEMP/font-venv"
"$py" -m venv "$venv"
echo "$venv/bin" >> "$GITHUB_PATH"
echo "FONT_PYTHON=$venv/bin/python" >> "$GITHUB_ENV"
