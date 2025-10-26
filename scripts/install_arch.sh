#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# Check for yay (required for AUR packages)
if ! command -v yay >/dev/null 2>&1; then
  echo "[ERROR] yay is required to install AUR packages (nodejs-readability-cli)."
  echo "Install yay first: https://github.com/Jguer/yay#installation"
  echo "Alternative: Install nodejs-readability-cli manually via npm:"
  echo "  npm install -g readability-cli"
  exit 1
fi

PACMAN_PACKAGES=(
  python
  python-pipx
  xclip
  jq
  glib2
  yt-dlp
  monolith
)
AUR_PACKAGES=(nodejs-readability-cli)

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

yay -S --needed "${AUR_PACKAGES[@]}"

# nodejs-readability-cli installs as 'readable', create symlink if needed
if command -v readable >/dev/null 2>&1 && ! command -v readability-cli >/dev/null 2>&1; then
  echo "[INFO] Creating readability-cli symlink to readable..."
  sudo ln -sf /usr/bin/readable /usr/bin/readability-cli
fi

pipx install --force "$REPO_ROOT"

systemctl --user daemon-reload || true

echo "DropSync installed via pipx. Run 'dropsync config init' if this is a fresh install."
