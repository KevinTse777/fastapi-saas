from __future__ import annotations

import logging
import uuid


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def new_trace_id() -> str:
    return uuid.uuid4().hex
