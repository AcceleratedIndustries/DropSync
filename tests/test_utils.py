from __future__ import annotations

from dropsync import utils


def test_sanitize_title_keeps_spaces():
    title = utils.sanitize_title("  Hello / there: world!  ", max_length=50)
    assert title == "Hello - there world"


def test_slug_from_url():
    slug = utils.slug_from_url("https://example.com/posts/2024/awesome-article.html")
    assert "awesome" in slug


def test_build_front_matter_roundtrip(tmp_path):
    metadata = {
        "title": "Example",
        "tags": ["a", "b"],
        "timestamp": "20240513-120000",
    }
    text = utils.build_front_matter(metadata)
    path = tmp_path / "front.md"
    utils.write_text_file(path, text)
    saved = path.read_text()
    assert "title: Example" in saved
    assert "tags: [a, b]" in saved
