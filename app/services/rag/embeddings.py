from __future__ import annotations


def estimate_token_count(text: str) -> int:
    # MVP: use a stable approximation until a real tokenizer/embedding backend is plugged in.
    return max(1, len(text.split()))
