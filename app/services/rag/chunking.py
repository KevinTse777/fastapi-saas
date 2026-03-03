from __future__ import annotations

from app.core.config import settings


def split_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    size = chunk_size or settings.ai_chunk_size
    step_overlap = overlap or settings.ai_chunk_overlap
    words = text.split()
    if not words:
        return []

    target_words = max(80, size // 6)
    overlap_words = max(10, step_overlap // 6)
    if overlap_words >= target_words:
        overlap_words = max(10, target_words // 4)

    chunks: list[str] = []
    start_index = 0
    while start_index < len(words):
        end_index = min(len(words), start_index + target_words)
        chunk = " ".join(words[start_index:end_index]).strip()
        if chunk:
            chunks.append(chunk)
        if end_index == len(words):
            break
        start_index = max(end_index - overlap_words, start_index + 1)
    return chunks
