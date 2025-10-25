"""Utility helpers for DropSync."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

import httpx


SAFE_FILENAME_PATTERN = re.compile(r"[^\w\s._-]")
MULTISPACE_PATTERN = re.compile(r"\s+")


@dataclass(slots=True)
class TitleMetadata:
    title: str
    source: str


class _MetaTitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta_title: Optional[str] = None
        self.h1_title: Optional[str] = None
        self.page_title: Optional[str] = None
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "meta":
            attr_map = {name.lower(): (value or "") for name, value in attrs}
            prop = attr_map.get("property") or attr_map.get("name")
            content = attr_map.get("content")
            if prop and content:
                prop_lower = prop.lower()
                if prop_lower in {"og:title", "twitter:title"} and not self.meta_title:
                    self.meta_title = content.strip()
        elif tag.lower() == "h1":
            self._in_h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            if not self.h1_title:
                self.h1_title = data.strip()
        if not self.page_title:
            self.page_title = data.strip()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def sanitize_title(raw_title: str, max_length: int = 120) -> str:
    title = raw_title.strip()
    title = title.replace("/", "-")
    title = SAFE_FILENAME_PATTERN.sub(" ", title)
    title = MULTISPACE_PATTERN.sub(" ", title)
    title = title.replace("\\", "-")
    title = title.strip(" .-")
    if len(title) > max_length:
        title = title[: max_length].rstrip()
    return title or "untitled"


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    slug_parts = [part for part in parsed.path.split("/") if part]
    if slug_parts:
        candidate = slug_parts[-1]
        candidate = re.sub(r"\W+", " ", candidate)
        candidate = candidate.replace("_", " ")
        candidate = candidate.strip()
        if candidate:
            return candidate
    return parsed.netloc or "untitled"


async def fetch_title_from_url(url: str, timeout: float = 3.0) -> Optional[TitleMetadata]:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "DropSync/0.1"})
            response.raise_for_status()
    except httpx.HTTPError:
        return None
    parser = _MetaTitleParser()
    parser.feed(response.text[:20000])
    if parser.meta_title:
        return TitleMetadata(title=parser.meta_title, source="meta")
    if parser.h1_title:
        return TitleMetadata(title=parser.h1_title, source="h1")
    if parser.page_title:
        return TitleMetadata(title=parser.page_title, source="title")
    return None


async def resolve_title(
    url: str,
    provided_title: Optional[str],
    max_length: int,
) -> tuple[str, str]:
    if provided_title:
        sanitized = sanitize_title(provided_title, max_length=max_length)
        return sanitized, "provided"
    metadata = await fetch_title_from_url(url)
    if metadata:
        return sanitize_title(metadata.title, max_length=max_length), metadata.source
    slug = slug_from_url(url)
    return sanitize_title(slug, max_length=max_length), "slug"


def unique_filename(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path
    counter = hashlib.sha256(str(base_path).encode("utf-8")).hexdigest()[:8]
    new_name = f"{base_path.stem}--{counter}{base_path.suffix}"
    return base_path.with_name(new_name)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text_file(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def decode_base64_to_file(content_b64: str, path: Path) -> None:
    ensure_directory(path.parent)
    data = base64.b64decode(content_b64)
    path.write_bytes(data)


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def infer_item_type_from_url(domain: str) -> str:
    video_domains = {
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "vimeo.com",
        "www.vimeo.com",
        "odysee.com",
    }
    media_galleries = {
        "imgur.com",
        "www.imgur.com",
        "reddit.com",
        "www.reddit.com",
        "pixiv.net",
    }
    if domain in video_domains:
        return "video"
    if domain in media_galleries:
        return "gallery"
    return "article"


@dataclass(slots=True)
class ItemPaths:
    stub: Path
    readable: Path
    singlefile: Path


def build_item_paths(base_dir: Path, timestamp: str, title: str) -> ItemPaths:
    safe_title = sanitize_title(title)
    stub_path = unique_filename(base_dir / f"{timestamp}--{safe_title}.md")
    readable_path = stub_path.with_suffix(".readable.md")
    single_path = stub_path.with_suffix(".single.html")
    return ItemPaths(stub=stub_path, readable=readable_path, singlefile=single_path)


def build_front_matter(metadata: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, (list, tuple, set)):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---\n")
    return "\n".join(lines)


__all__ = [
    "utc_timestamp",
    "sanitize_title",
    "slug_from_url",
    "fetch_title_from_url",
    "resolve_title",
    "unique_filename",
    "ensure_directory",
    "write_text_file",
    "decode_base64_to_file",
    "domain_from_url",
    "infer_item_type_from_url",
    "build_item_paths",
    "build_front_matter",
    "TitleMetadata",
]
