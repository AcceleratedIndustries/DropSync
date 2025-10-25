#!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="WilliamAppleton/DropSync"
REMOTE_SSH="git@github.com:${REPO_SLUG}.git"
REMOTE_HTTPS="https://github.com/${REPO_SLUG}.git"
DEFAULT_BRANCH="main"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must be run inside the DropSync repository." >&2
  exit 1
fi

git init

git add .

git commit -m "Initial DropSync import" || true

if ! git remote get-url origin >/dev/null 2>&1; then
  if command -v ssh >/dev/null 2>&1; then
    git remote add origin "${REMOTE_SSH}"
  else
    git remote add origin "${REMOTE_HTTPS}"
  fi
fi

git branch -M "${DEFAULT_BRANCH}"

git push -u origin "${DEFAULT_BRANCH}"

echo "Repository pushed to ${REPO_SLUG}. Use 'make publish' for releases." 
