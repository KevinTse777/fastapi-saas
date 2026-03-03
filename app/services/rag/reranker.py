from __future__ import annotations


def rerank_chunks(chunks: list[dict]) -> list[dict]:
    return sorted(chunks, key=lambda item: (item["score"], -item["chunk_id"]), reverse=True)
