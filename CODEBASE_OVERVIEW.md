# DropSync Codebase Overview

**Generated:** 2025-10-23

## What This Project Is

DropSync is a **local-first "capture → enrich → sync" companion for Syncthing**. It's a personal information management tool that:

- Accepts URLs, notes, code snippets, and files from multiple sources (HTTP, DBus, web UI, bookmarklet)
- Automatically enriches captured content with readability stubs, full-page HTML snapshots, and media downloads
- Organizes everything into a Syncthing-friendly folder structure that automatically syncs across devices
- Applies rule-based customizations to tag, organize, and post-process items

## Tech Stack

### Main Programming Language and Frameworks

- **Language**: Python 3.11+ (required minimum)
- **Main Frameworks**:
  - **FastAPI** - HTTP API server with async support
  - **Typer** - CLI framework for command-line interface
  - **Pydantic** - Data validation and configuration management
  - **dbus-next** - DBus integration for Linux desktop environment
  - **Uvicorn** - ASGI server for FastAPI
  - **httpx** - Async HTTP client for fetching page titles
- **Build System**: Hatchling (via `pyproject.toml`)
- **Quality Tools**: Ruff (linting), Black (code formatting), MyPy (type checking), Pytest (testing)

### Core Dependencies

From `pyproject.toml`:
- fastapi >= 0.111
- uvicorn[standard] >= 0.29
- typer >= 0.12
- pydantic >= 2.7
- pyyaml >= 6.0
- rich >= 13.7 (CLI formatting)
- dbus-next >= 0.2.3, < 0.3
- httpx >= 0.27

### External Tools (Optional)

- `readability-cli` - Extract readable text from URLs
- `monolith` - Save single-file HTML snapshots
- `yt-dlp` - Download videos
- `gallery-dl` - Download image galleries

### System Integration

- Systemd user units for daemon and nightly organizer
- Syncthing folder sync
- Linux DBus for desktop environment integration (KDE, GNOME)
- Wayland compositor support (Hyprland, Niri)

## Architecture

The architecture follows a modular, async-first design:

```
DropSync Architecture
├── HTTP API Layer (FastAPI)
│   ├── /url - POST URL with optional title/selection
│   ├── /note - POST quick notes
│   ├── /code - POST code snippets
│   ├── /file - POST binary files (base64)
│   ├── /health - Health check
│   ├── /config/reload - Reload configuration
│   └── /capture - Web UI for quick submissions
│
├── DBus Service Layer
│   ├── org.dropsync.Collector1 (DBus service)
│   ├── SaveUrl, SaveNote, SaveCode, SaveFile methods
│   └── ItemSaved signal for event notifications
│
├── Core Business Logic
│   ├── Collector - Orchestrates URL/note/code/file saving
│   ├── ConfigManager - TOML configuration management
│   ├── RuleEngine - Domain/type/extension-based rules
│   ├── ProcessorManager - Async subprocess orchestration
│   └── Web UI - Static HTML/CSS/JS capture interface
│
└── External Processors (async/background)
    ├── readability-cli - Extract article text
    ├── monolith - Single-file HTML snapshots
    ├── yt-dlp - Download videos (YouTube, Vimeo, etc.)
    └── gallery-dl - Download image galleries
```

## Entry Points and Main Files

| File | Purpose |
|------|---------|
| **`dropsync/cli.py`** | Command-line interface (Typer). Entry points: `dropsync` (CLI), `dropsyncd` (daemon) |
| **`dropsync/server.py`** | FastAPI application, HTTP endpoints, Collector class, AppState management |
| **`dropsync/config.py`** | Configuration loading/validation (Pydantic), TOML parsing, path management |
| **`dropsync/dbus_service.py`** | DBus service implementation via dbus-next |
| **`dropsync/processors.py`** | ProcessorManager for async subprocess execution of external tools |
| **`dropsync/rules.py`** | RuleEngine, rule parsing from TOML, organizer for re-processing files |
| **`dropsync/utils.py`** | Utilities: title extraction, filename sanitization, URL parsing, front-matter generation |
| **`dropsync/webui/`** | Static HTML/CSS/JS for `/capture` page |

## Configuration Files

| File | Purpose |
|------|----------|
| **`pyproject.toml`** | Python 3.11+ requirement, FastAPI framework, pipx-first packaging, version 0.1.0 |
| **`systemd/dropsync.service`** | User-level systemd service for daemon auto-start |
| **`systemd/dropsync-organize.timer`** | Nightly organizer runs on schedule |
| **`SPEC.md`** | Formal specification of v0.1.0 deliverables |
| **`RULES.md`** | Rules engine syntax for domain/type/extension matching |
| **`CONFIG.md`** | Configuration schema and environment variables |
| **`.github/workflows/ci.yml`** | GitHub Actions CI pipeline |
| **`Makefile`** | Build targets, install scripts for Arch/Debian/macOS |

## Data Flow

1. **Capture** → User submits URL/note/code via HTTP POST, bookmarklet, DBus, or web UI
2. **Extract** → Title resolved from meta tags, H1, or URL slug (async)
3. **Save** → YAML front-matter markdown stub written to `~/Sync/Collect/{links|notes|code}/`
4. **Enrich** → Background processors (readability-cli, monolith, yt-dlp, gallery-dl) run asynchronously
5. **Organize** → Nightly organizer re-applies rules, moves files, queues missing processors
6. **Sync** → Syncthing picks up files and syncs across devices

## Key Features

- **Multi-input**: HTTP, DBus, bookmarklet, web UI
- **Rule-driven**: TOML-based rules for tagging, moving, post-processing
- **Async-first**: Non-blocking processor orchestration
- **Metadata-rich**: YAML front-matter, domain tracking, timestamps
- **Offline-friendly**: All processing local, Syncthing-compatible
- **Minimal dependencies**: Single binary via pipx, system packages for processors
- **Linux-native**: DBus, systemd, Syncthing integration

## Project Status

- **Version**: 0.1.0
- **Development Status**: Active development
- **Python Version**: 3.11+ required

## Quick Start

```bash
# Install via pipx
pipx install .

# Start daemon
dropsyncd start

# Capture a URL
dropsync url "https://example.com"

# Quick note
dropsync note "Remember to..."

# Code snippet
dropsync code "print('hello')" --lang python
```

## Architecture Notes

This is a well-architected personal knowledge capture system designed specifically for:
- Integration with Syncthing for offline-first workflows
- Minimal dependencies and system resource usage
- Rule-based automation for personal information management
- Linux desktop environment integration via DBus
- Async processing to avoid blocking on slow operations
