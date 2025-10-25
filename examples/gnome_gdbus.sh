#!/usr/bin/env bash
# Send clipboard selection to DropSync as a note via DBus
set -euo pipefail

NOTE=$(wl-paste 2>/dev/null || xclip -o)

if [[ -z "$NOTE" ]]; then
  echo "Clipboard empty" >&2
  exit 1
fi

gdbus call \
  --session \
  --dest org.dropsync.Collector1 \
  --object-path /org/dropsync/Collector1 \
  --method org.dropsync.Collector1.SaveNote \
  "" \
  "$NOTE" \
  "{}" >/dev/null

echo "Clipboard note sent to DropSync"
