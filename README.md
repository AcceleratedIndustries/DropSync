# DropSync

DropSync is a local-first inbox for links, notes, files, and code. Capture material from browsers, hotkeys, or DBus, enrich it with readability and full-page snapshots, and sync everything into a Syncthing-friendly folder structure.

## Highlights

- **FastAPI + DBus daemon** – HTTP endpoints (`/url`, `/note`, `/code`, `/file`) and a DBus session service (`org.dropsync.Collector1`).
- **Automatic enrichment** – readability stubs, monolith single-file HTML, yt-dlp, and gallery-dl kicked off per-domain with rule-based overrides.
- **Rules & nightly organizer** – `~/.dropsync/rules.toml` to tag, move, and trigger post-processors; organizer service keeps directories tidy.
- **pipx-first packaging** – one command install, with user-level systemd units and installer scripts for Arch, Debian, and macOS.
- **Local web UI** – `/capture` page for quick submissions plus bookmarklet, Hyprland/Niri bindings, and DBus helpers for KDE/GNOME.

## Quickstart (Arch Linux)

```bash
# 1. Install system dependencies and pipx package
git clone https://github.com/WilliamAppleton/DropSync.git
cd DropSync
make install-arch

# 2. Generate default config and ensure folders exist
dropsync config init || true

# 3. Enable user services
make service

# 4. Verify
curl http://127.0.0.1:8765/health
```

Add the bookmarklet from `examples/bookmarklet.txt` to your browser, or visit `http://127.0.0.1:8765/capture` for the built-in UI. Captured items land under `~/Sync/Collect` by default and will appear in Syncthing as soon as files finish downloading.

## Directory layout

```
~/Sync/Collect/
  links/         # Markdown stubs and readability outputs
  notes/         # Scratch notes
  code/          # Code snippets (markdown fenced)
  files/         # Uploaded files (binary)
  media/         # yt-dlp / gallery-dl output
  .dropsync/     # rules.toml, state
```

## Commands

| Command | Purpose |
|---------|---------|
| `dropsync run` | Launch the FastAPI + DBus daemon (used by systemd service) |
| `dropsync doctor` | Check external dependencies and report versions |
| `dropsync config print` | Show effective configuration including env overrides |
| `dropsync config init` | Scaffold `~/.config/dropsync/config.toml` |
| `dropsync organize [--force]` | Apply rules, move files, queue missing post-processors |

See [`USAGE.md`](USAGE.md) for full HTTP/DBus examples.

## Processors & rules

- `readability-cli` generates `*.readable.md` for every URL.
- `monolith --isolate --no-js` saves a single-file HTML snapshot when the item type is an article or gallery.
- `yt-dlp` and `gallery-dl` run when the domain matches built-in heuristics (YouTube, Vimeo, Imgur, Reddit, etc.).
- Extend behaviour with `~/.dropsync/rules.toml` – sample in [`examples/rules.toml`](examples/rules.toml) and full syntax documented in [`RULES.md`](RULES.md).

## Integrations

- Bookmarklet and `/capture` web UI.
- Hyprland / Niri clipboard shortcuts.
- KDE & GNOME shell scripts using DBus (`examples/kde_gdbus.sh`, `examples/gnome_gdbus.sh`).

More recipes live in [`INTEGRATIONS.md`](INTEGRATIONS.md).

## Development

```bash
make fmt lint test
```

The project targets Python 3.11+, uses FastAPI, Typer, and dbus-next, and ships with pytest, ruff, black, and mypy. Continuous integration runs on GitHub Actions (`.github/workflows/ci.yml`).

## License

BSD-2-Clause © 2024 W. Appleton. See [`LICENSE`](LICENSE).
