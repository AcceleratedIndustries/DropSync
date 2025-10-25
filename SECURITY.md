# Security

DropSync is intentionally local-first. By default:

- The FastAPI server binds to `127.0.0.1:8765`.
- No authentication is required (loopback only).
- CORS is disabled.
- The DBus service is session-scoped.

## LAN access

To expose the service on your LAN:

1. Set `bind_host = "0.0.0.0"` (or a specific interface) in `config.toml`.
2. Configure a strong `auth_token`. All HTTP requests must include:
   
   ```http
   Authorization: Bearer <token>
   ```

3. (Optional) Adjust `cors_origins` to allow browser-based capture from other devices. Supply full origins, e.g. `"http://192.168.1.10:3000"`.

Restart the service or call `/config/reload` after changes. Treat the token like a password—any client with it can write files to your Syncthing folder.

## HTTPS / reverse proxies

For remote access, place DropSync behind an HTTPS-capable reverse proxy (Caddy, nginx, Traefik). Terminate TLS at the proxy and forward to `127.0.0.1:8765`. Ensure the proxy adds the bearer token (or use an auth gateway like Authelia).

## Process isolation

Enrichment helpers (`readability-cli`, `monolith`, `yt-dlp`, `gallery-dl`) are launched as subprocesses under your user. They inherit your environment and can access the filesystem. Keep them updated and prefer trusted binaries.

## Permissions

Captured data stays inside `root` (default `~/Sync/Collect`). Set Syncthing ignore rules if you store sensitive material that should not sync to all devices.

## DBus considerations

The session bus is per-user. Other local processes can call `SaveUrl` etc. If you require stricter controls, rely on the HTTP interface with a bearer token and restrict DBus access via policy rules.
