# Rules Engine

Rules customize how DropSync handles captured URLs. Place your file at `<root>/.dropsync/rules.toml` (default `~/Sync/Collect/.dropsync/rules.toml`). A starter version is available in [`examples/rules.toml`](examples/rules.toml).

## Structure

```toml
[[rules]]
domain = ["youtube.com", "youtu.be"]
type = "video"
move_to = "media"
add_tags = ["video", "youtube"]
post = ["yt-dlp"]
```

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string or array | Match one or more domains (case-insensitive). Omit to apply to all domains. |
| `type` | string | Match the detected item type (`article`, `video`, `gallery`, etc.). |
| `ext` | string | Match original stub extension (rare; useful for custom types). |
| `move_to` | string | Target subdirectory (key from config or literal folder name under `root`). |
| `add_tags` | array | Tags appended to front matter. |
| `post` | array | Additional processors to queue (`readability`, `monolith`, `yt-dlp`, `gallery-dl`). |

Rules are evaluated in order; multiple rules can match the same item. Tags accumulate, `move_to` overrides previous values, and `post` processors append.

## Item types

DropSync infers type via domain heuristics:

- `video`: YouTube, Vimeo, Odysee (yt-dlp).
- `gallery`: Imgur, Reddit, Pixiv (gallery-dl + monolith).
- `article`: Everything else (readability + monolith).

Your rules can refine this (e.g., set `type = "article"` for a video site to disable heavy downloads).

## Organizer

The nightly organizer (`dropsync organize`) re-applies rules to existing files:

1. Moves stubs (and companion files) to the configured `move_to` directory.
2. Triggers missing processors unless artifacts already exist (use `--force` to re-run).
3. Ensures `.dropsync/` exists for rules/state.

The organizer does not delete files—review changes in `journalctl --user -u dropsync-organize.service` or run `dropsync organize` manually for verbose output.

## Tips

- Keep `move_to` values relative to the DropSync root (`media`, `links/articles`, etc.).
- Use tags to group items downstream (front matter is YAML friendly).
- Combine with Syncthing ignores to prevent large `media/` directories from syncing to devices that do not need them.

When editing rules, run:

```bash
curl -X POST http://127.0.0.1:8765/config/reload
```

to reload without restarting the service.
