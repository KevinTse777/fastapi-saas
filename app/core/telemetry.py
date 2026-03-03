from __future__ import annotations

from collections import Counter


class InMemoryMetrics:
    def __init__(self) -> None:
        self._counter: Counter[str] = Counter()

    def incr(self, key: str) -> None:
        self._counter[key] += 1

    def snapshot(self) -> dict[str, int]:
        return dict(self._counter)


metrics = InMemoryMetrics()
