from __future__ import annotations

from typing import Any

from src.providers.base import LLMProvider, ProviderResponse


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key)
        self._client = None
        if api_key:
            try:
                from openai import OpenAI  # type: ignore

                self._client = OpenAI(api_key=api_key)
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
            raise RuntimeError("OpenAI client not configured")

        req: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1024),
        }
        if tools:
            req["tools"] = tools

        completion = self._client.chat.completions.create(**req)
        text = completion.choices[0].message.content or ""
        return ProviderResponse(text=text, raw=completion)
