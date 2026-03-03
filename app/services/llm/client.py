from __future__ import annotations

from app.core.config import settings
from app.services.llm.providers import BaseLLMProvider, DeterministicLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    # MVP keeps the provider pluggable while defaulting to a deterministic implementation.
    _provider_name = settings.llm_provider.lower()
    return DeterministicLLMProvider()
