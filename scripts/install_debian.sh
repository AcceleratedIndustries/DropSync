#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  pipx \
  xclip \
  jq \
  gir1.2-glib-2.0 \
  yt-dlp \
  gallery-dl \
  npm

if ! command -v readability-cli >/dev/null 2>&1; then
  sudo npm install -g readability-cli
fi

if ! command -v monolith >/dev/null 2>&1; then
  echo "[INFO] Installing monolith via cargo (requires Rust toolchain)."
  if ! command -v cargo >/dev/null 2>&1; then
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    source "$HOME/.cargo/env"
  fi
  cargo install monolith
fi

pipx install --force "$REPO_ROOT"

systemctl --user daemon-reload || true

echo "DropSync installed via pipx. Run 'dropsync config init' if needed."
