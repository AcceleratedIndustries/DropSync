"""Content processors for DropSync."""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .config import ConfigManager, DropSyncConfig
from .utils import ItemPaths, write_text_file

logger = logging.getLogger("dropsync.processors")


@dataclass(slots=True)
class UrlItem:
    url: str
    paths: ItemPaths
    domain: str
    item_type: str


@dataclass(slots=True)
class ProcessorJob:
    name: str
    command: List[str]
    cwd: Path
    capture_stdout_to: Path | None = None


class ProcessorManager:
    """Manage asynchronous processor subprocesses."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self._tasks: set[asyncio.Task[None]] = set()
        self._command_cache: dict[str, bool] = {}
        self._missing_commands_reported: set[str] = set()

    async def shutdown(self) -> None:
        pending = list(self._tasks)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    def queue_for_url(
        self,
        item: UrlItem,
        extra_processors: Sequence[str],
        force: bool = False,
    ) -> list[str]:
        cfg = self.config_manager.config
        scheduled: list[str] = []

        if cfg.processors.readability.enabled and (force or not item.paths.readable.exists()):
            if self._schedule(
                ProcessorJob(
                    name="readability",
                    command=[*cfg.processors.readability.command, item.url],
                    cwd=item.paths.stub.parent,
                    capture_stdout_to=item.paths.readable,
                )
            ):
                scheduled.append("readability")

        if item.item_type == "video" and cfg.processors.yt_dlp.enabled:
            if self._schedule(
                ProcessorJob(
                    name="yt-dlp",
                    command=[*cfg.processors.yt_dlp.command, item.url],
                    cwd=self._media_directory(cfg),
                )
            ):
                scheduled.append("yt-dlp")
        elif item.item_type == "gallery" and cfg.processors.gallery_dl.enabled:
            if self._schedule(
                ProcessorJob(
                    name="gallery-dl",
                    command=[*cfg.processors.gallery_dl.command, item.url],
                    cwd=self._media_directory(cfg),
                )
            ):
                scheduled.append("gallery-dl")

        if (
            cfg.processors.monolith.enabled
            and item.item_type in {"article", "gallery"}
            and (force or not item.paths.singlefile.exists())
        ):
            command = [*cfg.processors.monolith.command, item.url, "-o", str(item.paths.singlefile)]
            if self._schedule(
                ProcessorJob(
                    name="monolith",
                    command=command,
                    cwd=item.paths.stub.parent,
                )
            ):
                scheduled.append("monolith")

        for name in extra_processors:
            if name in scheduled:
                continue
            job = self._job_from_name(name, item, cfg)
            if job is None:
                continue
            if not force:
                if name == "readability" and item.paths.readable.exists():
                    continue
                if name == "monolith" and item.paths.singlefile.exists():
                    continue
            if self._schedule(job):
                scheduled.append(name)

        return scheduled

    def _job_from_name(self, name: str, item: UrlItem, cfg: DropSyncConfig) -> ProcessorJob | None:
        match name:
            case "readability":
                if not cfg.processors.readability.enabled:
                    return None
                return ProcessorJob(
                    name="readability",
                    command=[*cfg.processors.readability.command, item.url],
                    cwd=item.paths.stub.parent,
                    capture_stdout_to=item.paths.readable,
                )
            case "monolith":
                if not cfg.processors.monolith.enabled:
                    return None
                return ProcessorJob(
                    name="monolith",
                    command=[*cfg.processors.monolith.command, item.url, "-o", str(item.paths.singlefile)],
                    cwd=item.paths.stub.parent,
                )
            case "yt-dlp":
                if not cfg.processors.yt_dlp.enabled:
                    return None
                return ProcessorJob(
                    name="yt-dlp",
                    command=[*cfg.processors.yt_dlp.command, item.url],
                    cwd=self._media_directory(cfg),
                )
            case "gallery-dl":
                if not cfg.processors.gallery_dl.enabled:
                    return None
                return ProcessorJob(
                    name="gallery-dl",
                    command=[*cfg.processors.gallery_dl.command, item.url],
                    cwd=self._media_directory(cfg),
                )
            case _:
                logger.warning("Unknown processor requested: %s", name)
                return None

    def _media_directory(self, cfg: DropSyncConfig) -> Path:
        media_dir = cfg.subdirectory_path("media")
        media_dir.mkdir(parents=True, exist_ok=True)
        return media_dir

    def _schedule(self, job: ProcessorJob) -> bool:
        if not self._ensure_command_available(job.command[0], job.name):
            return False
        task = asyncio.create_task(self._run_job(job))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return True

    def _ensure_command_available(self, executable: str, job_name: str) -> bool:
        cached = self._command_cache.get(executable)
        if cached is None:
            cached = shutil.which(executable) is not None
            self._command_cache[executable] = cached
        if not cached and executable not in self._missing_commands_reported:
            config_key = job_name.replace("-", "_")
            logger.warning(
                "Skipping processor %s: command %r not found in PATH. Install it or disable processors.%s.enabled.",
                job_name,
                executable,
                config_key,
            )
            self._missing_commands_reported.add(executable)
        return cached

    async def _run_job(self, job: ProcessorJob) -> None:
        logger.info("Running processor %s: %s", job.name, job.command)
        try:
            process = await asyncio.create_subprocess_exec(
                *job.command,
                cwd=str(job.cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if job.capture_stdout_to and stdout:
                write_text_file(job.capture_stdout_to, stdout.decode("utf-8", errors="ignore"))
            if process.returncode != 0:
                logger.error(
                    "Processor %s exited with %s: %s",
                    job.name,
                    process.returncode,
                    stderr.decode("utf-8", errors="ignore"),
                )
        except FileNotFoundError:
            logger.error("Processor command not found: %s", job.command[0])
        except Exception:  # pylint: disable=broad-except
            logger.exception("Processor %s failed", job.name)


__all__ = ["ProcessorManager", "UrlItem"]
