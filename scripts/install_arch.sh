#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

PACMAN_PACKAGES=(
  python
  python-pipx
  xclip
  jq
  glib2
  yt-dlp
  monolith
)
AUR_PACKAGES=(readability-cli)

sudo pacman -Syu --needed "${PACMAN_PACKAGES[@]}"

if ! command -v gallery-dl >/dev/null 2>&1; then
  if pacman -Si gallery-dl >/dev/null 2>&1; then
    sudo pacman -S --needed gallery-dl
  else
    echo "[WARN] gallery-dl not available in configured pacman repositories."
    if command -v pipx >/dev/null 2>&1; then
      if ! pipx install --force gallery-dl; then
        echo "[WARN] pipx failed to install gallery-dl; install it manually."
      fi
    else
      echo "[WARN] pipx is unavailable; install gallery-dl manually (pipx install gallery-dl)."
    fi
  fi
fi

if command -v yay >/dev/null 2>&1; then
  yay -S --needed "${AUR_PACKAGES[@]}"
else
  echo "[WARN] yay not found; install readability-cli manually (npm i -g readability-cli)."
fi

pipx install --force "$REPO_ROOT"

systemctl --user daemon-reload || true

echo "DropSync installed via pipx. Run 'dropsync config init' if this is a fresh install."
