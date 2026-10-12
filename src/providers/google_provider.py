from __future__ import annotations

from typing import Any

from src.providers.base import LLMProvider, ProviderResponse


class GoogleProvider(LLMProvider):
    provider_name = "google"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key)
        self._client = None
        if api_key:
            try:
                from google import genai  # type: ignore

                self._client = genai.Client(api_key=api_key)
            except Exception:
                self._client = None

    def list_models_remote(self) -> list[str]:
        if not self._client:
            return []
        try:
            models = self._client.models.list()
            model_ids = []
            for model in models:
                model_name = getattr(model, "name", "")
                if model_name.startswith("models/"):
                    model_name = model_name.split("models/", 1)[1]
                if model_name:
                    model_ids.append(model_name)
            return sorted(model_ids)
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
            raise RuntimeError("Google client not configured")

        text_input = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        response = self._client.models.generate_content(model=model, contents=text_input)
        text = getattr(response, "text", "") or ""
        return ProviderResponse(text=text, raw=response)
