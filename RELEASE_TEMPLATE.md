# DropSync v0.1.0

## Highlights
- Initial FastAPI + DBus daemon with `/url`, `/note`, `/code`, `/file`, `/capture` endpoints.
- Asynchronous processors for readability-cli, monolith, yt-dlp, and gallery-dl.
- Rule engine with nightly organizer and CLI integration.
- pipx install scripts, systemd units, and `/capture` web UI.

## Upgrade Notes
- Requires Python 3.11+ and external tools (`readability-cli`, `monolith`, `yt-dlp`, `gallery-dl`).
- Default root `~/Sync/Collect`; customize via `dropsync config init` then edit TOML.

## Checksums
```
pipx install dropsync
```
