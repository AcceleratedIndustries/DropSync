# Changelog

All notable changes to this project will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v0.1.0] - 2024-05-13
### Added
- FastAPI + DBus daemon exposing capture endpoints and `org.dropsync.Collector1` service.
- Processor pipeline for readability-cli, monolith, yt-dlp, and gallery-dl with rule-driven overrides.
- TOML configuration (`~/.config/dropsync/config.toml`) and organizer CLI/systemd timer.
- `/capture` web UI, bookmarklet, Hyprland/Niri keybind snippets, and DBus helper scripts.
- pipx packaging, installer scripts, systemd user units, and GitHub Actions workflow.
- Comprehensive documentation covering install, config, usage, security, integrations, and uninstall steps.

[v0.1.0]: https://github.com/WilliamAppleton/DropSync/releases/tag/v0.1.0
