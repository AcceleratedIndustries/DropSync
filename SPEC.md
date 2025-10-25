# DropSync — SPEC v0.1.0

## Overview
DropSync is a local-first “capture → enrich → sync” companion for Syncthing. It accepts URLs, notes, code, and files via HTTP, DBus, or a minimal Web UI, enriches them using readability/monolith/yt-dlp/gallery-dl, and writes outputs to a Syncthing-friendly folder structure.

## Core components

- **Daemon (`dropsyncd`)**
  - FastAPI server on 127.0.0.1:8765 (configurable) with endpoints `/url`, `/note`, `/code`, `/file`, `/health`, `/config/reload`, `/capture`.
  - DBus session service `org.dropsync.Collector1` exposing `SaveUrl`, `SaveNote`, `SaveCode`, `SaveFile` plus `ItemSaved` signal.
  - Processor orchestrator launching `readability-cli`, `monolith --isolate --no-js`, `yt-dlp`, and `gallery-dl` asynchronously.
  - Rule engine loading `<root>/.dropsync/rules.toml` (match on domain/type/ext, apply tags, move targets, queue post-processors).

- **CLI (`dropsync`)**
  - `run`: start daemon (used by systemd service).
  - `doctor`: verify external tools (versions/status).
  - `config init/print`: manage TOML config.
  - `organize [--force]`: nightly organizer to reapply rules and trigger missing processors.

- **Packaging & services**
  - Python 3.11+, packaged for pipx via `pyproject.toml` (hatchling).
  - Installer scripts for Arch (`pacman` + `yay`), Debian/Ubuntu (`apt` + npm/cargo), macOS (Homebrew).
  - User-level systemd units (`dropsync.service`, `dropsync-organize.service`, `dropsync-organize.timer`).

## Data model

- Root directory default `~/Sync/Collect` (override via config or `DROPSYNC_ROOT`).
- Subdirectories: `links`, `notes`, `code`, `files`, `media`, `scratch`.
- Filenames follow `YYYYMMDD-HHMMSS--Title.ext`; collisions append `--hash8`.
- URL stubs contain YAML front matter (`title`, `url`, `domain`, `kind`, `type`, `timestamp`, `tags`, etc.) and optional selection text. Companion files: `*.readable.md`, `*.single.html`.

## Processors

- Readability runs for every URL (writes `*.readable.md`).
- Monolith runs for articles/galleries or when requested by rules (output `*.single.html`).
- yt-dlp handles video domains (saves media to `media/`).
- gallery-dl handles galleries (saves to `media/`).
- Additional processors can be queued via rules `post = ["monolith", ...]`.

## Security defaults

- Loopback binding (`127.0.0.1`) and token disabled by default.
- LAN operation requires explicit `bind_host` change plus `auth_token`.
- CORS disabled unless `cors_origins` configured.

## Integrations

- Bookmarklet (`examples/bookmarklet.txt`).
  - `/capture` web UI (HTML/CSS/JS in `dropsync/webui/`).
  - Wayland compositor snippets (Hyprland/Niri) and DBus helpers (KDE/GNOME).

## Quality & CI

- Linting: `ruff`, `black --check`, `mypy`.
- Testing: `pytest`, `pytest-asyncio` covering config, utils, server handlers, rules, processor scheduling.
- GitHub Actions workflow `.github/workflows/ci.yml` (Python 3.11).

## Publishing

- `Makefile` with targets: `pipx`, `install-arch`, `install-debian`, `install-macos`, `service`, `run`, `organize`, `lint`, `fmt`, `test`, `publish`, `clean`.
- `make publish` ensures remote `WilliamAppleton/DropSync`, pushes `main`, optionally invokes `gh release create --draft v0.1.0` when available.

## Documentation

- Comprehensive docs: `README`, `INSTALL`, `USAGE`, `CONFIG`, `RULES`, `INTEGRATIONS`, `SECURITY`, `UNINSTALL`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `CHANGELOG`.

This spec tracks the v0.1.0 deliverable implemented in this repository.
