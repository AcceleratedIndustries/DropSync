from __future__ import annotations

import importlib
from pathlib import Path

import httpx
import pytest


@pytest.mark.asyncio
async def test_post_url_creates_stub(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    root = tmp_path / "Collect"
    config_path.write_text(f"root = \"{root}\"\n")
    monkeypatch.setenv("DROPSYNC_CONFIG", str(config_path))
    monkeypatch.setenv("DROPSYNC_ROOT", str(root))

    import dropsync.server as server_module

    importlib.reload(server_module)

    recorded = []

    def fake_queue(item, extra_processors, force=False):  # type: ignore[signature-diff]
        recorded.append((item.url, list(extra_processors), force))
        return ["readability"]

    server_module.app_state.processor_manager.queue_for_url = fake_queue  # type: ignore[assignment]

    async with httpx.AsyncClient(app=server_module.app, base_url="http://test") as client:
        response = await client.post(
            "/url",
            json={"url": "https://example.com/test", "title": "Example"},
        )
    assert response.status_code == 200

    files = list((root / "links").glob("*.md"))
    assert files, "stub markdown not created"
    assert recorded
