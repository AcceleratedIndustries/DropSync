# Integrations

DropSync is designed to be launched from browsers, window managers, and shell scripts.

## Bookmarklet

Copy the contents of [`examples/bookmarklet.txt`](examples/bookmarklet.txt) into a new browser bookmark. When clicked, the current page (URL, title, text selection) is sent to `/url`.

## Web UI

Visit `http://127.0.0.1:8765/capture` for a minimal capture page that wraps the same endpoints. Add it as a PWA-style shortcut if you prefer a dedicated window.

## Hyprland

Add the snippet from [`examples/hyprland.conf.snip`](examples/hyprland.conf.snip) to your Hyprland config. It binds `Super+u` to send the clipboard as a URL and `Super+Shift+n` to prompt for a note via `bemenu`.

## Niri

[`examples/niri.conf.snip`](examples/niri.conf.snip) demonstrates two bindings using `wl-paste` and `wofi` to feed the HTTP API.

## KDE Plasma & GNOME

Use the DBus helpers:

- [`examples/kde_gdbus.sh`](examples/kde_gdbus.sh) – drop into KDE service menus or custom shortcuts to forward URLs.
- [`examples/gnome_gdbus.sh`](examples/gnome_gdbus.sh) – send clipboard text as a note. Works with GNOME custom keybindings or scripts.

Both scripts call the `org.dropsync.Collector1` service and emit the same `ItemSaved` signal received by the daemon. Check success via `journalctl --user -u dropsync.service`.

## Clipboard workflows

Examples assume Wayland (`wl-paste`). Adjust to `xclip -o` on X11. The HTTP API accepts JSON payloads so any scripting language can pipe data in:

```bash
pbpaste | jq -Rs '{body: .}' | curl -H 'Content-Type: application/json' -d @- http://127.0.0.1:8765/note
```

## Tray / status

A lightweight tray helper is planned for a future release. For now, monitor the `ItemSaved` DBus signal or watch the Syncthing folder.
