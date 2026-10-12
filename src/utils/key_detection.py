from __future__ import annotations

import os
from dataclasses import dataclass


_PLACEHOLDER_VALUES = {
    "",
    "your-key-here",
    "your_api_key_here",
    "change_me",
    "replace_me",
    "sk-your-key-here",
    "sk-ant-your-key-here",
}


@dataclass(frozen=True)
class KeyValidation:
    provider: str
    configured: bool
    state: str
    message: str


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in _PLACEHOLDER_VALUES or "your-key" in normalized


def _matches_format(provider: str, value: str) -> bool:
    if provider == "openai":
        return value.startswith("sk-") and len(value) > 20
    if provider == "anthropic":
        return value.startswith("sk-ant-") and len(value) > 20
    if provider == "google":
        return len(value) >= 16 and " " not in value
    return len(value) > 8


def validate_api_key(provider: str, env_key: str) -> KeyValidation:
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return KeyValidation(provider, False, "missing", f"{env_key} is not set")
    if _is_placeholder(raw):
        return KeyValidation(provider, False, "placeholder", f"{env_key} is still a placeholder")
    if not _matches_format(provider, raw):
        return KeyValidation(provider, False, "invalid_format", f"{env_key} format looks invalid")
    return KeyValidation(provider, True, "valid", f"{env_key} looks configured")
