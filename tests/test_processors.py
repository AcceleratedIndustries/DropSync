from __future__ import annotations

from pathlib import Path

import pytest

from dropsync.config import ConfigManager
from dropsync.processors import ProcessorManager, UrlItem
from dropsync.utils import ItemPaths


@pytest.fixture
def processor_manager(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    root = tmp_path / "root"
    root.mkdir()
    config_path.write_text(f"root = \"{root}\"\n")
    monkeypatch.setenv("DROPSYNC_CONFIG", str(config_path))

    manager = ConfigManager()
    return ProcessorManager(manager)


def test_queue_for_article(processor_manager, tmp_path, monkeypatch):
    recorded = []

    def fake_schedule(job):
        recorded.append(job)
        return True

    monkeypatch.setattr(processor_manager, "_schedule", fake_schedule)

    stub = tmp_path / "links" / "20240513-000000--Example.md"
    stub.parent.mkdir(parents=True, exist_ok=True)
    paths = ItemPaths(
        stub=stub,
        readable=stub.with_suffix(".readable.md"),
        singlefile=stub.with_suffix(".single.html"),
    )

    item = UrlItem(
        url="https://example.com/article",
        paths=paths,
        domain="example.com",
        item_type="article",
    )

    scheduled = processor_manager.queue_for_url(item, extra_processors=[])
    names = [job.name for job in recorded]
    assert "readability" in names
    assert "monolith" in names
    assert "readability" in scheduled


def test_queue_for_video(processor_manager, tmp_path, monkeypatch):
    recorded = []

    def fake_schedule(job):
        recorded.append(job)
        return True

    monkeypatch.setattr(processor_manager, "_schedule", fake_schedule)

    stub = tmp_path / "links" / "20240513-000000--Video.md"
    stub.parent.mkdir(parents=True, exist_ok=True)
    paths = ItemPaths(
        stub=stub,
        readable=stub.with_suffix(".readable.md"),
        singlefile=stub.with_suffix(".single.html"),
    )

    item = UrlItem(
        url="https://youtube.com/watch?v=abc",
        paths=paths,
        domain="youtube.com",
        item_type="video",
    )

    scheduled = processor_manager.queue_for_url(item, extra_processors=[])
    names = [job.name for job in recorded]
    assert "yt-dlp" in names
    assert "readability" in names
    assert "yt-dlp" in scheduled


def test_queue_skips_when_schedule_fails(processor_manager, tmp_path, monkeypatch):
    def fake_schedule(job):
        return False

    monkeypatch.setattr(processor_manager, "_schedule", fake_schedule)

    stub = tmp_path / "links" / "20240513-000000--Example.md"
    stub.parent.mkdir(parents=True, exist_ok=True)
    paths = ItemPaths(
        stub=stub,
        readable=stub.with_suffix(".readable.md"),
        singlefile=stub.with_suffix(".single.html"),
    )

    item = UrlItem(
        url="https://example.com/article",
        paths=paths,
        domain="example.com",
        item_type="article",
    )

    scheduled = processor_manager.queue_for_url(item, extra_processors=[])
    assert scheduled == []
