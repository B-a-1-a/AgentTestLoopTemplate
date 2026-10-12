from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelSpec:
    provider: str
    id: str
    name: str
    default_params: dict[str, Any] = field(default_factory=dict)
    pinned: bool = False
    fallback_pinned_id: str | None = None


@dataclass
class ConfiguredModelStatus:
    provider: str
    id: str
    name: str
    pinned: bool
    stale_or_unavailable: bool
    suggested_ids: list[str] = field(default_factory=list)


@dataclass
class ProviderStatus:
    provider: str
    configured: bool
    key_state: str
    message: str
    models_validated: bool = False
    stale_models: list[str] = field(default_factory=list)
    available_remote_models: list[str] = field(default_factory=list)


@dataclass
class ProviderResponse:
    text: str
    raw: Any = None


@dataclass
class RegistrySnapshot:
    provider_statuses: list[ProviderStatus]
    configured_models: list[ConfiguredModelStatus]


class LLMProvider(ABC):
    provider_name: str

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    @abstractmethod
    def list_models_remote(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def chat(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        params: dict[str, Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> ProviderResponse:
        raise NotImplementedError
