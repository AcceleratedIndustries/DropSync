#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh first." >&2
  exit 1
fi

brew update
brew install \
  python@3.11 \
  pipx \
  jq \
  yt-dlp \
  gallery-dl \
  gobject-introspection \
  monolith \
  node

pipx ensurepath

if ! command -v readability-cli >/dev/null 2>&1; then
  npm install -g readability-cli
fi

pipx install --force "$REPO_ROOT"

echo "DropSync installed for macOS. Configure launchd or run 'dropsync run'."
