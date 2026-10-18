#!/bin/sh
# Homebrew Python 3.13 for self-hosted Mac minis.
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
if command -v python3.13 >/dev/null 2>&1; then
  py=$(command -v python3.13)
elif command -v python3 >/dev/null 2>&1; then
  ver=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  if [ "$ver" = "3.13" ]; then
    py=$(command -v python3)
  fi
fi

if [ -z "$py" ]; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "Python 3.13 is required. Install Homebrew, then: brew install python@3.13"
    echo "actions/setup-python cannot install here: it writes /Users/runner/hostedtoolcache."
    exit 1
  fi
  echo "Installing python@3.13 with Homebrew (same 3.13 pin as setup-python)."
  brew install python@3.13
  if command -v python3.13 >/dev/null 2>&1; then
    py=$(command -v python3.13)
  else
    py="$(brew --prefix python@3.13)/bin/python3.13"
  fi
fi

if [ ! -x "$py" ]; then
  echo "Python 3.13 was not found after install at $py"
  exit 1
fi
"$py" --version
venv="$RUNNER_TEMP/font-venv"
"$py" -m venv "$venv"
echo "$venv/bin" >> "$GITHUB_PATH"
echo "FONT_PYTHON=$venv/bin/python" >> "$GITHUB_ENV"
