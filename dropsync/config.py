"""Configuration management for DropSync."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
import tomllib
from pydantic import BaseModel, Field, ValidationError

def _expand_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    try:
        return path.resolve()
    except FileNotFoundError:
        return path


def _default_root() -> Path:
    env_root = os.environ.get("DROPSYNC_ROOT")
    if env_root:
        return _expand_path(env_root)
    return _expand_path(Path.home() / "Sync" / "Collect")


class ProcessorConfig(BaseModel):
    enabled: bool = True
    command: list[str] = Field(default_factory=list)


class ProcessorsConfig(BaseModel):
    readability: ProcessorConfig = Field(
        default_factory=lambda: ProcessorConfig(
            enabled=True, command=["readability-cli"]
        )
    )
    monolith: ProcessorConfig = Field(
        default_factory=lambda: ProcessorConfig(
            enabled=True, command=["monolith", "--isolate", "--no-js"]
        )
    )
    yt_dlp: ProcessorConfig = Field(
        default_factory=lambda: ProcessorConfig(
            enabled=True,
            command=[
                "yt-dlp",
                "--write-info-json",
                "--write-thumbnail",
                "-o",
                "%(title).200B.%(ext)s",
            ],
        )
    )
    gallery_dl: ProcessorConfig = Field(
        default_factory=lambda: ProcessorConfig(
            enabled=True,
            command=["gallery-dl", "-D", "."],
        )
    )


class DropSyncConfig(BaseModel):
    root: Path = Field(default_factory=_default_root)
    bind_host: str = "127.0.0.1"
    port: int = 8765
    allow_lan: bool = False
    auth_token: Optional[str] = None
    cors_origins: list[str] = Field(default_factory=list)
    subdirectories: Dict[str, str] = Field(
        default_factory=lambda: {
            "links": "links",
            "notes": "notes",
            "code": "code",
            "files": "files",
            "media": "media",
            "scratch": "scratch",
        }
    )
    processors: ProcessorsConfig = Field(default_factory=ProcessorsConfig)
    filename_max_length: int = 120
    timezone: Optional[str] = None

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def root_path(self) -> Path:
        return _expand_path(self.root)

    def subdirectory_path(self, key: str) -> Path:
        folder = self.subdirectories.get(key, key)
        return self.root_path / folder

    @property
    def config_dir(self) -> Path:
        return _expand_path(Path.home() / ".config" / "dropsync")


DEFAULT_CONFIG_TEMPLATE = """# DropSync configuration file (TOML)
# Root path where captured items will be stored (defaults to ~/Sync/Collect)
# root = "~/Sync/Collect"

# bind_host = "127.0.0.1"
# port = 8765
# allow_lan = false
# auth_token = ""

[subdirectories]
links = "links"
notes = "notes"
code = "code"
files = "files"
media = "media"
scratch = "scratch"

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
"""


class ConfigManager:
    """Load, cache, and persist DropSync configuration."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = self._resolve_config_path(config_path)
        self._config = self._load()

    @staticmethod
    def _resolve_config_path(config_path: Optional[Path]) -> Path:
        if env_path := os.environ.get("DROPSYNC_CONFIG"):
            return _expand_path(env_path)
        if config_path is not None:
            return _expand_path(config_path)
        return _expand_path(Path.home() / ".config" / "dropsync" / "config.toml")

    def _read_raw(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            return tomllib.loads(self.config_path.read_text())
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise RuntimeError(f"Failed to read config: {exc}") from exc

    def _load(self) -> DropSyncConfig:
        data = self._read_raw()
        try:
            config = DropSyncConfig.model_validate(data)
        except ValidationError as exc:
            raise RuntimeError(f"Invalid configuration: {exc}") from exc
        # Apply env override for root after validation to keep pydantic type conversions.
        env_root = os.environ.get("DROPSYNC_ROOT")
        if env_root:
            config.root = _expand_path(env_root)
        return config

    @property
    def config(self) -> DropSyncConfig:
        return self._config

    def reload(self) -> DropSyncConfig:
        self._config = self._load()
        return self._config

    def ensure_directories(self) -> None:
        cfg = self.config
        root = cfg.root_path
        root.mkdir(parents=True, exist_ok=True)
        for path in cfg.subdirectories.values():
            (root / path).mkdir(parents=True, exist_ok=True)
        (root / ".dropsync").mkdir(parents=True, exist_ok=True)

    def write_default_config(self, force: bool = False) -> Path:
        target = self.config_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not force:
            raise FileExistsError(f"Config already exists at {target}")
        target.write_text(DEFAULT_CONFIG_TEMPLATE)
        return target

    def dump(self) -> Dict[str, Any]:
        return self.config.model_dump()


__all__ = ["ConfigManager", "DropSyncConfig", "DEFAULT_CONFIG_TEMPLATE"]
