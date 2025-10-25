from __future__ import annotations

import os
from pathlib import Path

from dropsync.config import ConfigManager, DropSyncConfig


def test_env_overrides_root(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text("root = \"~/Example\"")

    root = tmp_path / "root"
    monkeypatch.setenv("DROPSYNC_CONFIG", str(config_path))
    monkeypatch.setenv("DROPSYNC_ROOT", str(root))

    manager = ConfigManager()
    assert manager.config.root_path == root.resolve()


def test_write_default_config(tmp_path, monkeypatch):
    required_path = tmp_path / "dropsync" / "config.toml"
    monkeypatch.setenv("DROPSYNC_CONFIG", str(required_path))

    manager = ConfigManager(required_path)
    written = manager.write_default_config(force=True)
    assert written.exists()
    config = DropSyncConfig.model_validate({})
    assert config.filename_max_length == 120
