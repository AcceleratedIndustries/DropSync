# Configuration

DropSync reads configuration from `~/.config/dropsync/config.toml` (or `DROPSYNC_CONFIG`). Environment variable `DROPSYNC_ROOT` overrides the root path regardless of file contents.

## Top-level options

| Key | Default | Description |
|-----|---------|-------------|
| `root` | `~/Sync/Collect` | Base directory for captured items |
| `bind_host` | `127.0.0.1` | Host for FastAPI server; change to `0.0.0.0` only when `allow_lan=true` and a token is configured |
| `port` | `8765` | HTTP port |
| `allow_lan` | `false` | Informational; all security is enforced via `bind_host` + `auth_token` |
| `auth_token` | unset | Bearer token; when set, requests must include `Authorization: Bearer <token>` |
| `cors_origins` | `[]` | List of origins for cross-origin requests; **required for bookmarklets** (e.g., `["*"]` when bound to localhost) |
| `filename_max_length` | `120` | Maximum characters kept from sanitized titles |
| `timezone` | unset | Reserved for future localized timestamps |

## Subdirectories

The `subdirectories` table maps logical buckets to folder names relative to `root`.

```toml
[subdirectories]
links = "links"
notes = "notes"
code = "code"
files = "files"
media = "media"
scratch = "scratch"
```

All directories are created automatically by `dropsync run` or `dropsync config init`.

## Processors

Each processor can be toggled or customized via command arrays.

```toml
[processors.readability]
enabled = true
command = ["readability-cli"]

[processors.monolith]
enabled = true
command = ["monolith", "--isolate", "--no-js"]

[processors.yt_dlp]
enabled = true
command = [
  "yt-dlp",
  "--write-info-json",
  "--write-thumbnail",
  "-o",
  "%(title).200B.%(ext)s",
]

[processors.gallery_dl]
enabled = true
command = ["gallery-dl", "-D", "."]
```

Command arrays are passed directly to `asyncio.create_subprocess_exec`. Modify them to add proxies, rate limits, or alternate output destinations.

## Environment overrides

- `DROPSYNC_CONFIG=/path/to/config.toml`
- `DROPSYNC_ROOT=/new/root`

Environment variables take precedence over file values and are effective immediately after `dropsync config reload` or service restart.

## Default file structure

Each capture generates filenames in the form `YYYYMMDD-HHMMSS--Title.ext`. Collisions append `--hash8`. Associated files:

- Stub markdown: `*.md`
- Readability output: `*.readable.md`
- Monolith snapshot: `*.single.html`

Adjust the default rule set via `~/.dropsync/rules.toml` (documented in [`RULES.md`](RULES.md)).
