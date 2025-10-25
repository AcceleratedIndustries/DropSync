# Usage

DropSync exposes both HTTP endpoints and a DBus session service. The CLI offers helper commands for configuration, diagnostics, and manual organizer runs.

## HTTP API

All endpoints default to `http://127.0.0.1:8765`. Set `Authorization: Bearer <token>` if you enable authentication.

### `POST /url`

```bash
curl -X POST http://127.0.0.1:8765/url \
  -H 'Content-Type: application/json' \
  -d '{
        "url": "https://example.com/post",
        "title": "Example Post",
        "selection": "important clip"
      }'
```

Creates `links/YYYYMMDD-HHMMSS--Example Post.md` with YAML front matter plus optional selection body. Automatically triggers readability, monolith, and media processors based on heuristics and rules.

### `POST /note`

```bash
curl -X POST http://127.0.0.1:8765/note \
  -H 'Content-Type: application/json' \
  -d '{"body": "Remember to water the plants."}'
```

Saved to `notes/` as Markdown with front matter.

### `POST /code`

```bash
curl -X POST http://127.0.0.1:8765/code \
  -H 'Content-Type: application/json' \
  -d '{
        "lang": "python",
        "code": "print(\"Hello DropSync\")"
      }'
```

Creates a Markdown file with fenced code block in `code/`.

### `POST /file`

```bash
base64 screenshot.png | tr -d '\n' > screenshot.b64
curl -X POST http://127.0.0.1:8765/file \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"screenshot.png\",\"content_b64\":\"$(cat screenshot.b64)\"}"
```

Binary payloads land in `files/` using the standard filename algorithm.

### `POST /config/reload`

Reload configuration and rules without restarting the daemon.

```bash
curl -X POST http://127.0.0.1:8765/config/reload
```

### `GET /health`

Returns status, root path, and current bind host/port.

### `GET /capture`

Serves the static web UI (`capture.html`).

## DBus service

Service name `org.dropsync.Collector1`, object `/org/dropsync/Collector1`.

### SaveUrl

```bash
gdbus call \
  --session \
  --dest org.dropsync.Collector1 \
  --object-path /org/dropsync/Collector1 \
  --method org.dropsync.Collector1.SaveUrl \
  "https://example.com" \
  "Optional Title" \
  "Highlighted text" \
  "{}"
```

### SaveNote / SaveCode / SaveFile

Arguments mirror the HTTP payloads. The final `a{sv}` dictionary is reserved for future options—pass `{}`.

### Signals

The service emits `ItemSaved(path, type)` after each capture, allowing integrations to react without polling.

## CLI recap

```bash
# Start the daemon (normally handled by systemd)
dropsync run

# Health check helpers
dropsync doctor

# Show config including env overrides
dropsync config print

# Write default config (fails if file exists unless --force)
dropsync config init

# Run organizer manually
dropsync organize --force
```

Run `dropsync --help` for the full command tree.
