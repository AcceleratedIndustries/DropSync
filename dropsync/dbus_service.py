"""DBus integration for DropSync."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method, signal

from .server import CodePayload, Collector, FilePayload, NotePayload, UrlPayload

logger = logging.getLogger("dropsync.dbus")

BUS_NAME = "org.dropsync.Collector1"
OBJECT_PATH = "/org/dropsync/Collector1"
INTERFACE_NAME = "org.dropsync.Collector1"


class CollectorInterface(ServiceInterface):
    def __init__(self, collector: Collector) -> None:
        super().__init__(INTERFACE_NAME)
        self.collector = collector

    @method()
    async def SaveUrl(self, url: "s", title: "s", selection: "s", opts: "a{sv}") -> "s":
        payload = UrlPayload(url=url, title=title or None, selection=selection or None)
        result = await self.collector.save_url(payload)
        return str(result.path)

    @method()
    async def SaveNote(self, title: "s", body: "s", opts: "a{sv}") -> "s":
        payload = NotePayload(title=title or None, body=body)
        result = await self.collector.save_note(payload)
        return str(result.path)

    @method()
    async def SaveCode(self, lang: "s", title: "s", code: "s", opts: "a{sv}") -> "s":
        payload = CodePayload(lang=lang or None, title=title or None, code=code)
        result = await self.collector.save_code(payload)
        return str(result.path)

    @method()
    async def SaveFile(self, name: "s", content_b64: "s", opts: "a{sv}") -> "s":
        payload = FilePayload(name=name, content_b64=content_b64)
        result = await self.collector.save_file(payload)
        return str(result.path)

    @signal()
    def ItemSaved(self, path: "s", item_type: "s") -> "ss":
        return [path, item_type]


class DropSyncDBusService:
    """Manage lifecycle of the DropSync DBus service."""

    def __init__(self, collector: Collector) -> None:
        self.collector = collector
        self._bus: Optional[MessageBus] = None
        self._interface = CollectorInterface(collector)
        self.collector.add_listener(self._emit_signal)

    async def start(self) -> None:
        logger.info("Starting DBus service: %s", BUS_NAME)
        self._bus = await MessageBus().connect()
        self._bus.export(OBJECT_PATH, self._interface)
        await self._bus.request_name(BUS_NAME)

    async def stop(self) -> None:
        self.collector.remove_listener(self._emit_signal)
        if self._bus is None:
            return
        try:
            await self._bus.wait_for_disconnect()
        except asyncio.CancelledError:
            pass
        self._bus = None

    def _emit_signal(self, path: Path, item_type: str) -> None:
        try:
            self._interface.ItemSaved(str(path), item_type)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Failed to emit DBus ItemSaved signal")


__all__ = ["DropSyncDBusService", "BUS_NAME", "OBJECT_PATH", "INTERFACE_NAME"]
