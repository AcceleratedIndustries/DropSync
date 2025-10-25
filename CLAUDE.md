# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DropSync is a local-first inbox for links, notes, files, and code. It's a FastAPI + DBus daemon that captures content from browsers, hotkeys, or DBus, enriches it with readability and full-page snapshots, and syncs everything into a Syncthing-friendly folder structure.

**Tech Stack**: Python 3.11+, FastAPI, Typer, Pydantic, dbus-next, Uvicorn, httpx
**Build System**: Hatchling
**Quality Tools**: Ruff (linting), Black (formatting), MyPy (type checking), Pytest (testing)

## Common Commands

### Development
```bash
make fmt              # Format code with ruff and black
make lint             # Run linting (ruff, black --check, mypy)
make test             # Run pytest
make clean            # Remove cache directories
```

### Installation & Service Management
```bash
make pipx             # Install via pipx (force reinstall)
make install-arch     # Install on Arch Linux (system deps + pipx)
make install-debian   # Install on Debian (system deps + pipx)
make install-macos    # Install on macOS (system deps + pipx)
make service          # Enable systemd user services
```

### Running
```bash
dropsync run          # Launch the FastAPI + DBus daemon
dropsync organize     # Apply rules, move files, queue missing processors
dropsync organize --force  # Re-run all processors regardless of existing artifacts
dropsync doctor       # Check external dependencies
dropsync config print # Show effective configuration
dropsync config init  # Scaffold default config.toml
```

### Testing Individual Components
```bash
pytest tests/test_server.py           # Test HTTP API and Collector
pytest tests/test_processors.py       # Test ProcessorManager
pytest tests/test_rules.py           # Test RuleEngine
pytest tests/test_config.py          # Test configuration loading
pytest tests/test_utils.py           # Test utility functions
pytest -k "test_name"                # Run specific test
pytest -v                            # Verbose output
```

## Architecture

### Core Components

**Entry Points**:
- `dropsync/cli.py` - Typer CLI application; defines `dropsync` and `dropsyncd` commands
- `dropsync/server.py` - FastAPI application, HTTP endpoints, Collector class

**Data Flow**:
1. **Capture** → HTTP POST, bookmarklet, DBus, or web UI (`/capture`)
2. **Extract** → Title resolved from meta tags, H1, or URL slug (async via httpx)
3. **Save** → YAML front-matter markdown stub written to `~/Sync/Collect/{links|notes|code}/`
4. **Enrich** → Background processors run asynchronously (readability-cli, monolith, yt-dlp, gallery-dl)
5. **Organize** → Nightly organizer re-applies rules, moves files, queues missing processors
6. **Sync** → Syncthing picks up files automatically

### Key Modules

| Module | Purpose |
|--------|---------|
| **server.py** | FastAPI app, Collector orchestration, AppState management, HTTP endpoints |
| **config.py** | Pydantic-based configuration, TOML parsing, environment variable support |
| **processors.py** | ProcessorManager - async subprocess orchestration for external tools |
| **rules.py** | RuleEngine - domain/type/extension matching, organizer for re-processing files |
| **dbus_service.py** | DBus service (`org.dropsync.Collector1`) for KDE/GNOME integration |
| **utils.py** | Title extraction, filename sanitization, URL parsing, front-matter generation |
| **webui/** | Static HTML/CSS/JS for `/capture` page |

### Async Architecture

- **Non-blocking processors**: ProcessorManager uses asyncio.create_task() to run external commands without blocking the HTTP server
- **Task lifecycle**: Tasks are tracked in `_tasks` set, cleaned up via done_callback
- **Title resolution**: Uses httpx async client to fetch page titles without blocking
- **Collector notifications**: Listener pattern allows DBus service to emit signals when items are saved

### Configuration System

- **Primary config**: `~/.config/dropsync/config.toml` (or `DROPSYNC_CONFIG` env var)
- **Root override**: `DROPSYNC_ROOT` environment variable always takes precedence
- **Rules**: `<root>/.dropsync/rules.toml` for domain/type/extension-based customization
- **Reload endpoint**: `POST /config/reload` reloads config and rules without restarting daemon

### Rules Engine

Rules are TOML-based and support:
- **domain**: Match one or more domains (case-insensitive)
- **type**: Match item type (article, video, gallery)
- **ext**: Match file extension
- **add_tags**: Tags appended to YAML front matter
- **move_to**: Target subdirectory (relative to root)
- **post**: Additional processors to queue

Rules are evaluated in order. Multiple rules can match; tags accumulate, move_to overrides, post processors append.

The organizer (`dropsync organize`) re-applies rules to existing files, moving stubs and companion files, and queuing missing processors.

### Item Types & Processors

**Item type inference** (dropsync/utils.py):
- `video`: YouTube, Vimeo, Odysee → yt-dlp
- `gallery`: Imgur, Reddit, Pixiv → gallery-dl + monolith
- `article`: Everything else → readability + monolith

**Processor behavior**:
- Readability runs on all URLs, outputs to `*.readable.md`
- Monolith saves single-file HTML to `*.single.html` for articles/galleries
- yt-dlp and gallery-dl output to `media/` subdirectory
- Processors skip if output files exist (unless `--force`)
- Missing commands are logged once and cached to avoid spam

### File Naming Convention

Files follow: `YYYYMMDD-HHMMSS--Title.ext`
- Timestamp is UTC (ISO 8601 compact format)
- Titles are sanitized (alphanumeric + limited punctuation)
- Hash suffix added on collision (`--hash8`)
- Companion files: `*.md` (stub), `*.readable.md`, `*.single.html`

## Important Implementation Details

### Code Style
- Line length: 100 characters (enforced by black/ruff)
- Python 3.11+ features: Use modern type hints (e.g., `list[str]` not `List[str]`)
- Type annotations: Required for public functions; mypy strict=false but warn_unused_ignores=true
- Dataclasses: Use slots=True for performance

### Testing Considerations
- Tests use pytest with fixtures for config/managers
- Mock external commands (readability-cli, monolith, etc.) in processor tests
- HTTP tests use FastAPI TestClient
- Config tests verify environment variable precedence

### External Dependencies (Optional)
- `readability-cli` - npm package for article extraction
- `monolith` - Rust binary for single-file HTML snapshots
- `yt-dlp` - Python package for video downloads
- `gallery-dl` - Python package for image gallery downloads

The daemon continues to work if these are missing; processors are skipped with warnings.

### DBus Integration
- Service name: `org.dropsync.Collector1`
- Object path: `/org/dropsync/Collector1`
- Methods: SaveUrl, SaveNote, SaveCode, SaveFile
- Signal: ItemSaved(path: str, item_type: str)
- Only available on Linux with dbus-next installed

### Web UI & CORS
- Built-in capture form at `/capture` (dropsync/webui/capture.html)
- CORS disabled by default; configure `cors_origins` for cross-origin requests
- Bookmarklet available in `examples/bookmarklet.txt`

### Security
- Default: Binds to 127.0.0.1 (localhost only)
- LAN access: Set `bind_host = "0.0.0.0"` AND configure `auth_token`
- Auth middleware: Validates `Authorization: Bearer <token>` header when token is set

## Build & Packaging

- **pyproject.toml**: Uses hatchling build backend
- **Package includes**: systemd units, examples, webui static files (via force-include)
- **Scripts**: `dropsync` (CLI), `dropsyncd` (daemon)
- **Minimum Python**: 3.11 (required for tomllib and modern typing features)

## Release Process

```bash
make publish  # Adds git remote (if needed), pushes to main, creates draft release via gh
```

Release notes template: `RELEASE_TEMPLATE.md`

## Common Pitfalls

1. **Config reload**: Changes to `config.toml` or `rules.toml` require `POST /config/reload` or service restart
2. **Missing processors**: Warnings only appear once; check logs with `journalctl --user -u dropsync.service`
3. **File permissions**: All paths must be writable by the user running the service
4. **Organizer timing**: Nightly timer runs via systemd; manual runs use `dropsync organize`
5. **Rule precedence**: Last matching `move_to` wins; tags and processors accumulate
6. **Processor cache**: ProcessorManager caches command availability; restart daemon if installing new tools
