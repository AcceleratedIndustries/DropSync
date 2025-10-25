"""Rules engine and organizer for DropSync."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set

import tomllib

from .processors import ProcessorManager, UrlItem
from .utils import ItemPaths, domain_from_url


@dataclass(slots=True)
class Rule:
    domains: Set[str] = field(default_factory=set)
    item_type: Optional[str] = None
    extension: Optional[str] = None
    add_tags: Set[str] = field(default_factory=set)
    move_to: Optional[str] = None
    post: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ItemContext:
    path: Path
    domain: str
    item_type: str
    extension: Optional[str] = None


@dataclass(slots=True)
class RuleApplication:
    tags: Set[str] = field(default_factory=set)
    move_to: Optional[str] = None
    post: List[str] = field(default_factory=list)


class RuleEngine:
    """Simple matcher for DropSync rules."""

    def __init__(self, rules: Iterable[Rule]):
        self._rules = list(rules)

    def apply(self, item: ItemContext) -> RuleApplication:
        result = RuleApplication()
        for rule in self._rules:
            if not self._matches(rule, item):
                continue
            result.tags.update(rule.add_tags)
            if rule.move_to:
                result.move_to = rule.move_to
            if rule.post:
                result.post.extend(rule.post)
        return result

    @staticmethod
    def _matches(rule: Rule, item: ItemContext) -> bool:
        if rule.domains and item.domain not in rule.domains:
            return False
        if rule.item_type and rule.item_type != item.item_type:
            return False
        if rule.extension and item.extension != rule.extension:
            return False
        return True


def _parse_domains(value: str | Iterable[str] | None) -> Set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        return {value.lower()}
    return {v.lower() for v in value}


def load_rules(root: Path) -> RuleEngine:
    rules_file = root / ".dropsync" / "rules.toml"
    if not rules_file.exists():
        return RuleEngine([])
    try:
        data = tomllib.loads(rules_file.read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError(f"Failed to load rules: {exc}") from exc
    parsed_rules: List[Rule] = []
    for entry in data.get("rules", []):
        parsed_rules.append(
            Rule(
                domains=_parse_domains(entry.get("domain")),
                item_type=entry.get("type"),
                extension=entry.get("ext"),
                add_tags=set(entry.get("add_tags", [])),
                move_to=entry.get("move_to"),
                post=list(entry.get("post", [])),
            )
        )
    return RuleEngine(parsed_rules)


def _parse_front_matter(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    if not content.startswith("---\n"):
        return {}
    lines = content.splitlines()
    metadata: dict[str, Any] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip().strip('"')
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            metadata[key] = [item.strip().strip('"') for item in inner.split(",") if item.strip()]
        else:
            metadata[key] = value
    return metadata


def _associated_paths(stub: Path) -> ItemPaths:
    return ItemPaths(
        stub=stub,
        readable=stub.with_suffix(".readable.md"),
        singlefile=stub.with_suffix(".single.html"),
    )


def organize_once(
    config: "DropSyncConfig",
    rule_engine: RuleEngine,
    processor_manager: ProcessorManager,
    force: bool = False,
) -> list[str]:
    from .config import DropSyncConfig  # local import to avoid cycle

    if not isinstance(config, DropSyncConfig):
        raise TypeError("config must be a DropSyncConfig instance")

    root = config.root_path
    actions: list[str] = []

    for stub in root.rglob("*.md"):
        name = stub.name
        if name.endswith(".readable.md"):
            continue
        if name.endswith(".single.html"):
            continue
        metadata = _parse_front_matter(stub)
        kind = metadata.get("kind")
        if kind != "url":
            continue
        url = metadata.get("url")
        if not url:
            continue
        domain = metadata.get("domain") or domain_from_url(url)
        item_type = metadata.get("item_type") or metadata.get("type") or "article"

        paths = _associated_paths(stub)
        application = rule_engine.apply(
            ItemContext(
                path=stub,
                domain=domain,
                item_type=item_type,
                extension=stub.suffix.lstrip(".") if stub.suffix else None,
            )
        )

        target_dir = config.subdirectory_path(application.move_to or "links")
        if stub.parent != target_dir:
            target_dir.mkdir(parents=True, exist_ok=True)
            new_stub = target_dir / stub.name
            shutil.move(str(stub), new_stub)
            if paths.readable.exists():
                shutil.move(str(paths.readable), target_dir / paths.readable.name)
            if paths.singlefile.exists():
                shutil.move(str(paths.singlefile), target_dir / paths.singlefile.name)
            actions.append(f"moved {stub.name} -> {target_dir.relative_to(root)}")
            stub = new_stub
            paths = _associated_paths(stub)

        scheduled = processor_manager.queue_for_url(
            UrlItem(
                url=url,
                paths=paths,
                domain=domain,
                item_type=item_type,
            ),
            extra_processors=application.post,
            force=force,
        )
        if scheduled:
            actions.append(f"scheduled {stub.name}: {', '.join(scheduled)}")

    return actions


__all__ = [
    "Rule",
    "RuleEngine",
    "load_rules",
    "ItemContext",
    "RuleApplication",
    "organize_once",
]
