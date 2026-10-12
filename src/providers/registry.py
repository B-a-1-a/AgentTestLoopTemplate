from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.providers.anthropic_provider import AnthropicProvider
from src.providers.base import ConfiguredModelStatus, ModelSpec, ProviderStatus, RegistrySnapshot
from src.providers.google_provider import GoogleProvider
from src.providers.openai_provider import OpenAIProvider
from src.utils.config import load_yaml
from src.utils.key_detection import validate_api_key


@dataclass
class ModelResolution:
    selected_model_id: str
    used_fallback: bool
    reason: str


class ProviderRegistry:
    def __init__(self, models_path: str | Path = "config/models.yaml") -> None:
        self.models_path = Path(models_path)
        self.model_config = load_yaml(self.models_path)

    def _providers_config(self) -> dict[str, Any]:
        return self.model_config.get("providers", {})

    def _model_specs_for(self, provider_name: str) -> list[ModelSpec]:
        provider_block = self._providers_config().get(provider_name, {})
        specs: list[ModelSpec] = []
        for row in provider_block.get("models", []):
            specs.append(
                ModelSpec(
                    provider=provider_name,
                    id=row["id"],
                    name=row.get("name", row["id"]),
                    default_params=row.get("default_params", {}),
                    pinned=bool(row.get("pinned", False)),
                    fallback_pinned_id=row.get("fallback_pinned_id"),
                )
            )
        return specs

    def _provider_instance(self, provider_name: str):
        conf = self._providers_config().get(provider_name, {})
        env_key = conf.get("env_key", "")
        api_key = os.getenv(env_key, "").strip() if env_key else ""
        if provider_name == "openai":
            return OpenAIProvider(api_key=api_key)
        if provider_name == "anthropic":
            return AnthropicProvider(api_key=api_key)
        if provider_name == "google":
            return GoogleProvider(api_key=api_key)
        return None

    def provider_statuses(self) -> list[ProviderStatus]:
        statuses: list[ProviderStatus] = []
        for provider_name, conf in self._providers_config().items():
            key_check = validate_api_key(provider_name, conf.get("env_key", ""))
            statuses.append(
                ProviderStatus(
                    provider=provider_name,
                    configured=key_check.configured,
                    key_state=key_check.state,
                    message=key_check.message,
                )
            )
        return statuses

    def validate_models_from_api(self) -> RegistrySnapshot:
        statuses = self.provider_statuses()
        validated_models: list[ConfiguredModelStatus] = []

        for status in statuses:
            specs = self._model_specs_for(status.provider)
            remote_ids: list[str] = []
            if status.configured:
                provider = self._provider_instance(status.provider)
                if provider:
                    remote_ids = provider.list_models_remote()

            status.models_validated = bool(remote_ids)
            status.available_remote_models = remote_ids

            for spec in specs:
                stale = bool(remote_ids) and spec.id not in remote_ids
                suggestions = self._suggest_models(spec.id, remote_ids)
                if stale:
                    status.stale_models.append(spec.id)
                validated_models.append(
                    ConfiguredModelStatus(
                        provider=spec.provider,
                        id=spec.id,
                        name=spec.name,
                        pinned=spec.pinned,
                        stale_or_unavailable=stale,
                        suggested_ids=suggestions,
                    )
                )

            if status.stale_models:
                status.message = f"{len(status.stale_models)} model(s) stale_or_unavailable"

        return RegistrySnapshot(provider_statuses=statuses, configured_models=validated_models)

    def get_provider(self, provider_name: str):
        provider = self._provider_instance(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider

    def configured_models(self) -> list[ModelSpec]:
        all_specs: list[ModelSpec] = []
        for provider_name in self._providers_config().keys():
            all_specs.extend(self._model_specs_for(provider_name))
        return all_specs

    def resolve_model_id(
        self,
        provider_name: str,
        requested_id: str,
        remote_ids: list[str],
    ) -> ModelResolution:
        if not remote_ids:
            return ModelResolution(requested_id, False, "remote list unavailable")
        if requested_id in remote_ids:
            return ModelResolution(requested_id, False, "configured model available")

        specs = self._model_specs_for(provider_name)
        requested_spec = next((s for s in specs if s.id == requested_id), None)
        if requested_spec and not requested_spec.pinned and requested_spec.fallback_pinned_id:
            if requested_spec.fallback_pinned_id in remote_ids:
                return ModelResolution(
                    requested_spec.fallback_pinned_id,
                    True,
                    "alias unavailable, using fallback pinned model",
                )

        suggestions = self._suggest_models(requested_id, remote_ids)
        if suggestions:
            return ModelResolution(suggestions[0], True, "configured model unavailable, using suggested model")
        return ModelResolution(requested_id, False, "configured model unavailable and no fallback")

    @staticmethod
    def _suggest_models(requested_id: str, remote_ids: list[str]) -> list[str]:
        if not remote_ids:
            return []
        family = requested_id.split("-", 1)[0]
        family_matches = [m for m in remote_ids if m.startswith(family)]
        if family_matches:
            return family_matches[:5]
        return remote_ids[:5]
