from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    start_offset: int
    end_offset: int


def split_text(text: str, *, max_chars: int = 1200, overlap: int = 150) -> list[TextChunk]:
    """Split text at natural boundaries while guaranteeing forward progress."""
    if max_chars <= 0 or overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be non-negative and smaller than max_chars")
    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        target = min(start + max_chars, len(normalized))
        end = target
        if target < len(normalized):
            boundary = max(
                normalized.rfind("\n\n", start, target),
                normalized.rfind("\n", start, target),
                normalized.rfind(" ", start, target),
            )
            if boundary > start:
                end = boundary
        content = normalized[start:end].strip()
        actual_start = start + (len(normalized[start:end]) - len(normalized[start:end].lstrip()))
        actual_end = actual_start + len(content)
        if content:
            chunks.append(TextChunk(len(chunks), content, actual_start, actual_end))
        if end >= len(normalized):
            break
        next_start = max(end - overlap, start + 1)
        while next_start < len(normalized) and normalized[next_start].isspace():
            next_start += 1
        start = next_start
    return chunks
