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
if ! command -v python3.13 >/dev/null 2>&1; then
  echo "Python 3.13 is required on the runner. Install with: brew install python@3.13"
  echo "actions/setup-python cannot install here: it writes /Users/runner/hostedtoolcache."
  exit 1
fi
python3.13 --version
venv="$RUNNER_TEMP/font-venv"
python3.13 -m venv "$venv"
echo "$venv/bin" >> "$GITHUB_PATH"
echo "FONT_PYTHON=$venv/bin/python" >> "$GITHUB_ENV"
