# Installation Guide

DropSync targets Linux (Arch/Debian) and macOS via `pipx`. The daemon is designed to run as a per-user service (systemd user units provided).

## 1. Prerequisites

- Python 3.11+
- `pipx` in your `$PATH`
- Syncthing already managing your DropSync root (default `~/Sync/Collect`)

### Required helpers

| Tool | Purpose | Notes |
| ---- | ------- | ----- |
| `readability-cli` | Article extraction | AUR (`nodejs-readability-cli`) or `npm install -g readability-cli` |
| `monolith` | Single-file HTML snapshots | Available via `pacman` (Arch), `cargo install monolith`, or Homebrew |
| `yt-dlp` | Media downloads | `pacman`, `apt`, `brew` |
| `gallery-dl` | Galleries, image sets | `pacman`, `apt`, `brew` |
| `gdbus` | DBus CLI helper | Part of `glib2` / `gobject-introspection` |
| `jq`, `xclip` | Helper tools used in examples | Optional but recommended |

## 2. Arch Linux (primary target)

**Prerequisite**: `yay` (AUR helper) must be installed. See [yay installation](https://github.com/Jguer/yay#installation).

```bash
git clone https://github.com/WilliamAppleton/DropSync.git
cd DropSync
make install-arch

# Configure DropSync (creates ~/.config/dropsync/config.toml)
dropsync config init || true

# Enable services
make service
systemctl --user start dropsync.service
systemctl --user enable --now dropsync-organize.timer

# Verify
dropsync doctor
curl http://127.0.0.1:8765/health
```

`make install-arch` uses `pacman` for base packages and `yay` for AUR packages (`nodejs-readability-cli`). The install script automatically creates a symlink from `readability-cli` to `readable` if needed.

## 3. Debian / Ubuntu

```bash
git clone https://github.com/WilliamAppleton/DropSync.git
cd DropSync
make install-debian

dropsync config init || true
make service
systemctl --user enable --now dropsync.service dropsync-organize.timer
```

`make install-debian` installs from `apt` where possible, falls back to `npm`/`cargo` for readability-cli and monolith. Ensure `$HOME/.local/bin` is on your PATH (pipx).

## 4. macOS (Homebrew)

```bash
git clone https://github.com/WilliamAppleton/DropSync.git
cd DropSync
make install-macos
```

Launch manually with `dropsync run` or build a LaunchAgent (see `INTEGRATIONS.md`). On macOS the DBus service requires `dbus-daemon --session` (e.g., via Homebrew `dbus` formula).

## 5. Manual pipx install

```bash
git clone https://github.com/WilliamAppleton/DropSync.git
cd DropSync
pipx install .
```

Systemd unit files live under `systemd/`; copy them to `~/.config/systemd/user/` and enable as shown above.

## 6. Upgrading

```bash
cd /path/to/DropSync
git pull
pipx install --force .
systemctl --user restart dropsync.service
```

## 7. Post-install checklist

- Open `~/.config/dropsync/config.toml` and adjust `root`, `bind_host`, or processor command arrays if needed.
- Copy `examples/rules.toml` to `~/Sync/Collect/.dropsync/rules.toml` and tailor domain-specific rules.
- Add the bookmarklet or configure your window manager bindings.
- Confirm `~/.local/bin` precedes the system Python in PATH (for pipx scripts).

For troubleshooting, run `dropsync doctor` and review logs via `journalctl --user -u dropsync.service`.
