from __future__ import annotations

from typing import Any

from src.providers.base import LLMProvider, ProviderResponse


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key)
        self._client = None
        if api_key:
            try:
                from anthropic import Anthropic  # type: ignore

                self._client = Anthropic(api_key=api_key)
            except Exception:
                self._client = None

    def list_models_remote(self) -> list[str]:
        if not self._client:
            return []
        try:
            models = self._client.models.list()
            return sorted([m.id for m in models.data if getattr(m, "id", None)])
        except Exception:
            return []

    def chat(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        params: dict[str, Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> ProviderResponse:
        if not self._client:
            raise RuntimeError("Anthropic client not configured")

        system_chunks = [m["content"] for m in messages if m.get("role") == "system"]
        conversational = [m for m in messages if m.get("role") != "system"]

        response = self._client.messages.create(
            model=model,
            system="\n\n".join(system_chunks),
            messages=conversational,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 1024),
        )
        text_parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                text_parts.append(getattr(block, "text", ""))
        return ProviderResponse(text="\n".join(text_parts).strip(), raw=response)
