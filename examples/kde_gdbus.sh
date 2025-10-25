#!/usr/bin/env bash
# Usage: kde_gdbus.sh "https://example.com" "Optional Title"
set -euo pipefail

URL=${1:-}
TITLE=${2:-}

if [[ -z "$URL" ]]; then
  echo "Usage: $0 <url> [title]" >&2
  exit 1
fi

gdbus call \
  --session \
  --dest org.dropsync.Collector1 \
  --object-path /org/dropsync/Collector1 \
  --method org.dropsync.Collector1.SaveUrl \
  "$URL" \
  "${TITLE}" \
  "" \
  "{}" >/dev/null

echo "Sent $URL to DropSync"
