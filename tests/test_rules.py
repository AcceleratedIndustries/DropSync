from __future__ import annotations

from pathlib import Path

from dropsync.config import DropSyncConfig
from dropsync.rules import ItemContext, Rule, RuleApplication, RuleEngine, load_rules, organize_once


class DummyProcessorManager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str], bool]] = []

    def queue_for_url(self, item, extra_processors, force=False):  # type: ignore[signature-diff]
        self.calls.append((item.url, list(extra_processors), force))
        return list(extra_processors)


def test_rule_matching():
    rule = Rule(domains={"example.com"}, item_type="article", add_tags={"test"})
    engine = RuleEngine([rule])
    application = engine.apply(
        ItemContext(path=Path("dummy"), domain="example.com", item_type="article")
    )
    assert "test" in application.tags


def test_organize_moves_and_schedules(tmp_path):
    root = tmp_path / "Collect"
    links_dir = root / "links"
    media_dir = root / "media"
    rules_dir = root / ".dropsync"
    links_dir.mkdir(parents=True)
    media_dir.mkdir()
    rules_dir.mkdir()

    stub = links_dir / "20240513-000000--Example.md"
    stub.write_text(
        "---\n"
        "title: Example\n"
        "url: https://youtube.com/watch?v=abc\n"
        "domain: youtube.com\n"
        "kind: url\n"
        "type: video\n"
        "timestamp: 20240513-000000\n"
        "---\n"
    )

    rules_file = rules_dir / "rules.toml"
    rules_file.write_text(
        "[[rules]]\n" "domain = [\"youtube.com\"]\n" "type = \"video\"\n" "move_to = \"media\"\n"
    )

    config = DropSyncConfig.model_validate({"root": str(root)})
    processor_manager = DummyProcessorManager()
    rule_engine = load_rules(root)

    actions = organize_once(config, rule_engine, processor_manager)
    assert any("moved" in action for action in actions)
    moved_stub = media_dir / stub.name
    assert moved_stub.exists()
    assert processor_manager.calls
