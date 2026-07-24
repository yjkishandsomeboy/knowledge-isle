import pytest

from knowledge_isle_api.services.chunking import split_text


def test_split_text_is_bounded_and_reproducible() -> None:
    text = "第一段内容。\n\n" + ("长文本 " * 500) + "\n\n最后一段。"
    first = split_text(text, max_chars=120, overlap=20)
    second = split_text(text, max_chars=120, overlap=20)

    assert first == second
    assert first
    assert all(0 < len(chunk.content) <= 120 for chunk in first)
    assert all(chunk.end_offset > chunk.start_offset for chunk in first)
    assert [chunk.index for chunk in first] == list(range(len(first)))


def test_split_text_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        split_text("content", max_chars=10, overlap=10)
