"""HTTP server and collector orchestration for DropSync."""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from starlette.middleware.base import RequestResponseEndpoint

from .config import ConfigManager, DropSyncConfig
from .processors import ProcessorManager, UrlItem
from .rules import ItemContext, RuleApplication, RuleEngine, load_rules
from .utils import (
    ItemPaths,
    build_front_matter,
    build_item_paths,
    decode_base64_to_file,
    domain_from_url,
    infer_item_type_from_url,
    resolve_title,
    sanitize_title,
    utc_timestamp,
    write_text_file,
)

logger = logging.getLogger("dropsync.server")

_FAVICON_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAA1BMVEUAAACnej3aAAAAAXRSTlMAQObYZgAAAApJREFUCNdjYAAAAAIAAeIhvDMAAAAASUVORK5CYII="
)


class UrlPayload(BaseModel):
    url: HttpUrl
    title: str | None = None
    selection: str | None = None
    tags: list[str] | None = None


class NotePayload(BaseModel):
    title: str | None = None
    body: str
    tags: list[str] | None = None


class CodePayload(BaseModel):
    lang: str | None = None
    title: str | None = None
    code: str
    tags: list[str] | None = None


class FilePayload(BaseModel):
    name: str
    content_b64: str
    tags: list[str] | None = None


class ItemResponse(BaseModel):
    path: str
    type: str
    processors: list[str] | None = None


ItemSavedListener = Callable[[Path, str], Awaitable[None] | None]


@dataclass(slots=True)
class SavedItem:
    path: Path
    item_type: str
    processors: list[str]


class Collector:
    """Core business logic for saving captured items."""

    def __init__(
        self,
        config_manager: ConfigManager,
        rule_engine: RuleEngine,
        processor_manager: ProcessorManager,
    ) -> None:
        self.config_manager = config_manager
        self.rule_engine = rule_engine
        self.processor_manager = processor_manager
        self._listeners: set[ItemSavedListener] = set()

    def add_listener(self, listener: ItemSavedListener) -> None:
        self._listeners.add(listener)

    def remove_listener(self, listener: ItemSavedListener) -> None:
        self._listeners.discard(listener)

    def update_rules(self) -> None:
        self.rule_engine = load_rules(self.config_manager.config.root_path)

    async def save_url(self, payload: UrlPayload) -> SavedItem:
        cfg = self.config_manager.config
        timestamp = utc_timestamp()
        domain = domain_from_url(str(payload.url))
        item_type = infer_item_type_from_url(domain)
        title, title_source = await resolve_title(str(payload.url), payload.title, cfg.filename_max_length)
        initial_paths = build_item_paths(cfg.subdirectory_path("links"), timestamp, title)
        rule_application = self._apply_rules(initial_paths.stub, domain, item_type)
        base_dir = cfg.subdirectory_path(rule_application.move_to or "links")
        paths = build_item_paths(base_dir, timestamp, title)

        metadata: dict[str, Any] = {
            "title": title,
            "url": str(payload.url),
            "domain": domain,
            "item_type": item_type,
            "kind": "url",
            "type": item_type,
            "timestamp": timestamp,
            "title_source": title_source,
        }
        tags: set[str] = set(payload.tags or [])

        rule_application = self._apply_rules(paths.stub, domain, item_type)
        tags.update(rule_application.tags)
        if tags:
            metadata["tags"] = sorted(tags)
        if payload.selection:
            metadata["selection"] = payload.selection.strip()

        front_matter = build_front_matter(metadata)
        body_parts = [front_matter]
        if payload.selection:
            body_parts.append(payload.selection.strip())
        body_parts.append("\nCaptured via DropSync.")
        write_text_file(paths.stub, "\n\n".join(body_parts))

        processors = self.processor_manager.queue_for_url(
            UrlItem(
                url=str(payload.url),
                paths=paths,
                domain=domain,
                item_type=item_type,
            ),
            extra_processors=rule_application.post,
        )
        saved = SavedItem(path=paths.stub, item_type="url", processors=processors)
        await self._notify(saved)
        return saved

    async def save_note(self, payload: NotePayload) -> SavedItem:
        cfg = self.config_manager.config
        timestamp = utc_timestamp()
        title = payload.title or payload.body.splitlines()[0][: cfg.filename_max_length]
        title = sanitize_title(title, cfg.filename_max_length)
        base_dir = cfg.subdirectory_path("notes")
        path = build_item_paths(base_dir, timestamp, title).stub

        metadata = {
            "title": title,
            "kind": "note",
            "type": "note",
            "timestamp": timestamp,
        }
        if payload.tags:
            metadata["tags"] = payload.tags

        content = f"{build_front_matter(metadata)}\n\n{payload.body.strip()}\n"
        write_text_file(path, content)
        saved = SavedItem(path=path, item_type="note", processors=[])
        await self._notify(saved)
        return saved

    async def save_code(self, payload: CodePayload) -> SavedItem:
        cfg = self.config_manager.config
        timestamp = utc_timestamp()
        title = payload.title or payload.lang or "snippet"
        title = sanitize_title(title, cfg.filename_max_length)
        base_dir = cfg.subdirectory_path("code")
        path = build_item_paths(base_dir, timestamp, title).stub

        metadata = {
            "title": title,
            "kind": "code",
            "type": payload.lang or "code",
            "timestamp": timestamp,
        }
        if payload.lang:
            metadata["language"] = payload.lang
        if payload.tags:
            metadata["tags"] = payload.tags

        code_block = payload.code.rstrip()
        fence = payload.lang or ""
        body = f"{build_front_matter(metadata)}\n\n```{fence}\n{code_block}\n```\n"
        write_text_file(path, body)
        saved = SavedItem(path=path, item_type="code", processors=[])
        await self._notify(saved)
        return saved

    async def save_file(self, payload: FilePayload) -> SavedItem:
        cfg = self.config_manager.config
        timestamp = utc_timestamp()
        name = sanitize_title(payload.name, cfg.filename_max_length)
        extension = Path(payload.name).suffix
        base_dir = cfg.subdirectory_path("files")
        path = build_item_paths(base_dir, timestamp, name).stub
        if extension:
            path = path.with_suffix(extension)
        decode_base64_to_file(payload.content_b64, path)
        saved = SavedItem(path=path, item_type="file", processors=[])
        await self._notify(saved)
        return saved

    def _apply_rules(self, path: Path, domain: str, item_type: str) -> RuleApplication:
        extension = path.suffix.lstrip(".") if path.suffix else None
        return self.rule_engine.apply(
            ItemContext(
                path=path,
                domain=domain,
                item_type=item_type,
                extension=extension,
            )
        )

    async def _notify(self, item: SavedItem) -> None:
        for listener in list(self._listeners):
            try:
                maybe_awaitable = listener(item.path, item.item_type)
                if asyncio.iscoroutine(maybe_awaitable):
                    await maybe_awaitable
            except Exception:  # pylint: disable=broad-except
                logger.exception("Listener failed for %s", item.path)


class AppState:
    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.processor_manager = ProcessorManager(self.config_manager)
        self.rule_engine = load_rules(self.config_manager.config.root_path)
        self.collector = Collector(
            config_manager=self.config_manager,
            rule_engine=self.rule_engine,
            processor_manager=self.processor_manager,
        )

    def reload(self) -> DropSyncConfig:
        config = self.config_manager.reload()
        self.config_manager.ensure_directories()
        self.rule_engine = load_rules(config.root_path)
        self.collector.rule_engine = self.rule_engine
        return config


app_state = AppState()


def get_collector() -> Collector:
    return app_state.collector


def get_config() -> DropSyncConfig:
    return app_state.config_manager.config


def create_app() -> FastAPI:
    app = FastAPI(title="DropSync", version="0.1.0")

    config = app_state.config_manager.config
    if config.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    webui_dir = Path(__file__).parent / "webui"
    app.mount("/static", StaticFiles(directory=str(webui_dir)), name="static")

    @app.on_event("startup")
    async def _startup() -> None:
        app_state.config_manager.ensure_directories()

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        config = get_config()
        if config.auth_token:
            token = request.headers.get("Authorization", "")
            if token != f"Bearer {config.auth_token}":
                return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        response = await call_next(request)
        return response

    @app.post("/url", response_model=ItemResponse)
    async def post_url(payload: UrlPayload, collector: Collector = Depends(get_collector)) -> ItemResponse:
        saved = await collector.save_url(payload)
        return ItemResponse(
            path=str(saved.path),
            type=saved.item_type,
            processors=saved.processors,
        )

    @app.post("/note", response_model=ItemResponse)
    async def post_note(payload: NotePayload, collector: Collector = Depends(get_collector)) -> ItemResponse:
        saved = await collector.save_note(payload)
        return ItemResponse(path=str(saved.path), type=saved.item_type, processors=[])

    @app.post("/code", response_model=ItemResponse)
    async def post_code(payload: CodePayload, collector: Collector = Depends(get_collector)) -> ItemResponse:
        saved = await collector.save_code(payload)
        return ItemResponse(path=str(saved.path), type=saved.item_type, processors=[])

    @app.post("/file", response_model=ItemResponse)
    async def post_file(payload: FilePayload, collector: Collector = Depends(get_collector)) -> ItemResponse:
        saved = await collector.save_file(payload)
        return ItemResponse(path=str(saved.path), type=saved.item_type, processors=[])

    @app.get("/health")
    async def get_health(config: DropSyncConfig = Depends(get_config)) -> dict[str, Any]:
        return {
            "status": "ok",
            "root": str(config.root_path),
            "bind_host": config.bind_host,
            "port": config.port,
        }

    @app.post("/config/reload")
    async def post_config_reload() -> JSONResponse:
        config = app_state.reload()
        return JSONResponse({"status": "reloaded", "root": str(config.root_path)})

    @app.get("/favicon.ico")
    async def get_favicon() -> Response:
        return Response(content=_FAVICON_BYTES, media_type="image/png")

    @app.get("/capture")
    async def get_capture_page() -> FileResponse:
        return FileResponse(webui_dir / "capture.html")

    return app


app = create_app()


__all__ = ["create_app", "app", "Collector", "get_config", "get_collector"]
